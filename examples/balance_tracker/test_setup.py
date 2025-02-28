#!/usr/bin/env python3
"""
Test Setup for Balance Tracker

This script sets up test data in the balance tracker database, including:
1. Creating addresses to monitor
2. Adding test assets
3. Creating test orders
4. Optionally confirming orders with simulated transactions

It provides a clean way to set up test data for demo purposes.
"""

import sqlite3
import uuid
import datetime
import argparse
from decimal import Decimal

def ensure_schema():
    """Ensure the database has the correct schema."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    # Create addresses table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS addresses (
        address TEXT PRIMARY KEY,
        label TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create assets table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_name TEXT PRIMARY KEY,
        total_supply REAL,
        units INTEGER,
        reissuable BOOLEAN,
        has_ipfs BOOLEAN,
        ipfs_hash TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create balances table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        address TEXT,
        asset_name TEXT,
        balance REAL NOT NULL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (address, asset_name),
        FOREIGN KEY (address) REFERENCES addresses (address),
        FOREIGN KEY (asset_name) REFERENCES assets (asset_name)
    )
    """)
    
    # Create transactions table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txid TEXT PRIMARY KEY,
        block_hash TEXT,
        block_height INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmations INTEGER DEFAULT 0,
        status TEXT CHECK (status IN ('pending', 'confirming', 'confirmed', 'failed'))
    )
    """)
    
    # Create tx_outputs table if it doesn't exist
    cursor.execute("""
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
    )
    """)
    
    # Create orders table if it doesn't exist
    cursor.execute("""
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
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_outputs_txid ON tx_outputs (txid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_outputs_address ON tx_outputs (address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_outputs_asset ON tx_outputs (asset_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_balances_address ON balances (address)")
    
    conn.commit()
    conn.close()

def add_address(address, label):
    """Add an address to monitor."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO addresses (address, label) VALUES (?, ?)",
        (address, label)
    )
    
    conn.commit()
    conn.close()
    print(f"Added address: {address} ({label})")

def add_asset(asset_name, total_supply=1000, divisibility=8, has_ipfs=False, ipfs_hash=""):
    """Add an asset to the database."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT OR IGNORE INTO assets (asset_name, total_supply, units, reissuable, has_ipfs, ipfs_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (asset_name, float(total_supply), divisibility, True, has_ipfs, ipfs_hash)
    )
    
    conn.commit()
    conn.close()
    print(f"Added asset: {asset_name} (supply: {total_supply})")

def add_balance(address, asset_name, amount):
    """Add an asset balance to an address."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    print(f"Added {amount} {asset_name} to {address}")

def create_test_order(seller, buyer, asset, amount, price):
    """Create a test order."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Create the order in pending status
    cursor.execute(
        """
        INSERT INTO orders (order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (order_id, seller, buyer, asset, float(amount), float(price), float(amount) * float(price), "pending")
    )
    
    conn.commit()
    conn.close()
    print(f"Created test order: {order_id} for {amount} {asset} at {price} EVR each ({amount * price} EVR total)")
    return order_id

def simulate_payment(order_id):
    """Simulate a payment transaction for an order."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Get the pending order
        cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'pending'", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            print(f"No pending order found with ID {order_id}")
            return None
        
        # Extract order details
        seller = order[1]  # seller_address
        buyer = order[2]   # buyer_address
        asset = order[3]   # asset_name
        amount = order[4]  # amount
        price = order[5]   # price
        total_cost = order[6]  # total_cost
        
        # Create a simulated transaction ID
        txid = str(uuid.uuid4())
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the transaction with status 'confirmed'
        cursor.execute(
            "INSERT INTO transactions (txid, status, timestamp) VALUES (?, ?, ?)",
            (txid, 'confirmed', current_time)
        )
        
        # Update the transaction with block details
        block_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        block_height = 12345
        confirmations = 6
        
        cursor.execute(
            "UPDATE transactions SET block_hash = ?, block_height = ?, confirmations = ? WHERE txid = ?",
            (block_hash, block_height, confirmations, txid)
        )
        
        # Update the order status to processing and set payment_txid
        cursor.execute(
            "UPDATE orders SET status = 'processing', payment_txid = ?, updated_at = ? WHERE order_id = ?",
            (txid, current_time, order_id)
        )
        
        # Update balances to reflect the payment
        # Add EVR to seller's balance, subtract from buyer
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (seller, "EVR", 0.0)
        )
        cursor.execute(
            "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?",
            (float(total_cost), seller, "EVR")
        )
        
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (buyer, "EVR", float(total_cost) * 2)  # Ensure buyer has enough balance
        )
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
            (float(total_cost), buyer, "EVR")
        )
        
        # Record transaction outputs
        cursor.execute(
            "INSERT INTO tx_outputs (txid, address, asset_name, amount, vout) VALUES (?, ?, ?, ?, ?)",
            (txid, seller, "EVR", float(total_cost), 0)
        )
        
        conn.commit()
        print(f"Simulated payment for order {order_id} with transaction {txid}")
        print(f"Order status updated to 'processing'")
        print(f"Added {total_cost} EVR to {seller}")
        
        return order_id
        
    except Exception as e:
        print(f"Error simulating payment: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def simulate_delivery(order_id):
    """Simulate asset delivery for an order."""
    conn = sqlite3.connect('balance_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Get the processing order
        cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'processing'", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            print(f"No processing order found with ID {order_id}")
            return
        
        # Extract order details
        seller = order[1]  # seller_address
        buyer = order[2]   # buyer_address
        asset = order[3]   # asset_name
        amount = order[4]  # amount
        
        # Create a simulated transaction ID for delivery
        txid = str(uuid.uuid4())
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the transaction with status 'confirmed'
        cursor.execute(
            "INSERT INTO transactions (txid, status, timestamp) VALUES (?, ?, ?)",
            (txid, 'confirmed', current_time)
        )
        
        # Update the transaction with block details
        block_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        block_height = 12346
        confirmations = 6
        
        cursor.execute(
            "UPDATE transactions SET block_hash = ?, block_height = ?, confirmations = ? WHERE txid = ?",
            (block_hash, block_height, confirmations, txid)
        )
        
        # Update the order status to completed and set delivery_txid
        cursor.execute(
            "UPDATE orders SET status = 'completed', delivery_txid = ?, updated_at = ? WHERE order_id = ?",
            (txid, current_time, order_id)
        )
        
        # Update balances to reflect the asset transfer
        # Subtract from seller, add to buyer
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
            (float(amount), seller, asset)
        )
        
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (buyer, asset, 0.0)
        )
        cursor.execute(
            "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?",
            (float(amount), buyer, asset)
        )
        
        # Record transaction outputs
        cursor.execute(
            "INSERT INTO tx_outputs (txid, address, asset_name, amount, vout) VALUES (?, ?, ?, ?, ?)",
            (txid, buyer, asset, float(amount), 0)
        )
        
        conn.commit()
        print(f"Simulated delivery for order {order_id} with transaction {txid}")
        print(f"Order status updated to 'completed'")
        print(f"Transferred {amount} {asset} from {seller} to {buyer}")
        
    except Exception as e:
        print(f"Error simulating delivery: {e}")
        conn.rollback()
    finally:
        conn.close()

