#!/usr/bin/env python3
"""
Simulate Payment for Test Order

This script simulates a payment transaction for test orders in the balance tracker database.
It creates a fake transaction ID and marks the order as confirmed.
"""

import sqlite3
import uuid
import datetime
from decimal import Decimal
import sys

# Function to simulate a payment transaction
def simulate_payment(order_id=None):
    """
    Simulate a payment transaction for a test order.
    
    Args:
        order_id: Optional order ID to update. If None, update the first pending order.
    """
    # Connect to the database
    conn = sqlite3.connect('balance_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get the pending order
        if order_id:
            cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'pending'", (order_id,))
        else:
            cursor.execute("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at LIMIT 1")
        
        order = cursor.fetchone()
        if not order:
            print("No pending orders found")
            return
        
        # Print order details
        order_id = order['order_id']
        seller = order['seller_address']
        buyer = order['buyer_address']
        asset = order['asset_name']
        amount = order['amount']
        price = order['price']
        
        print(f"Found pending order: {order_id}")
        print(f"Asset: {asset}, Amount: {amount}, Price: {price}")
        print(f"Seller: {seller}")
        print(f"Buyer: {buyer}")
        
        # Create a simulated transaction ID
        txid = str(uuid.uuid4())
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the transaction with the correct column names and status
        cursor.execute(
            "INSERT INTO transactions (txid, status, timestamp) VALUES (?, ?, ?)",
            (txid, 'confirmed', current_time)
        )
        
        # Update the transaction with block details (simulating confirmation)
        block_hash = "000000000000000000000000000000000000000000000000000000000000000"
        block_height = 12345
        confirmations = 6
        
        cursor.execute(
            "UPDATE transactions SET block_hash = ?, block_height = ?, confirmations = ? WHERE txid = ?",
            (block_hash, block_height, confirmations, txid)
        )
        
        # Update the order status and set payment_txid - using the correct status 'processing'
        cursor.execute(
            "UPDATE orders SET status = 'processing', payment_txid = ?, updated_at = ? WHERE order_id = ?",
            (txid, current_time, order_id)
        )
        
        # Update balances to reflect the payment
        # First, deduct the payment amount from buyer's EVR balance
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (buyer, "EVR", 0.0)
        )
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
            (float(price) * float(amount), buyer, "EVR")
        )
        
        # Add the payment amount to seller's EVR balance
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (seller, "EVR", 0.0)
        )
        cursor.execute(
            "UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?",
            (float(price) * float(amount), seller, "EVR")
        )
        
        # Record transaction outputs
        cursor.execute(
            "INSERT INTO tx_outputs (txid, address, asset_name, amount, vout) VALUES (?, ?, ?, ?, ?)",
            (txid, seller, "EVR", float(price) * float(amount), 0)
        )
        
        # Commit the changes
        conn.commit()
        
        print(f"Payment simulated with transaction ID: {txid}")
        print(f"Order status updated to 'processing'")
        print(f"Added {float(price) * float(amount)} EVR to seller's balance")
        
        # Return the order ID for use in the next step
        return order_id
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def simulate_delivery(order_id=None):
    """
    Simulate asset delivery for a processing order.
    
    Args:
        order_id: Optional order ID to update. If None, update the first processing order.
    """
    # Connect to the database
    conn = sqlite3.connect('balance_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get the processing order (not confirmed)
        if order_id:
            cursor.execute("SELECT * FROM orders WHERE order_id = ? AND status = 'processing'", (order_id,))
        else:
            cursor.execute("SELECT * FROM orders WHERE status = 'processing' ORDER BY created_at LIMIT 1")
        
        order = cursor.fetchone()
        if not order:
            print("No processing orders found")
            return
        
        # Print order details
        order_id = order['order_id']
        seller = order['seller_address']
        buyer = order['buyer_address']
        asset = order['asset_name']
        amount = order['amount']
        
        print(f"Found processing order: {order_id}")
        print(f"Asset: {asset}, Amount: {amount}")
        print(f"Seller: {seller}")
        print(f"Buyer: {buyer}")
        
        # Create a simulated transaction ID for delivery
        txid = str(uuid.uuid4())
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the transaction with the correct column names
        cursor.execute(
            "INSERT INTO transactions (txid, status, timestamp) VALUES (?, ?, ?)",
            (txid, 'confirmed', current_time)
        )
        
        # Update the transaction with block details (simulating confirmation)
        block_hash = "000000000000000000000000000000000000000000000000000000000000000"
        block_height = 12346
        confirmations = 6
        
        cursor.execute(
            "UPDATE transactions SET block_hash = ?, block_height = ?, confirmations = ? WHERE txid = ?",
            (block_hash, block_height, confirmations, txid)
        )
        
        # Update the order status and set delivery_txid - using the correct status 'completed'
        cursor.execute(
            "UPDATE orders SET status = 'completed', delivery_txid = ?, updated_at = ? WHERE order_id = ?",
            (txid, current_time, order_id)
        )
        
        # Update balances to reflect the asset transfer
        # First, deduct the asset from seller's balance
        cursor.execute(
            "INSERT OR IGNORE INTO balances (address, asset_name, balance) VALUES (?, ?, ?)",
            (seller, asset, 0.0)
        )
        cursor.execute(
            "UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?",
            (float(amount), seller, asset)
        )
        
        # Add the asset to buyer's balance
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
        
        # Commit the changes
        conn.commit()
        
        print(f"Delivery simulated with transaction ID: {txid}")
        print(f"Order status updated to 'completed'")
        print(f"Transferred {amount} {asset} from seller to buyer")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Check if an order ID was provided
    order_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Perform both payment and delivery simulation
    print("Simulating payment...")
    processed_order_id = simulate_payment(order_id)
    
    if processed_order_id:
        print("\nSimulating delivery...")
        simulate_delivery(processed_order_id)
    else:
        print("\nSkipping delivery simulation since payment simulation failed.")
    
    print("\nSimulation complete!") 