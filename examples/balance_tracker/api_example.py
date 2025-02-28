#!/usr/bin/env python3
"""
Balance Tracker API Example

This example shows how to create a simple REST API using FastAPI 
that integrates with the balance tracker to provide NFT exchange functionality.

Requirements:
- FastAPI: pip install fastapi uvicorn
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import the database manager and tracker from our tracker
from tracker import DatabaseManager, BalanceTracker, TransactionPattern

# Create FastAPI app
app = FastAPI(
    title="Evrmore NFT Exchange API",
    description="API for tracking balances and managing NFT orders with advanced analytics",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Instantiate the database manager
db = DatabaseManager("balance_tracker.db")

# Maintain a global tracker instance
tracker = None
tracker_task = None

# Models for API requests and responses
class AddressModel(BaseModel):
    address: str
    label: Optional[str] = None

class OrderCreateModel(BaseModel):
    seller_address: str
    buyer_address: Optional[str] = None
    asset_name: str
    amount: float = Field(..., gt=0)
    price: float = Field(..., gt=0)

class OrderUpdateModel(BaseModel):
    status: str
    payment_txid: Optional[str] = None
    delivery_txid: Optional[str] = None

class BalanceModel(BaseModel):
    address: str
    asset_name: str

class TransactionPatternModel(BaseModel):
    pattern_name: str
    description: str
    criteria: Dict[str, Any]

class AddressBalanceResponse(BaseModel):
    address: str
    balances: Dict[str, float]
    total_assets: int

class OrderResponse(BaseModel):
    order_id: str
    seller_address: str
    buyer_address: Optional[str]
    asset_name: str
    amount: float
    price: float
    total_cost: float
    status: str
    created_at: str
    updated_at: Optional[str]
    payment_txid: Optional[str]
    delivery_txid: Optional[str]

class TransactionResponse(BaseModel):
    txid: str
    confirmations: int
    status: str
    block_hash: Optional[str]
    block_height: Optional[int]
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None
    anomaly_reasons: Optional[List[str]] = None
    matched_patterns: Optional[List[str]] = None

# Dependency to get DB
def get_db():
    return db

@app.on_event("startup")
async def startup_event():
    """Initialize the tracker when the API starts."""
    global tracker, tracker_task
    tracker = BalanceTracker("balance_tracker.db")
    
    # Initialize the tracker but don't start the live display
    await tracker.initialize()
    
    # Start update loop in the background
    tracker_task = asyncio.create_task(tracker.update_loop())

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when shutting down."""
    global tracker, tracker_task
    if tracker:
        await tracker.stop()
    if tracker_task:
        tracker_task.cancel()
        try:
            await tracker_task
        except asyncio.CancelledError:
            pass
    
    # Stop the WebSocket ticker
    if hasattr(tracker, 'real_time_monitor'):
        await tracker.real_time_monitor.stop_ticker()
    
    db.close()

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Evrmore NFT Exchange API",
        "version": "0.2.0",
        "description": "API for tracking balances and managing NFT orders with advanced analytics"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    try:
        # Handle the WebSocket connection through our RealTimeMonitor
        await tracker.real_time_monitor.handle_websocket_connection(websocket)
    except WebSocketDisconnect:
        pass

@app.post("/addresses", tags=["Addresses"])
async def add_address(address_data: AddressModel, db: DatabaseManager = Depends(get_db)):
    """Add a new address to monitor."""
    db.add_address(address_data.address, address_data.label)
    
    # Also add to the tracker's in-memory set
    if tracker:
        tracker.monitored_addresses.add(address_data.address)
        
    return {"status": "success", "message": f"Now monitoring address: {address_data.address}"}

@app.get("/addresses", tags=["Addresses"])
async def list_addresses(db: DatabaseManager = Depends(get_db)):
    """List all monitored addresses."""
    addresses = []
    for item in db.get_balances_summary():
        addresses.append({
            "address": item['address'],
            "label": item['label'],
            "asset_count": item['asset_count'],
            "evr_balance": item['evr_balance']
        })
    return addresses

@app.get("/addresses/{address}/balances", response_model=AddressBalanceResponse, tags=["Balances"])
async def get_address_balances(address: str, db: DatabaseManager = Depends(get_db)):
    """Get all balances for an address."""
    balances_data = db.get_address_balances(address)
    
    if not balances_data:
        return {
            "address": address,
            "balances": {},
            "total_assets": 0
        }
        
    balances = {}
    for item in balances_data:
        balances[item['asset_name']] = float(item['balance'])
        
    return {
        "address": address,
        "balances": balances,
        "total_assets": len(balances)
    }

