#!/usr/bin/env python3
"""
Balance Tracker Example

This example demonstrates how to use evrmore-rpc with SQLite to track asset balances
and orders in real-time. It shows how to:

1. Set up a SQLite database to store balances and transactions
2. Track multiple addresses and their asset balances
3. Monitor transactions in real-time using ZMQ
4. Update balances when transactions are confirmed
5. Track order/transaction status (pending, confirmed, etc.)

This serves as a simple foundation for building a exchange backend.
"""

import os
import asyncio
import sqlite3
import logging
import signal
import json
import uuid
import argparse
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('balance_tracker')

# Rich console for pretty output
console = Console()

# Define database schema
SCHEMA = """
-- Addresses table: Tracks addresses we're monitoring
CREATE TABLE IF NOT EXISTS addresses (
    address TEXT PRIMARY KEY,
    label TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table: Stores asset information
CREATE TABLE IF NOT EXISTS assets (
    asset_name TEXT PRIMARY KEY,
    issuer TEXT,
    total_supply REAL,
    units INTEGER,
    reissuable BOOLEAN,
    has_ipfs BOOLEAN,
    ipfs_hash TEXT,
    divisibility INTEGER,
    last_updated TIMESTAMP
);

-- Balances table: Tracks address balances for each asset
CREATE TABLE IF NOT EXISTS balances (
    address TEXT,
    asset_name TEXT,
    balance REAL NOT NULL DEFAULT 0,
    last_updated TIMESTAMP,
    PRIMARY KEY (address, asset_name),
    FOREIGN KEY (address) REFERENCES addresses (address),
    FOREIGN KEY (asset_name) REFERENCES assets (asset_name)
);

-- Transactions table: Tracks transaction history
CREATE TABLE IF NOT EXISTS transactions (
    txid TEXT PRIMARY KEY,
    block_hash TEXT,
    block_height INTEGER,
    timestamp TIMESTAMP,
    confirmations INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('pending', 'confirming', 'confirmed', 'failed'))
);

-- Transaction Outputs table: Details of transaction outputs
CREATE TABLE IF NOT EXISTS tx_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT,
    address TEXT,
    asset_name TEXT,
    amount REAL,
    vout INTEGER,
    FOREIGN KEY (txid) REFERENCES transactions (txid),
    FOREIGN KEY (address) REFERENCES addresses (address),
    FOREIGN KEY (asset_name) REFERENCES assets (asset_name)
);

-- Orders table: Tracks exchange orders
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    seller_address TEXT,
    buyer_address TEXT,
    asset_name TEXT,
    amount REAL,
    price REAL,
    total_cost REAL,
    status TEXT CHECK (status IN ('pending', 'processing', 'completed', 'cancelled', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_txid TEXT,
    delivery_txid TEXT,
    FOREIGN KEY (seller_address) REFERENCES addresses (address),
    FOREIGN KEY (buyer_address) REFERENCES addresses (address),
    FOREIGN KEY (asset_name) REFERENCES assets (asset_name),
    FOREIGN KEY (payment_txid) REFERENCES transactions (txid),
    FOREIGN KEY (delivery_txid) REFERENCES transactions (txid)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tx_outputs_txid ON tx_outputs (txid);
CREATE INDEX IF NOT EXISTS idx_tx_outputs_address ON tx_outputs (address);
CREATE INDEX IF NOT EXISTS idx_tx_outputs_asset ON tx_outputs (asset_name);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_balances_address ON balances (address);
"""