def setup_test_data(auto_confirm=False):
    """Set up basic test data."""
    # Ensure the database schema exists
    ensure_schema()
    
    # Add test addresses
    exchange_addr = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"
    user_addr = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"
    
    add_address(exchange_addr, "Exchange Wallet")
    add_address(user_addr, "User Wallet")
    
    # Add test assets
    add_asset("TESTASSET", 1000)
    add_asset("NFT1", 1, 0)
    add_asset("NFT2", 1, 0)
    
    # Add initial balances
    add_balance(exchange_addr, "TESTASSET", 100)
    add_balance(exchange_addr, "NFT1", 1)
    add_balance(exchange_addr, "NFT2", 1)
    add_balance(user_addr, "EVR", 100)
    
    # Create test orders
    order1 = create_test_order(exchange_addr, user_addr, "TESTASSET", 10, 0.5)
    order2 = create_test_order(exchange_addr, user_addr, "NFT1", 1, 5)
    
    # Auto-confirm if requested
    if auto_confirm:
        print("\nAuto-confirming orders:")
        # Simulate payment and delivery for the first order
        processed_order = simulate_payment(order1)
        if processed_order:
            simulate_delivery(processed_order)
        
        # Simulate payment for the second order but leave it in processing
        simulate_payment(order2)
    
    print("\nTest data setup complete!")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up test data for the Balance Tracker")
    parser.add_argument("--auto-confirm", action="store_true", help="Automatically confirm orders")
    args = parser.parse_args()
    
    # Set up test data
    setup_test_data(args.auto_confirm) 