@app.post("/orders", tags=["Orders"])
async def create_order(order_data: OrderCreateModel, db: DatabaseManager = Depends(get_db)):
    """Create a new order."""
    order_id = str(uuid.uuid4())
    
    try:
        db.create_order(
            order_id=order_id,
            seller_address=order_data.seller_address,
            buyer_address=order_data.buyer_address,
            asset_name=order_data.asset_name,
            amount=order_data.amount,
            price=order_data.price
        )
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": f"Order created for {order_data.amount} {order_data.asset_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders", tags=["Orders"])
async def list_orders(status: Optional[str] = None, db: DatabaseManager = Depends(get_db)):
    """List all orders, optionally filtered by status."""
    cursor = db.conn.cursor()
    
    query = """
        SELECT order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, 
               status, created_at, updated_at, payment_txid, delivery_txid
        FROM orders
    """
    
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
        
    cursor.execute(query, params)
    
    columns = [col[0] for col in cursor.description]
    orders = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return orders

@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def get_order(order_id: str, db: DatabaseManager = Depends(get_db)):
    """Get details for a specific order."""
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT order_id, seller_address, buyer_address, asset_name, amount, price, total_cost,
               status, created_at, updated_at, payment_txid, delivery_txid
        FROM orders
        WHERE order_id = ?
        """,
        (order_id,)
    )
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
    columns = [col[0] for col in cursor.description]
    order = dict(zip(columns, row))
    
    return order

@app.patch("/orders/{order_id}", tags=["Orders"])
async def update_order(order_id: str, order_data: OrderUpdateModel, db: DatabaseManager = Depends(get_db)):
    """Update an order's status and associated transactions."""
    try:
        db.update_order_status(
            order_id=order_id,
            status=order_data.status,
            payment_txid=order_data.payment_txid,
            delivery_txid=order_data.delivery_txid
        )
        
        # If a new transaction ID was provided, add it to tracking
        if order_data.payment_txid and tracker:
            db.add_transaction(order_data.payment_txid, 'pending')
            tracker.pending_txs.add(order_data.payment_txid)
            
        if order_data.delivery_txid and tracker:
            db.add_transaction(order_data.delivery_txid, 'pending')
            tracker.pending_txs.add(order_data.delivery_txid)
            
        return {
            "status": "success",
            "message": f"Order {order_id} updated to {order_data.status}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transactions", tags=["Transactions"])
async def list_transactions(status: Optional[str] = None, db: DatabaseManager = Depends(get_db)):
    """List all tracked transactions, optionally filtered by status."""
    cursor = db.conn.cursor()
    
    query = """
        SELECT txid, block_hash, block_height, confirmations, status, timestamp
        FROM transactions
    """
    
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
        
    cursor.execute(query, params)
    
    columns = [col[0] for col in cursor.description]
    transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return transactions

@app.get("/transactions/{txid}", response_model=TransactionResponse, tags=["Transactions"])
async def get_transaction(txid: str, db: DatabaseManager = Depends(get_db)):
    """Get details for a specific transaction."""
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT txid, block_hash, block_height, confirmations, status
        FROM transactions
        WHERE txid = ?
        """,
        (txid,)
    )
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Transaction {txid} not found")
        
    columns = [col[0] for col in cursor.description]
    transaction = dict(zip(columns, row))
    
    # Add advanced analytics if available
    if tracker and hasattr(tracker, 'rpc_client'):
        try:
            # Get transaction details
            tx_details = await tracker.rpc_client.getrawtransaction(txid, True)
            
            # Check for anomalies
            anomaly_result = tracker.anomaly_detector.check_transaction(tx_details)
            if anomaly_result['is_anomaly']:
                transaction['is_anomaly'] = True
                transaction['anomaly_score'] = anomaly_result['anomaly_score']
                transaction['anomaly_reasons'] = anomaly_result['reasons']
            
            # Check for pattern matches
            matched_patterns = []
            for pattern in tracker.patterns:
                if pattern.matches(tx_details):
                    matched_patterns.append(pattern.pattern_name)
            
            if matched_patterns:
                transaction['matched_patterns'] = matched_patterns
                
        except Exception as e:
            # Just log the error but still return basic transaction info
            print(f"Error analyzing transaction {txid}: {e}")
    
    return transaction

@app.post("/transactions/{txid}/outputs", tags=["Transactions"])
async def add_transaction_output(
    txid: str,
    address: str,
    asset_name: str,
    amount: float,
    vout: int,
    db: DatabaseManager = Depends(get_db)
):
    """Manually add a transaction output (useful for testing)."""
    try:
        db.add_tx_output(txid, address, asset_name, amount, vout)
        return {
            "status": "success",
            "message": f"Added output for {amount} {asset_name} to {address}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/stats", tags=["General"])
async def get_stats(db: DatabaseManager = Depends(get_db)):
    """Get overall statistics."""
    # Get address count
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM addresses")
    address_count = cursor.fetchone()[0]
    
    # Get asset count
    cursor.execute("SELECT COUNT(*) FROM assets")
    asset_count = cursor.fetchone()[0]
    
    # Get order statistics
    order_stats = db.get_order_summary()
    
    # Get transaction statistics
    cursor.execute(
        """
        SELECT status, COUNT(*) as count
        FROM transactions
        GROUP BY status
        """
    )
    tx_stats = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Add advanced statistics
    advanced_stats = {}
    if tracker and hasattr(tracker, 'anomaly_detector'):
        if tracker.anomaly_detector.is_initialized:
            advanced_stats["baseline_stats"] = tracker.anomaly_detector.baseline_stats
            advanced_stats["anomaly_sensitivity"] = tracker.anomaly_detector.sensitivity
    
    return {
        "addresses": address_count,
        "assets": asset_count,
        "orders": order_stats,
        "transactions": tx_stats,
        "advanced_stats": advanced_stats
    }

# New endpoints for advanced features
@app.post("/patterns", tags=["Advanced"])
async def register_pattern(pattern_data: TransactionPatternModel):
    """Register a new transaction pattern to watch for."""
    if not tracker:
        raise HTTPException(status_code=503, detail="Tracker not initialized")
    
    pattern = TransactionPattern(
        pattern_name=pattern_data.pattern_name,
        match_criteria={
            "description": pattern_data.description,
            **pattern_data.criteria
        }
    )
    
    tracker.register_pattern(pattern)
    
    return {
        "status": "success",
        "message": f"Registered pattern: {pattern_data.pattern_name}"
    }

@app.get("/patterns", tags=["Advanced"])
async def list_patterns():
    """List all registered transaction patterns."""
    if not tracker:
        raise HTTPException(status_code=503, detail="Tracker not initialized")
    
    patterns = []
    for pattern in tracker.patterns:
        patterns.append({
            "pattern_name": pattern.pattern_name,
            "description": pattern.description,
            "criteria": pattern.criteria
        })
    
    return patterns

@app.post("/anomaly-detection/sensitivity", tags=["Advanced"])
async def set_anomaly_sensitivity(sensitivity: float):
    """Set the sensitivity of the anomaly detector."""
    if not tracker or not hasattr(tracker, 'anomaly_detector'):
        raise HTTPException(status_code=503, detail="Anomaly detector not initialized")
    
    if sensitivity < 0 or sensitivity > 1:
        raise HTTPException(status_code=400, detail="Sensitivity must be between 0 and 1")
    
    tracker.anomaly_detector.sensitivity = sensitivity
    
    return {
        "status": "success",
        "message": f"Anomaly detection sensitivity set to {sensitivity}"
    }

# For testing purposes, add some endpoints to create test data
@app.post("/test/addresses", tags=["Testing"])
async def add_test_addresses(background_tasks: BackgroundTasks):
    """Add some test addresses."""
    test_addresses = [
        {"address": "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB", "label": "Exchange Wallet"},
        {"address": "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7", "label": "User Wallet"},
        {"address": "ERuZK72vesRdKxDGYZ1B2PcCzctvoC7jHx", "label": "NFT Creator"}
    ]
    
    for addr in test_addresses:
        db.add_address(addr["address"], addr["label"])
        if tracker:
            tracker.monitored_addresses.add(addr["address"])
    
    return {"status": "success", "message": f"Added {len(test_addresses)} test addresses"}

@app.post("/test/orders", tags=["Testing"])
async def add_test_orders():
    """Add some test orders."""
    test_orders = [
        {
            "seller_address": "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7",
            "buyer_address": "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB",
            "asset_name": "RAVEN/LOGO",
            "amount": 1,
            "price": 100
        },
        {
            "seller_address": "ERuZK72vesRdKxDGYZ1B2PcCzctvoC7jHx",
            "buyer_address": None,  # Open order
            "asset_name": "MANTICORE/NFT",
            "amount": 1,
            "price": 500
        }
    ]
    
    order_ids = []
    for order in test_orders:
        if tracker:
            order_id = tracker.create_test_order(
                seller=order["seller_address"],
                buyer=order["buyer_address"],
                asset=order["asset_name"],
                amount=order["amount"],
                price=order["price"]
            )
        else:
            order_id = str(uuid.uuid4())
            db.create_order(
                order_id=order_id,
                seller_address=order["seller_address"],
                buyer_address=order["buyer_address"],
                asset_name=order["asset_name"],
                amount=order["amount"],
                price=order["price"]
            )
        order_ids.append(order_id)
    
    return {
        "status": "success", 
        "message": f"Added {len(test_orders)} test orders",
        "order_ids": order_ids
    }

@app.post("/test/simulate-payment/{order_id}", tags=["Testing"])
async def simulate_payment(order_id: str):
    """Simulate a payment for an order."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    # Create a simulated payment transaction
    payment_txid = f"simulated_payment_{order_id}"
    db.add_transaction(payment_txid, 'pending')
    
    # Update the order
    db.update_order_status(
        order_id=order_id,
        status='processing',
        payment_txid=payment_txid
    )
    
    # Add to pending transactions for the tracker to monitor
    if tracker:
        tracker.pending_txs.add(payment_txid)
    
    return {
        "status": "success",
        "message": f"Simulated payment for order {order_id}",
        "payment_txid": payment_txid
    }

@app.post("/test/simulate-confirmation/{txid}", tags=["Testing"])
async def simulate_confirmation(txid: str, confirmations: int = 6):
    """Simulate confirmations for a transaction."""
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE txid = ?", (txid,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Transaction {txid} not found")
    
    # Update the transaction with simulated confirmations
    db.update_transaction(
        txid=txid,
        block_hash="0000000000000000000000000000000000000000000000000000000000000000",
        block_height=1000000,
        confirmations=confirmations,
        status='confirmed' if confirmations >= 6 else 'confirming'
    )
    
    # If confirmed and a delivery transaction, update the associated order
    if confirmations >= 6:
        cursor.execute(
            """
            SELECT order_id FROM orders
            WHERE payment_txid = ? OR delivery_txid = ?
            """,
            (txid, txid)
        )
        
        order_ids = [row[0] for row in cursor.fetchall()]
        
        # Update orders if this transaction is associated with any
        for order_id in order_ids:
            cursor.execute(
                "SELECT status, payment_txid, delivery_txid FROM orders WHERE order_id = ?",
                (order_id,)
            )
            order = cursor.fetchone()
            
            if order[0] == 'processing' and order[2] == txid:
                # If this is a delivery transaction
                db.update_order_status(order_id, 'completed')
            elif order[0] == 'pending' and order[1] == txid:
                # If this is a payment transaction
                # Create a simulated delivery transaction
                delivery_txid = f"simulated_delivery_{order_id}"
                db.add_transaction(delivery_txid, 'pending')
                
                # Update the order
                db.update_order_status(
                    order_id=order_id,
                    status='processing',
                    delivery_txid=delivery_txid
                )
                
                # Add to pending transactions
                if tracker:
                    tracker.pending_txs.add(delivery_txid)
    
    return {
        "status": "success",
        "message": f"Simulated {confirmations} confirmations for transaction {txid}"
    }