class DatabaseManager:
    """Manages the SQLite database operations."""
    
    def __init__(self, db_path: str = "balance_tracker.db"):
        """Initialize the database manager."""
        self.db_path = db_path
        self.conn = None
        self.setup_database()
        
    def setup_database(self) -> None:
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Create schema
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
        
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
        
    def add_address(self, address: str, label: Optional[str] = None) -> None:
        """Add an address to track."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO addresses (address, label) VALUES (?, ?)",
            (address, label)
        )
        self.conn.commit()
        logger.info(f"Added address: {address} ({label})")
        
    def add_asset(self, asset_data: Dict[str, Any]) -> None:
        """Add or update asset information."""
        cursor = self.conn.cursor()
        
        # Handle both dict formats (from API or from our test data)
        name = asset_data.get('name', asset_data.get('asset_name', ''))
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO assets 
            (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                name,
                asset_data.get('issuer', ''),
                asset_data.get('amount', asset_data.get('total_supply', 0)),
                asset_data.get('units', 0),
                asset_data.get('reissuable', True),
                asset_data.get('has_ipfs', False),
                asset_data.get('ipfs_hash', asset_data.get('ipfs', '')),
                asset_data.get('divisibility', 8),
            )
        )
        self.conn.commit()
        logger.debug(f"Added/updated asset: {name}")
        
    def update_balance(self, address: str, asset_name: str, balance: Union[Decimal, float]) -> None:
        """Update balance for an address and asset."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO balances (address, asset_name, balance, last_updated)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (address, asset_name, float(balance))
        )
        self.conn.commit()
        logger.debug(f"Updated balance for {address}: {asset_name} = {balance}")
        
    def add_transaction(self, txid: str, status: str = 'pending') -> None:
        """Add a new transaction to track."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO transactions (txid, status, timestamp)
            VALUES (?, ?, datetime('now'))
            """,
            (txid, status)
        )
        self.conn.commit()
        logger.debug(f"Added transaction: {txid} (status: {status})")
        
    def update_transaction(self, txid: str, block_hash: Optional[str] = None, 
                           block_height: Optional[int] = None, 
                           confirmations: Optional[int] = None,
                           status: Optional[str] = None) -> None:
        """Update transaction information."""
        cursor = self.conn.cursor()
        
        update_parts = []
        params = []
        
        if block_hash is not None:
            update_parts.append("block_hash = ?")
            params.append(block_hash)
            
        if block_height is not None:
            update_parts.append("block_height = ?")
            params.append(block_height)
            
        if confirmations is not None:
            update_parts.append("confirmations = ?")
            params.append(confirmations)
            
        if status is not None:
            update_parts.append("status = ?")
            params.append(status)
            
        if not update_parts:
            return  # Nothing to update
            
        update_parts.append("timestamp = datetime('now')")
        query = f"UPDATE transactions SET {', '.join(update_parts)} WHERE txid = ?"
        params.append(txid)
        
        cursor.execute(query, params)
        self.conn.commit()
        logger.debug(f"Updated transaction: {txid} (confirmations: {confirmations}, status: {status})")
        
    def add_tx_output(self, txid: str, address: str, asset_name: str, 
                     amount: Union[Decimal, float], vout: int) -> None:
        """Add a transaction output."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO tx_outputs (txid, address, asset_name, amount, vout)
            VALUES (?, ?, ?, ?, ?)
            """,
            (txid, address, asset_name, float(amount), vout)
        )
        self.conn.commit()
        logger.debug(f"Added tx output: {txid} -> {address}, {asset_name} = {amount}")
        
    def create_order(self, order_id: str, seller_address: str, buyer_address: Optional[str],
                    asset_name: str, amount: Union[Decimal, float], 
                    price: Union[Decimal, float]) -> None:
        """Create a new order."""
        total_cost = float(amount) * float(price)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders 
            (order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (order_id, seller_address, buyer_address, asset_name, float(amount), float(price), total_cost)
        )
        self.conn.commit()
        logger.info(f"Created order: {order_id} for {amount} {asset_name}")
        
    def update_order_status(self, order_id: str, status: str, 
                           payment_txid: Optional[str] = None,
                           delivery_txid: Optional[str] = None) -> None:
        """Update order status and transaction IDs."""
        cursor = self.conn.cursor()
        
        update_parts = ["status = ?", "updated_at = datetime('now')"]
        params = [status]
        
        if payment_txid is not None:
            update_parts.append("payment_txid = ?")
            params.append(payment_txid)
            
        if delivery_txid is not None:
            update_parts.append("delivery_txid = ?")
            params.append(delivery_txid)
            
        query = f"UPDATE orders SET {', '.join(update_parts)} WHERE order_id = ?"
        params.append(order_id)
        
        cursor.execute(query, params)
        self.conn.commit()
        logger.info(f"Updated order: {order_id} (status: {status})")
        
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status
            FROM orders
            WHERE status IN ('pending', 'processing')
            """
        )
        
        columns = [col[0] for col in cursor.description]
        orders = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return orders
        
    def get_pending_transactions(self) -> List[Dict[str, Any]]:
        """Get all pending transactions."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT txid, block_hash, block_height, confirmations, status
            FROM transactions
            WHERE status IN ('pending', 'confirming')
            """
        )
        
        columns = [col[0] for col in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return transactions
        
    def get_address_balances(self, address: str) -> List[Dict[str, Any]]:
        """Get all balances for an address."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT b.asset_name, b.balance, b.last_updated,
                   a.units, a.reissuable, a.has_ipfs, a.ipfs_hash
            FROM balances b
            LEFT JOIN assets a ON b.asset_name = a.asset_name
            WHERE b.address = ?
            """,
            (address,)
        )
        
        columns = [col[0] for col in cursor.description]
        balances = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return balances
        
    def get_all_monitored_addresses(self) -> List[str]:
        """Get all addresses that we're monitoring."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT address FROM addresses")
        return [row[0] for row in cursor.fetchall()]
        
    def get_transactions_for_address(self, address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for an address."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT t.txid, t.block_hash, t.block_height, t.confirmations, t.status, 
                   t.timestamp, o.asset_name, o.amount
            FROM transactions t
            JOIN tx_outputs o ON t.txid = o.txid
            WHERE o.address = ?
            ORDER BY t.timestamp DESC
            LIMIT ?
            """,
            (address, limit)
        )
        
        columns = [col[0] for col in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return transactions
    
    def get_balances_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all balances by address."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT a.address, a.label, COUNT(DISTINCT b.asset_name) as asset_count, 
                   SUM(CASE WHEN b.asset_name = 'EVR' THEN b.balance ELSE 0 END) as evr_balance
            FROM addresses a
            LEFT JOIN balances b ON a.address = b.address
            GROUP BY a.address, a.label
            """
        )
        
        columns = [col[0] for col in cursor.description]
        summary = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return summary
    
    def get_order_summary(self) -> Dict[str, int]:
        """Get a summary of order statuses."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT status, COUNT(*) as count
            FROM orders
            GROUP BY status
            """
        )
        
        return {row[0]: row[1] for row in cursor.fetchall()}


