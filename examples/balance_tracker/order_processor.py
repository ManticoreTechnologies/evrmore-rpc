#!/usr/bin/env python3
"""
Order Processor for Evrmore Balance Tracker

This script provides a command-line interface to manage orders in the balance tracker:
- Create new orders
- Process payments for pending orders
- Complete delivery for processing orders
- Cancel pending or processing orders
- Check order status

It works with the existing balance_tracker.db database and serves as a separate
utility for order management.
"""

import argparse
import sqlite3
import uuid
import datetime
import sys
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('order_processor')

# Rich console for pretty output
console = Console()

class OrderProcessor:
    """
    Handles order processing, payments, and delivery for the balance tracker system.
    """
    
    def __init__(self, db_path: str = "balance_tracker.db"):
        """Initialize the order processor with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.info(f"Connected to database at {db_path}")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get orders from the database, optionally filtered by status.
        
        Args:
            status: Filter by order status (pending, processing, completed, cancelled, failed)
                   If None, returns all orders
        
        Returns:
            List of order dictionaries
        """
        cursor = self.conn.cursor()
        
        if status:
            sql = """
                SELECT * FROM orders 
                WHERE status = ?
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (status,))
        else:
            sql = """
                SELECT * FROM orders
                ORDER BY created_at DESC
            """
            cursor.execute(sql)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """
        Get a specific order by ID.
        
        Args:
            order_id: The order ID to retrieve
            
        Returns:
            Order dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_order(self, asset_name: str, amount: Union[Decimal, float], 
                    price: Union[Decimal, float], seller_address: str, 
                    buyer_address: Optional[str] = None) -> str:
        """
        Create a new order in the system.
        
        Args:
            asset_name: Name of the asset being sold
            amount: Amount of the asset
            price: Price per unit in EVR
            seller_address: Address of the seller
            buyer_address: Address of the buyer (optional)
            
        Returns:
            The newly created order ID
        """
        # Generate a unique order ID
        order_id = str(uuid.uuid4())
        total_cost = float(amount) * float(price)
        
        cursor = self.conn.cursor()
        
        # Check if the seller has enough of the asset
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = ?",
            (seller_address, asset_name)
        )
        result = cursor.fetchone()
        
        if not result or result['balance'] < float(amount):
            raise ValueError(f"Seller doesn't have enough {asset_name} for this order")
        
        # Create the order
        cursor.execute(
            """
            INSERT INTO orders 
            (order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'), datetime('now'))
            """,
            (order_id, seller_address, buyer_address, asset_name, float(amount), float(price), total_cost)
        )
        
        self.conn.commit()
        logger.info(f"Created order {order_id} for {amount} {asset_name} at {price} EVR each (total: {total_cost} EVR)")
        return order_id
    
    def process_payment(self, order_id: str) -> str:
        """
        Process payment for a pending order, moving it to the processing state.
        
        In a real system, this would verify that payment was received.
        For this example, we simulate receiving payment.
        
        Args:
            order_id: The order ID to process payment for
            
        Returns:
            The transaction ID for the payment
        """
        cursor = self.conn.cursor()
        
        # Get the order
        cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'pending'", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise ValueError(f"Order {order_id} not found or not in pending status")
        
        # Check if the buyer has enough EVR
        buyer_address = order['buyer_address']
        total_cost = order['total_cost']
        
        if not buyer_address:
            raise ValueError("This order doesn't have a buyer address specified")
        
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = 'EVR'",
            (buyer_address,)
        )
        result = cursor.fetchone()
        
        if not result or result['balance'] < total_cost:
            raise ValueError(f"Buyer doesn't have enough EVR for this order")
        
        # Generate a transaction ID for the payment
        txid = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        # Create a confirmed transaction for the payment
        cursor.execute(
            """
            INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (txid, "0000000000000000000000000000000000000000000000000000000000000000", 
             12345, timestamp, 6, 'confirmed')
        )
        
        # Update the order status
        cursor.execute(
            """
            UPDATE orders 
            SET status = 'processing', payment_txid = ?, updated_at = datetime('now') 
            WHERE order_id = ?
            """,
            (txid, order_id)
        )
        
        # Transfer EVR from buyer to seller
        seller_address = order['seller_address']
        
        # Subtract from buyer
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = 'EVR'",
            (total_cost, buyer_address)
        )
        
        # Add to seller
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = 'EVR'",
            (seller_address,)
        )
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = 'EVR'",
                (total_cost, seller_address)
            )
        else:
            cursor.execute(
                "INSERT INTO balances (address, asset_name, balance, last_updated) VALUES (?, ?, ?, datetime('now'))",
                (seller_address, "EVR", total_cost)
            )
        
        self.conn.commit()
        logger.info(f"Processed payment for order {order_id}: {total_cost} EVR transferred from {buyer_address} to {seller_address}")
        return txid
    
    def deliver_asset(self, order_id: str) -> str:
        """
        Deliver asset for a processing order, moving it to the completed state.
        
        In a real system, this would create and broadcast the actual transaction.
        For this example, we simulate the delivery.
        
        Args:
            order_id: The order ID to deliver asset for
            
        Returns:
            The transaction ID for the delivery
        """
        cursor = self.conn.cursor()
        
        # Get the order
        cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'processing'", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise ValueError(f"Order {order_id} not found or not in processing status")
        
        seller_address = order['seller_address']
        buyer_address = order['buyer_address']
        asset_name = order['asset_name']
        amount = order['amount']
        
        # Check if seller still has the asset
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = ?",
            (seller_address, asset_name)
        )
        result = cursor.fetchone()
        
        if not result or result['balance'] < amount:
            raise ValueError(f"Seller no longer has enough {asset_name} for this order")
        
        # Generate a transaction ID for the delivery
        txid = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        # Create a confirmed transaction for the delivery
        cursor.execute(
            """
            INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (txid, "0000000000000000000000000000000000000000000000000000000000000000", 
             12346, timestamp, 6, 'confirmed')
        )
        
        # Add outputs for the delivery transaction
        cursor.execute(
            """
            INSERT INTO tx_outputs (txid, address, asset_name, amount, vout)
            VALUES (?, ?, ?, ?, ?)
            """,
            (txid, buyer_address, asset_name, amount, 0)
        )
        
        # Update the order status
        cursor.execute(
            """
            UPDATE orders 
            SET status = 'completed', delivery_txid = ?, updated_at = datetime('now') 
            WHERE order_id = ?
            """,
            (txid, order_id)
        )
        
        # Transfer asset from seller to buyer
        # Subtract from seller
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
            (amount, seller_address, asset_name)
        )
        
        # Add to buyer
        cursor.execute(
            "SELECT balance FROM balances WHERE address = ? AND asset_name = ?",
            (buyer_address, asset_name)
        )
        result = cursor.fetchone()
        
        if result:
            cursor.execute(
                "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?",
                (amount, buyer_address, asset_name)
            )
        else:
            cursor.execute(
                "INSERT INTO balances (address, asset_name, balance, last_updated) VALUES (?, ?, ?, datetime('now'))",
                (buyer_address, asset_name, amount)
            )
        
        self.conn.commit()
        logger.info(f"Delivered asset for order {order_id}: {amount} {asset_name} transferred from {seller_address} to {buyer_address}")
        return txid
    
    def cancel_order(self, order_id: str, reason: str = "Cancelled by user") -> None:
        """
        Cancel an order that is in pending or processing state.
        
        If the order is in processing state (payment already made), this will
        refund the payment to the buyer.
        
        Args:
            order_id: The order ID to cancel
            reason: The reason for cancellation
        """
        cursor = self.conn.cursor()
        
        # Get the order
        cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status IN ('pending', 'processing')", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise ValueError(f"Order {order_id} not found or not in cancellable status")
        
        # If order is in processing state, need to refund payment
        if order['status'] == 'processing':
            seller_address = order['seller_address']
            buyer_address = order['buyer_address']
            total_cost = order['total_cost']
            
            # Subtract from seller
            cursor.execute(
                "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = 'EVR'",
                (total_cost, seller_address)
            )
            
            # Add back to buyer
            cursor.execute(
                "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = 'EVR'",
                (total_cost, buyer_address)
            )
            
            logger.info(f"Refunded {total_cost} EVR from {seller_address} to {buyer_address}")
        
        # Update the order status
        cursor.execute(
            """
            UPDATE orders 
            SET status = 'cancelled', updated_at = datetime('now') 
            WHERE order_id = ?
            """,
            (order_id,)
        )
        
        self.conn.commit()
        logger.info(f"Cancelled order {order_id}: {reason}")
    
    def display_orders(self, orders: List[Dict]) -> None:
        """
        Display orders in a formatted table.
        
        Args:
            orders: List of order dictionaries to display
        """
        if not orders:
            console.print("No orders found", style="yellow")
            return
        
        table = Table(title="Orders")
        
        # Add columns
        table.add_column("Order ID", style="cyan")
        table.add_column("Asset", style="green")
        table.add_column("Amount", justify="right")
        table.add_column("Price (EVR)", justify="right")
        table.add_column("Total Cost", justify="right")
        table.add_column("Status", style="yellow")
        table.add_column("Created At", style="dim")
        table.add_column("Seller", style="blue")
        table.add_column("Buyer", style="magenta")
        
        # Add rows
        for order in orders:
            table.add_row(
                order['order_id'][:8] + "...",
                order['asset_name'],
                f"{order['amount']:.6f}",
                f"{order['price']:.6f}",
                f"{order['total_cost']:.6f}",
                order['status'],
                order['created_at'],
                order['seller_address'][:8] + "...",
                order['buyer_address'][:8] + "..." if order['buyer_address'] else "None"
            )
        
        console.print(table)
    
    def display_balances(self) -> None:
        """Display all balances in the system."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT b.address, a.label, b.asset_name, b.balance 
            FROM balances b 
            LEFT JOIN addresses a ON b.address = a.address 
            ORDER BY b.address, b.asset_name
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            console.print("No balances found", style="yellow")
            return
        
        table = Table(title="Balances")
        
        # Add columns
        table.add_column("Address", style="cyan")
        table.add_column("Label", style="green")
        table.add_column("Asset", style="blue")
        table.add_column("Balance", justify="right")
        
        # Add rows
        for row in rows:
            table.add_row(
                row['address'][:8] + "...",
                row['label'] or "N/A",
                row['asset_name'],
                f"{row['balance']:.6f}"
            )
        
        console.print(table)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Order processor for Evrmore Balance Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List orders command
    list_parser = subparsers.add_parser('list', help='List orders')
    list_parser.add_argument('--status', choices=['pending', 'processing', 'completed', 'cancelled', 'failed'],
                            help='Filter by status')
    
    # Create order command
    create_parser = subparsers.add_parser('create', help='Create a new order')
    create_parser.add_argument('--asset', required=True, help='Asset name')
    create_parser.add_argument('--amount', required=True, type=float, help='Asset amount')
    create_parser.add_argument('--price', required=True, type=float, help='Price per unit in EVR')
    create_parser.add_argument('--seller', required=True, help='Seller address')
    create_parser.add_argument('--buyer', help='Buyer address')
    
    # Process payment command
    pay_parser = subparsers.add_parser('pay', help='Process payment for an order')
    pay_parser.add_argument('order_id', help='Order ID to process payment for')
    
    # Deliver asset command
    deliver_parser = subparsers.add_parser('deliver', help='Deliver asset for an order')
    deliver_parser.add_argument('order_id', help='Order ID to deliver asset for')
    
    # Cancel order command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel an order')
    cancel_parser.add_argument('order_id', help='Order ID to cancel')
    cancel_parser.add_argument('--reason', default='Cancelled by user', help='Reason for cancellation')
    
    # Get order command
    get_parser = subparsers.add_parser('get', help='Get order details')
    get_parser.add_argument('order_id', help='Order ID to get details for')
    
    # List balances command
    balances_parser = subparsers.add_parser('balances', help='List all balances')
    
    # Auto process command
    auto_parser = subparsers.add_parser('auto', help='Automatically process and complete all pending orders')
    
    # General options
    parser.add_argument('--db', default='balance_tracker.db', help='Path to database file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize the order processor
    processor = OrderProcessor(args.db)
    
    try:
        if args.command == 'list':
            orders = processor.get_orders(args.status)
            processor.display_orders(orders)
            
        elif args.command == 'create':
            order_id = processor.create_order(
                asset_name=args.asset,
                amount=args.amount,
                price=args.price,
                seller_address=args.seller,
                buyer_address=args.buyer
            )
            console.print(f"Created order [bold cyan]{order_id}[/]")
            
        elif args.command == 'pay':
            txid = processor.process_payment(args.order_id)
            console.print(f"Processed payment for order [bold cyan]{args.order_id}[/]")
            console.print(f"Payment transaction ID: [bold green]{txid}[/]")
            
        elif args.command == 'deliver':
            txid = processor.deliver_asset(args.order_id)
            console.print(f"Delivered asset for order [bold cyan]{args.order_id}[/]")
            console.print(f"Delivery transaction ID: [bold green]{txid}[/]")
            
        elif args.command == 'cancel':
            processor.cancel_order(args.order_id, args.reason)
            console.print(f"Cancelled order [bold cyan]{args.order_id}[/]: {args.reason}")
            
        elif args.command == 'get':
            order = processor.get_order(args.order_id)
            if order:
                processor.display_orders([order])
            else:
                console.print(f"Order [bold cyan]{args.order_id}[/] not found", style="red")
                
        elif args.command == 'balances':
            processor.display_balances()
            
        elif args.command == 'auto':
            # Get all pending orders
            pending_orders = processor.get_orders('pending')
            console.print(f"Found {len(pending_orders)} pending orders")
            
            # Process payments for all pending orders
            for order in pending_orders:
                try:
                    txid = processor.process_payment(order['order_id'])
                    console.print(f"Processed payment for order [bold cyan]{order['order_id']}[/]")
                    console.print(f"Payment transaction ID: [bold green]{txid}[/]")
                except Exception as e:
                    console.print(f"Error processing payment for order {order['order_id']}: {e}", style="red")
            
            # Get all processing orders
            processing_orders = processor.get_orders('processing')
            console.print(f"Found {len(processing_orders)} processing orders")
            
            # Deliver assets for all processing orders
            for order in processing_orders:
                try:
                    txid = processor.deliver_asset(order['order_id'])
                    console.print(f"Delivered asset for order [bold cyan]{order['order_id']}[/]")
                    console.print(f"Delivery transaction ID: [bold green]{txid}[/]")
                except Exception as e:
                    console.print(f"Error delivering asset for order {order['order_id']}: {e}", style="red")
            
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")
        
    finally:
        processor.close()

if __name__ == "__main__":
    main() 