@app.post("/test/generate-anomaly", tags=["Testing"])
async def generate_anomaly():
    """Generate a simulated anomalous transaction for testing."""
    if not tracker:
        raise HTTPException(status_code=503, detail="Tracker not initialized")
    
    # Create a simulated transaction that will be flagged as anomalous
    txid = f"simulated_anomaly_{uuid.uuid4().hex[:8]}"
    
    # Add to database
    db.add_transaction(txid, 'pending')
    
    # Create a fake tx_details that would trigger the anomaly detector
    tx_details = {
        'txid': txid,
        'vin': [{'dummy': 'input'} for _ in range(100)],  # Unusually high number of inputs
        'vout': [
            {
                'value': 1000.0,  # Unusually high value
                'n': 0,
                'scriptPubKey': {
                    'addresses': ['EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB']
                }
            }
        ]
    }
    
    # Manually check with anomaly detector
    anomaly_result = tracker.anomaly_detector.check_transaction(tx_details)
    
    # Add the transaction output to the database
    db.add_tx_output(
        txid=txid,
        address='EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB',
        asset_name='EVR',
        amount=1000.0,
        vout=0
    )
    
    return {
        "status": "success",
        "message": "Generated anomalous transaction",
        "txid": txid,
        "anomaly_details": anomaly_result
    }

if __name__ == "__main__":
    uvicorn.run("api_example:app", host="0.0.0.0", port=8080, reload=True) 