class TransactionPattern:
    """
    Advanced transaction pattern matching system that can identify specific transaction patterns
    such as asset swaps, NFT transfers, etc.
    """
    
    def __init__(self, pattern_name: str, match_criteria: Dict[str, Any]):
        self.pattern_name = pattern_name
        self.criteria = match_criteria
        self.description = match_criteria.get('description', 'No description')
        
    def matches(self, tx_details: Dict[str, Any]) -> bool:
        """
        Check if a transaction matches this pattern.
        
        Supports complex matching with multiple conditions:
        - Asset type matching
        - Amount range matching
        - Address pattern matching
        - Multiple input/output matching
        """
        # Basic matching logic - can be extended with much more sophistication
        if 'asset_name' in self.criteria:
            # Extract asset name from transaction
            asset_names = []
            for vout in tx_details.get('vout', []):
                asset_info = vout.get('scriptPubKey', {}).get('asset', {})
                if asset_info and 'name' in asset_info:
                    asset_names.append(asset_info['name'])
            
            # Check if any output matches the asset name pattern
            if self.criteria['asset_name'] not in asset_names:
                return False
        
        if 'min_amount' in self.criteria:
            # Check if any output has an amount greater than min_amount
            has_min_amount = False
            for vout in tx_details.get('vout', []):
                amount = vout.get('value', 0)
                asset_info = vout.get('scriptPubKey', {}).get('asset', {})
                if asset_info:
                    amount = asset_info.get('amount', 0)
                
                if amount >= self.criteria['min_amount']:
                    has_min_amount = True
                    break
            
            if not has_min_amount:
                return False
        
        # You can add more sophisticated matching logic here
        
        return True


class AnomalyDetector:
    """
    Advanced anomaly detection for Evrmore transactions.
    
    Can identify unusual transaction patterns that might indicate important
    market activities or security concerns.
    """
    
    def __init__(self, db: DatabaseManager, sensitivity: float = 0.8):
        self.db = db
        self.sensitivity = sensitivity
        self.baseline_stats = {}
        self.historical_txs = []
        self.is_initialized = False
    
    async def initialize(self, client: EvrmoreAsyncRPCClient):
        """Initialize the anomaly detector with historical data."""
        # Get some historical transactions for baseline
        try:
            height = await client.getblockcount()
            
            # Analyze last 10 blocks for baseline
            for block_height in range(height - 10, height):
                block_hash = await client.getblockhash(block_height)
                block = await client.getblock(block_hash)
                
                for txid in block.tx[:20]:  # Sample first 20 txs per block
                    try:
                        tx = await client.getrawtransaction(txid, True)
                        self.historical_txs.append(tx)
                    except Exception:
                        continue
            
            # Calculate baseline statistics
            self._calculate_baseline()
            self.is_initialized = True
            logger.info(f"Anomaly detector initialized with {len(self.historical_txs)} transactions")
            
        except Exception as e:
            logger.error(f"Failed to initialize anomaly detector: {e}")
    
    def _calculate_baseline(self):
        """Calculate baseline statistics from historical transactions."""
        if not self.historical_txs:
            return
            
        # Calculate average values and standard deviations
        amounts = []
        vin_counts = []
        vout_counts = []
        
        for tx in self.historical_txs:
            # Extract transaction value
            tx_value = 0
            for vout in tx.get('vout', []):
                tx_value += vout.get('value', 0)
            
            amounts.append(tx_value)
            vin_counts.append(len(tx.get('vin', [])))
            vout_counts.append(len(tx.get('vout', [])))
        
        # Calculate statistics
        self.baseline_stats = {
            'avg_amount': sum(amounts) / len(amounts) if amounts else 0,
            'std_amount': self._std_dev(amounts) if amounts else 0,
            'avg_vin': sum(vin_counts) / len(vin_counts) if vin_counts else 0,
            'std_vin': self._std_dev(vin_counts) if vin_counts else 0,
            'avg_vout': sum(vout_counts) / len(vout_counts) if vout_counts else 0,
            'std_vout': self._std_dev(vout_counts) if vout_counts else 0,
        }
    
    def _std_dev(self, values):
        """Calculate standard deviation."""
        if not values or len(values) < 2:
            return 0
            
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def check_transaction(self, tx_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a transaction is anomalous.
        
        Returns a dict with:
        - is_anomaly: bool
        - anomaly_score: float (0-1)
        - reasons: list of reasons why it's anomalous
        """
        if not self.is_initialized or not self.baseline_stats:
            return {'is_anomaly': False, 'anomaly_score': 0, 'reasons': []}
            
        reasons = []
        scores = []
        
        # Calculate transaction total value
        tx_value = 0
        for vout in tx_details.get('vout', []):
            tx_value += vout.get('value', 0)
        
        # Check amount anomaly
        if self.baseline_stats['std_amount'] > 0:
            amount_z_score = abs(tx_value - self.baseline_stats['avg_amount']) / self.baseline_stats['std_amount']
            if amount_z_score > 3:  # More than 3 standard deviations
                reasons.append(f"Transaction amount ({tx_value}) is unusually {'high' if tx_value > self.baseline_stats['avg_amount'] else 'low'}")
                scores.append(min(1.0, amount_z_score / 10))
        
        # Check input/output count anomalies
        vin_count = len(tx_details.get('vin', []))
        vout_count = len(tx_details.get('vout', []))
        
        if self.baseline_stats['std_vin'] > 0:
            vin_z_score = abs(vin_count - self.baseline_stats['avg_vin']) / self.baseline_stats['std_vin']
            if vin_z_score > 3:
                reasons.append(f"Unusual number of inputs: {vin_count}")
                scores.append(min(1.0, vin_z_score / 10))
        
        if self.baseline_stats['std_vout'] > 0:
            vout_z_score = abs(vout_count - self.baseline_stats['avg_vout']) / self.baseline_stats['std_vout']
            if vout_z_score > 3:
                reasons.append(f"Unusual number of outputs: {vout_count}")
                scores.append(min(1.0, vout_z_score / 10))
        
        # Calculate overall anomaly score
        anomaly_score = max(scores) if scores else 0
        is_anomaly = anomaly_score > self.sensitivity
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'reasons': reasons
        }


class RealTimeMonitor:
    """
    Real-time monitoring system with WebSocket support.
    
    This allows for building live dashboards and notifications.
    """
    def __init__(self, tracker):
        self.tracker = tracker
        self.websocket_clients = set()
        self.ticker_running = False
        self.ticker_task = None
    
    async def start_ticker(self):
        """Start the data ticker that sends updates to all websocket clients."""
        if self.ticker_running:
            return
            
        self.ticker_running = True
        self.ticker_task = asyncio.create_task(self._ticker_loop())
    
    async def stop_ticker(self):
        """Stop the data ticker."""
        self.ticker_running = False
        if self.ticker_task:
            self.ticker_task.cancel()
            try:
                await self.ticker_task
            except asyncio.CancelledError:
                pass
    
    async def _ticker_loop(self):
        """Send periodic updates to all connected websocket clients."""
        while self.ticker_running:
            if self.websocket_clients:
                # Get latest data
                data = self._prepare_update_data()
                
                # Send to all connected clients
                for client in list(self.websocket_clients):
                    try:
                        await client.send_json(data)
                    except Exception:
                        # Remove disconnected clients
                        self.websocket_clients.discard(client)
            
            await asyncio.sleep(1)  # Update once per second
    
    def _prepare_update_data(self):
        """Prepare data for websocket updates."""
        # Get address balances
        balances_summary = self.tracker.db.get_balances_summary()
        formatted_balances = []
        for item in balances_summary:
            formatted_balances.append({
                'address': item['address'],
                'label': item['label'],
                'asset_count': item['asset_count'],
                'evr_balance': float(item['evr_balance']) if item['evr_balance'] else 0
            })
        
        # Get orders
        pending_orders = self.tracker.db.get_pending_orders()
        
        # Get transactions
        pending_txs = self.tracker.db.get_pending_transactions()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'balances': formatted_balances,
            'orders': pending_orders,
            'transactions': pending_txs
        }
    
    async def handle_websocket_connection(self, websocket):
        """Handle a new websocket connection."""
        # Add to client set
        self.websocket_clients.add(websocket)
        
        # Send initial data
        try:
            await websocket.send_json(self._prepare_update_data())
        except Exception:
            self.websocket_clients.discard(websocket)
            return
        
        # Start ticker if not already running
        if not self.ticker_running:
            await self.start_ticker()
        
        # Keep connection alive until client disconnects
        try:
            while True:
                # Wait for messages (or client disconnect)
                msg = await websocket.receive_text()
                
                # Process commands from client if needed
                if msg == 'ping':
                    await websocket.send_text('pong')
                
        except Exception:
            # Client disconnected
            self.websocket_clients.discard(websocket)


class BalanceTracker:
    """
    Main class for tracking address balances and orders.
    Uses ZMQ for real-time notifications and RPC for fetching data.
    """
    
    def __init__(self, db_path: str = "balance_tracker.db", confirmations_required: int = 6):
        """Initialize the balance tracker."""
        self.db = DatabaseManager(db_path)
        self.rpc_client = None
        self.zmq_client = None
        self.confirmations_required = confirmations_required
        self.running = False
        
        # In-memory tracking
        self.pending_txs: Set[str] = set()
        self.monitored_addresses: Set[str] = set()
        
        # Advanced features
        self.patterns = []  # Transaction pattern matchers
        self.anomaly_detector = AnomalyDetector(self.db)
        self.real_time_monitor = RealTimeMonitor(self)
        
        # UI
        self.console = Console()
        self.layout = self._create_layout()
        
        # Register default transaction patterns
        self._register_default_patterns()
        
    def _register_default_patterns(self):
        """Register default transaction patterns to watch for."""
        self.patterns = [
            TransactionPattern("NFT Transfer", {
                "description": "Transfer of NFT assets between addresses",
                "asset_name": "ASSET"  # Generic pattern, will be enhanced with real asset data
            }),
            TransactionPattern("Large Transfer", {
                "description": "Large value transfer (>100 EVR)",
                "min_amount": 100
            }),
            # More patterns can be added here
        ]
        
    def register_pattern(self, pattern: TransactionPattern):
        """Register a new transaction pattern to watch for."""
        self.patterns.append(pattern)
        logger.info(f"Registered new transaction pattern: {pattern.pattern_name}")
    
    def _create_layout(self) -> Layout:
        """Create the main layout for the UI."""
        layout = Layout(name="root")
        
        # Split into header, body, and footer
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into left and right panels
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        # Right panel has orders on top, transactions on bottom
        layout["right"].split(
            Layout(name="orders"),
            Layout(name="transactions")
        )
        
        return layout
    
    def _render_header(self) -> Panel:
        """Render the header panel."""
        return Panel(
            Text("Evrmore Balance & Order Tracker", justify="center"),
            style="bold white on blue"
        )
    
    def _render_footer(self) -> Panel:
        """Render the footer with stats."""
        order_summary = self.db.get_order_summary()
        pending_orders = order_summary.get('pending', 0)
        processing_orders = order_summary.get('processing', 0)
        completed_orders = order_summary.get('completed', 0)
        
        text = Text()
        text.append(f"Monitoring {len(self.monitored_addresses)} addresses | ")
        text.append(f"Pending Orders: {pending_orders} | ")
        text.append(f"Processing: {processing_orders} | ")
        text.append(f"Completed: {completed_orders} | ")
        text.append(f"Confirmations Required: {self.confirmations_required}")
        
        return Panel(text, style="white on blue")
    
    def _render_addresses(self) -> Panel:
        """Render the addresses panel with balances."""
        table = Table(title="Monitored Addresses & Balances")
        table.add_column("Address", style="cyan")
        table.add_column("Label", style="green")
        table.add_column("Assets", justify="right")
        table.add_column("EVR Balance", justify="right")
        
        for item in self.db.get_balances_summary():
            table.add_row(
                item['address'][:10] + "...",
                item['label'] or "",
                str(item['asset_count']),
                f"{item['evr_balance']:.4f}" if item['evr_balance'] else "0.0000"
            )
            
        return Panel(table, title="Balances")
    
    def _render_orders(self) -> Panel:
        """Render the orders panel."""
        table = Table()
        table.add_column("Order ID", style="cyan")
        table.add_column("Asset", style="green")
        table.add_column("Amount", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Status", style="yellow")
        
        for order in self.db.get_pending_orders()[:10]:  # Show only top 10
            table.add_row(
                order['order_id'][:8] + "...",
                order['asset_name'],
                f"{order['amount']:.4f}",
                f"{order['price']:.4f}",
                order['status']
            )
            
        return Panel(table, title="Recent Orders")
    
    def _render_transactions(self) -> Panel:
        """Render the transactions panel."""
        table = Table()
        table.add_column("TXID", style="cyan")
        table.add_column("Confirmations", justify="right")
        table.add_column("Status", style="yellow")
        
        for tx in self.db.get_pending_transactions()[:10]:  # Show only top 10
            table.add_row(
                tx['txid'][:8] + "...",
                str(tx['confirmations'] or 0),
                tx['status']
            )
            
        return Panel(table, title="Recent Transactions")
    
    def _update_display(self) -> None:
        """Update the display with current state."""
        self.layout["header"].update(self._render_header())
        self.layout["footer"].update(self._render_footer())
        self.layout["left"].update(self._render_addresses())
        self.layout["right"]["orders"].update(self._render_orders())
        self.layout["right"]["transactions"].update(self._render_transactions())
    
    async def initialize(self) -> None:
        """Initialize clients and load initial data."""
        # Create RPC client
        self.rpc_client = EvrmoreAsyncRPCClient()
        await self.rpc_client.initialize()
        
        # Create ZMQ client
        self.zmq_client = EvrmoreZMQClient()
        
        # Load monitored addresses
        self.monitored_addresses = set(self.db.get_all_monitored_addresses())
        logger.info(f"Loaded {len(self.monitored_addresses)} monitored addresses")
        
        # Load pending transactions
        pending_txs = self.db.get_pending_transactions()
        self.pending_txs = {tx['txid'] for tx in pending_txs}
        logger.info(f"Loaded {len(self.pending_txs)} pending transactions")

        # Register ZMQ handlers
        self.zmq_client.on_transaction(self.handle_transaction)
        self.zmq_client.on_block(self.handle_block)
        
        # Initialize anomaly detector
        await self.anomaly_detector.initialize(self.rpc_client)
        
    async def start(self) -> None:
        """Start the balance tracker."""
        await self.initialize()
        self.running = True
        
        # Start ZMQ client
        zmq_task = asyncio.create_task(self.zmq_client.start())
        
        # Start update loop
        update_task = asyncio.create_task(self.update_loop())
        
        # Update display in a Live session
        with Live(self.layout, refresh_per_second=4, screen=True) as live:
            while self.running:
                self._update_display()
                await asyncio.sleep(0.25)  # 4 times per second
                
        # Stop tasks
        update_task.cancel()
        await self.zmq_client.stop()
        if not zmq_task.done():
            zmq_task.cancel()
        
        # Close database
        self.db.close()
        
    async def stop(self) -> None:
        """Stop the balance tracker."""
        logger.info("Stopping balance tracker...")
        self.running = False
        
    async def update_loop(self) -> None:
        """Periodic update loop to check pending transactions and orders."""
        while self.running:
            try:
                # Update pending transactions
                await self.update_pending_transactions()
                
                # Update address balances (every 10 seconds)
                await self.update_all_balances()
                
                # Update pending orders
                await self.update_pending_orders()
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                
            await asyncio.sleep(10)  # Run every 10 seconds
            
    async def update_pending_transactions(self) -> None:
        """Update status of pending transactions."""
        for txid in list(self.pending_txs):
            try:
                # Get transaction details
                tx_details = await self.rpc_client.getrawtransaction(txid, True)
                
                # Check for transaction patterns
                matched_patterns = []
                for pattern in self.patterns:
                    if pattern.matches(tx_details):
                        matched_patterns.append(pattern.pattern_name)
                        logger.info(f"Transaction {txid} matches pattern: {pattern.pattern_name}")
                
                # Check for anomalies
                anomaly_result = self.anomaly_detector.check_transaction(tx_details)
                if anomaly_result['is_anomaly']:
                    logger.warning(f"ANOMALY DETECTED in transaction {txid} (score: {anomaly_result['anomaly_score']:.2f})")
                    for reason in anomaly_result['reasons']:
                        logger.warning(f"  - {reason}")
                
                # Check if transaction involves any of our monitored addresses
                addresses_involved = set()
                for vout in tx_details.get('vout', []):
                    for address in vout.get('scriptPubKey', {}).get('addresses', []):
                        if address in self.monitored_addresses:
                            addresses_involved.add(address)
                            
                            # Get asset details (if this is an asset transfer)
                            asset_name = "EVR"  # Default to EVR
                            amount = vout.get('value', 0)
                            
                            # Extract asset details if present
                            asset_info = vout.get('scriptPubKey', {}).get('asset', {})
                            if asset_info:
                                asset_name = asset_info.get('name', "EVR")
                                amount = asset_info.get('amount', 0)
                                
                            # Record the output
                            self.db.add_tx_output(
                                txid=txid,
                                address=address,
                                asset_name=asset_name,
                                amount=amount,
                                vout=vout.get('n', 0)
                            )
                
                # If transaction involves our addresses, track it
                if addresses_involved:
                    logger.info(f"New transaction {txid} involving {len(addresses_involved)} monitored addresses")
                    
                    # Add extra information for matched patterns and anomalies
                    extra_info = {}
                    if matched_patterns:
                        extra_info['matched_patterns'] = matched_patterns
                    if anomaly_result['is_anomaly']:
                        extra_info['anomaly'] = anomaly_result
                    
                    # Store the transaction
                    self.db.add_transaction(txid, 'pending')
                    self.pending_txs.add(txid)
                    
                    # Update balances for these addresses
                    for address in addresses_involved:
                        try:
                            # Update EVR balance
                            evr_balance = await self.rpc_client.getbalance(address)
                            self.db.update_balance(address, "EVR", evr_balance)
                            
                            # Update asset balances
                            assets = await self.rpc_client.listmyassets("*", False)
                            for asset_name, balance in assets.items():
                                self.db.update_balance(address, asset_name, balance)
                        except Exception as e:
                            logger.error(f"Error updating balances for {address}: {e}")
                
            except EvrmoreRPCError as e:
                logger.error(f"RPC error updating transaction {txid}: {e}")
            except Exception as e:
                logger.error(f"Error updating transaction {txid}: {e}")
                
    async def update_all_balances(self) -> None:
        """Update balances for all monitored addresses."""
        for address in self.monitored_addresses:
            try:
                # Get EVR balance
                evr_balance = await self.rpc_client.getbalance(address)
                self.db.update_balance(address, "EVR", evr_balance)
                
                # Get asset balances
                assets = await self.rpc_client.listmyassets("*", False)
                for asset_name, balance in assets.items():
                    self.db.update_balance(address, asset_name, balance)
                    
                    # Update asset details
                    try:
                        asset_data = await self.rpc_client.getassetdata(asset_name)
                        self.db.add_asset({
                            'name': asset_name,
                            'amount': asset_data.amount,
                            'units': asset_data.units,
                            'reissuable': asset_data.reissuable,
                            'has_ipfs': asset_data.has_ipfs,
                            'ipfs_hash': asset_data.ipfs_hash if asset_data.has_ipfs else ''
                        })
                    except Exception as e:
                        logger.warning(f"Couldn't get data for asset {asset_name}: {e}")
                        
            except Exception as e:
                logger.error(f"Error updating balances for {address}: {e}")
                
    async def update_pending_orders(self) -> None:
        """Update status of pending orders."""
        orders = self.db.get_pending_orders()
        
        for order in orders:
            try:
                # Check if payment has been received
                if order['status'] == 'pending' and order['buyer_address']:
                    # In a real system, you would verify that payment was received
                    # For demo purposes, we just simulate a payment verification
                    # payment_verified = await self.verify_payment(order)
                    payment_verified = True  # Simulated for demo
                    
                    if payment_verified:
                        # Create delivery transaction
                        # In a real system, you would create and send the actual transaction
                        # delivery_txid = await self.create_delivery_transaction(order)
                        delivery_txid = f"simulated_delivery_{order['order_id']}"  # Simulated for demo
                        
                        # Update order
                        self.db.update_order_status(
                            order_id=order['order_id'],
                            status='processing',
                            delivery_txid=delivery_txid
                        )
                        
                        # Add delivery transaction to pending
                        self.db.add_transaction(delivery_txid, 'pending')
                        self.pending_txs.add(delivery_txid)
                
                # Check if delivery has been confirmed
                elif order['status'] == 'processing' and order['delivery_txid']:
                    tx = await self.get_transaction_status(order['delivery_txid'])
                    
                    if tx and tx.get('status') == 'confirmed':
                        self.db.update_order_status(
                            order_id=order['order_id'],
                            status='completed'
                        )
                        logger.info(f"Order completed: {order['order_id']}")
                        
            except Exception as e:
                logger.error(f"Error updating order {order['order_id']}: {e}")
                
    async def get_transaction_status(self, txid: str) -> Optional[Dict[str, Any]]:
        """Get transaction status from database or RPC."""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT txid, status, confirmations FROM transactions WHERE txid = ?",
            (txid,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                'txid': row[0],
                'status': row[1],
                'confirmations': row[2]
            }
            
        # If not in database, try to get from RPC
        try:
            tx_details = await self.rpc_client.getrawtransaction(txid, True)
            confirmations = tx_details.get('confirmations', 0)
            status = 'confirmed' if confirmations >= self.confirmations_required else 'confirming'
            
            return {
                'txid': txid,
                'status': status,
                'confirmations': confirmations
            }
        except Exception:
            return None
                
    async def handle_transaction(self, notification: ZMQNotification) -> None:
        """Handle transaction notifications from ZMQ."""
        try:
            txid = notification.hex
            
            # Skip if we're already tracking this transaction
            if txid in self.pending_txs:
                return
                
            # Get transaction details
            tx_details = await self.rpc_client.getrawtransaction(txid, True)
            
            # Check for transaction patterns
            matched_patterns = []
            for pattern in self.patterns:
                if pattern.matches(tx_details):
                    matched_patterns.append(pattern.pattern_name)
                    logger.info(f"Transaction {txid} matches pattern: {pattern.pattern_name}")
            
            # Check for anomalies
            anomaly_result = self.anomaly_detector.check_transaction(tx_details)
            if anomaly_result['is_anomaly']:
                logger.warning(f"ANOMALY DETECTED in transaction {txid} (score: {anomaly_result['anomaly_score']:.2f})")
                for reason in anomaly_result['reasons']:
                    logger.warning(f"  - {reason}")
            
            # Check if transaction involves any of our monitored addresses
            addresses_involved = set()
            for vout in tx_details.get('vout', []):
                for address in vout.get('scriptPubKey', {}).get('addresses', []):
                    if address in self.monitored_addresses:
                        addresses_involved.add(address)
                        
                        # Get asset details (if this is an asset transfer)
                        asset_name = "EVR"  # Default to EVR
                        amount = vout.get('value', 0)
                        
                        # Extract asset details if present
                        asset_info = vout.get('scriptPubKey', {}).get('asset', {})
                        if asset_info:
                            asset_name = asset_info.get('name', "EVR")
                            amount = asset_info.get('amount', 0)
                            
                        # Record the output
                        self.db.add_tx_output(
                            txid=txid,
                            address=address,
                            asset_name=asset_name,
                            amount=amount,
                            vout=vout.get('n', 0)
                        )
            
            # If transaction involves our addresses, track it
            if addresses_involved:
                logger.info(f"New transaction {txid} involving {len(addresses_involved)} monitored addresses")
                
                # Add extra information for matched patterns and anomalies
                extra_info = {}
                if matched_patterns:
                    extra_info['matched_patterns'] = matched_patterns
                if anomaly_result['is_anomaly']:
                    extra_info['anomaly'] = anomaly_result
                
                # Store the transaction
                self.db.add_transaction(txid, 'pending')
                self.pending_txs.add(txid)
                
                # Update balances for these addresses
                for address in addresses_involved:
                    try:
                        # Update EVR balance
                        evr_balance = await self.rpc_client.getbalance(address)
                        self.db.update_balance(address, "EVR", evr_balance)
                        
                        # Update asset balances
                        assets = await self.rpc_client.listmyassets("*", False)
                        for asset_name, balance in assets.items():
                            self.db.update_balance(address, asset_name, balance)
                    except Exception as e:
                        logger.error(f"Error updating balances for {address}: {e}")
        
        except Exception as e:
            logger.error(f"Error handling transaction notification: {e}")
            
    async def handle_block(self, notification: ZMQNotification) -> None:
        """Handle block notifications from ZMQ."""
        try:
            # When a new block is found, update all pending transactions
            await self.update_pending_transactions()
        except Exception as e:
            logger.error(f"Error handling block notification: {e}")
            
    def add_monitored_address(self, address: str, label: Optional[str] = None) -> None:
        """Add an address to monitor."""
        self.db.add_address(address, label)
        self.monitored_addresses.add(address)
        logger.info(f"Now monitoring address: {address} ({label})")
        
    def create_test_order(self, asset: str, amount: Union[Decimal, float], price: Union[Decimal, float]) -> str:
        """Create a test order."""
        # Generate a unique order ID
        order_id = str(uuid.uuid4())
        
        # Check if asset exists in our database
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE asset_name = ?", (asset,))
        asset_check = cursor.fetchone()
        
        if not asset_check:
            # First, add the asset to the database
            cursor.execute(
                """
                INSERT INTO assets (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (asset, "TESTER", float(amount), 0, True, False, "", 8)
            )
            self.db.conn.commit()
            print(f"Created test asset: {asset}")
        
        # Create a test balance for the seller (exchange)
        exchange_addr = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"  # Exchange wallet
        buyer_address = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"   # User wallet
        
        # Create the order in pending status
        cursor.execute(
            """
            INSERT INTO orders (order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (order_id, exchange_addr, buyer_address, asset, float(amount), float(price), float(amount) * float(price), "pending")
        )
        
        self.db.conn.commit()
        return order_id
        
    def add_asset_balance(self, address: str, asset_name: str, amount: Union[Decimal, float]) -> None:
        """Add asset balance to an address."""
        cursor = self.db.conn.cursor()
        
        # First check if the balance entry exists
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = ?",
            (address, asset_name)
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing balance
            cursor.execute(
                "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?",
                (float(amount), address, asset_name)
            )
        else:
            # Insert new balance
            cursor.execute(
                "INSERT INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
                (address, asset_name, float(amount))
            )
        
        self.db.conn.commit()
        logger.info(f"Added {amount} {asset_name} to {address}")
    
    def subtract_asset_balance(self, address: str, asset_name: str, amount: Union[Decimal, float]) -> None:
        """Subtract asset balance from an address."""
        cursor = self.db.conn.cursor()
        
        # First check if the balance entry exists
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = ?",
            (address, asset_name)
        )
        result = cursor.fetchone()
        
        if result and result[0] >= float(amount):
            # Update existing balance
            cursor.execute(
                "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
                (float(amount), address, asset_name)
            )
            self.db.conn.commit()
            logger.info(f"Subtracted {amount} {asset_name} from {address}")
        else:
            logger.warning(f"Insufficient balance to subtract {amount} {asset_name} from {address}")
    
    def add_credits_balance(self, address: str, amount: Union[Decimal, float]) -> None:
        """Add CREDITS balance to an address."""
        self.add_asset_balance(address, "CREDITS", amount)
    
    def subtract_credits_balance(self, address: str, amount: Union[Decimal, float]) -> None:
        """Subtract CREDITS balance from an address."""
        self.subtract_asset_balance(address, "CREDITS", amount)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Evrmore Balance Tracker')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no ZMQ, minimal testing)')
    parser.add_argument('--address', action='append', help='Add an address to monitor')
    parser.add_argument('--db', default='balance_tracker.db', help='Path to database file')
    parser.add_argument('--auto-confirm', action='store_true', help='Automatically confirm test orders')
    args = parser.parse_args()

    # Initialize the balance tracker
    tracker = BalanceTracker(args.db)
    
    # Add some addresses to monitor
    if args.address:
        for addr in args.address:
            tracker.add_monitored_address(addr, "Command Line Address")
    
    if args.test:
        print("Running in test mode...")
        
        # Add some test addresses if none were specified
        if not args.address:
            exchange_addr = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"
            user_addr = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"
            
            tracker.add_monitored_address(exchange_addr, "Exchange Wallet")
            tracker.add_monitored_address(user_addr, "User Wallet")
            print(f"Added addresses to monitor: {exchange_addr} (Exchange), {user_addr} (User)")
        
        # Create a test asset and order
        try:
            asset = "TESTASSET"
            amount = 10
            price = 0.5  # Price in CREDITS per unit
            
            # First, add the test assets to the database
            cursor = tracker.db.conn.cursor()
            
            # Add TESTASSET if it doesn't exist
            cursor.execute("SELECT * FROM assets WHERE asset_name = ?", (asset,))
            asset_check = cursor.fetchone()
            
            if not asset_check:
                # Add the asset to the database if it doesn't exist
                cursor.execute(
                    """
                    INSERT INTO assets (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (asset, "TESTER", float(amount), 0, True, False, "", 8)
                )
                tracker.db.conn.commit()
                print(f"Created test asset: {asset}")
            
            # Add CREDITS if it doesn't exist
            cursor.execute("SELECT * FROM assets WHERE asset_name = ?", ("CREDITS",))
            credits_check = cursor.fetchone()
            
            if not credits_check:
                # Add CREDITS to the database
                cursor.execute(
                    """
                    INSERT INTO assets (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    ("CREDITS", "SYSTEM", 1000000.0, 0, True, False, "", 8)
                )
                tracker.db.conn.commit()
                print("Created CREDITS asset for payments")
            
            # Create a test balance for the seller (exchange)
            exchange_addr = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"
            tracker.add_asset_balance(exchange_addr, asset, amount)
            print(f"Created test balance: {amount} {asset} for {exchange_addr}")
            
            # Make sure both addresses have CREDITS
            buyer_addr = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"
            tracker.add_asset_balance(buyer_addr, "CREDITS", 100.0)
            tracker.add_asset_balance(exchange_addr, "CREDITS", 100.0)
            print(f"Added CREDITS balances for testing")
            
            # Create a test order
            order_id = tracker.create_test_order(asset, amount, price)
            print(f"Created test order: {order_id} for {amount} {asset} at {price} CREDITS each ({amount * price} CREDITS total)")
            
            # Automatically confirm the test order if requested
            if args.auto_confirm:
                # Use the existing database connection
                cursor = tracker.db.conn.cursor()
                
                # Get the pending order
                cursor.execute("SELECT * FROM orders WHERE status = 'pending' AND order_id = ?", (order_id,))
                order = cursor.fetchone()
                
                if order:
                    order_id = order[0]
                    total_price = order[6]  # Total cost is at index 6
                    
                    # Generate a unique transaction ID
                    tx_id = str(uuid.uuid4())
                    block_hash = "0000000000000000000000000000000000000000000000000000000000000000"
                    block_height = 12345
                    timestamp = datetime.now()
                    confirmations = 6
                    
                    # Insert a transaction with status 'confirmed'
                    cursor.execute("""
                        INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (tx_id, block_hash, block_height, timestamp, confirmations, 'confirmed'))
                    
                    # Update the order status to processing and set the payment_txid
                    cursor.execute("""
                        UPDATE orders SET status = 'processing', payment_txid = ? WHERE order_id = ?
                    """, (tx_id, order_id))
                    
                    # Update the seller's EVR balance
                    cursor.execute("""
                        SELECT * FROM orders WHERE order_id = ?
                    """, (order_id,))
                    order = cursor.fetchone()
                    seller_address = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"  # Exchange wallet
                    buyer_address = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"   # User wallet
                    
                    # Add CREDITS to the seller's balance
                    tracker.add_credits_balance(seller_address, total_price)
                    tracker.subtract_credits_balance(buyer_address, total_price)
                    
                    print(f"Simulated payment for order {order_id[:8]}... with transaction {tx_id[:8]}...")
                    print(f"Order status updated to 'processing'")
                    print(f"Added {total_price} CREDITS to {seller_address[:8]}...")
                    
                    # Simulate delivery
                    # Generate a unique transaction ID for delivery
                    delivery_tx_id = str(uuid.uuid4())
                    block_height += 1
                    
                    # Insert a transaction for the delivery
                    cursor.execute("""
                        INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (delivery_tx_id, block_hash, block_height, timestamp, confirmations, 'confirmed'))
                    
                    # Update the order status to completed and set the delivery_txid
                    cursor.execute("""
                        UPDATE orders SET status = 'completed', delivery_txid = ? WHERE order_id = ?
                    """, (delivery_tx_id, order_id))
                    
                    # Transfer the asset from seller to buyer
                    cursor.execute("SELECT asset_name, amount FROM orders WHERE order_id = ?", (order_id,))
                    asset_info = cursor.fetchone()
                    asset_name = asset_info[0]
                    asset_amount = asset_info[1]
                    
                    # Subtract from seller, add to buyer
                    tracker.subtract_asset_balance(seller_address, asset_name, asset_amount)
                    tracker.add_asset_balance(buyer_address, asset_name, asset_amount)
                    
                    tracker.db.conn.commit()
                    print(f"Simulated delivery for order {order_id[:8]}... with transaction {delivery_tx_id[:8]}...")
                    print(f"Order status updated to 'completed'")
                    print(f"Transferred {asset_amount} {asset_name} from {seller_address[:8]}... to {buyer_address[:8]}...")
                
            print("Test mode completed.")
            return  # Exit after completing test mode
            
        except Exception as e:
            print(f"Error creating test order: {e}")
            # Continue with the program even if test order creation fails


if __name__ == "__main__":
    main() 