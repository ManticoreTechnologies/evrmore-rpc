#!/usr/bin/env python3

import sqlite3
import os
import uuid
from datetime import datetime

# Remove the database if it exists
if os.path.exists("balance_tracker.db"):
    os.remove("balance_tracker.db")
    print("Removed existing database")

# Create a new database
conn = sqlite3.connect("balance_tracker.db")
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Create schema
schema = """
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
"""

cursor.executescript(schema)
conn.commit()
print("Schema created successfully")

# Add test addresses
exchange_addr = "EgGxvVkRC5gTL43BiCJyoyh18qpXryGbvB"
user_addr = "EPWqFhGa44qXRB4sHbj2MnGsLTRmULirJ7"

cursor.execute("INSERT INTO addresses (address, label) VALUES (?, ?)", (exchange_addr, "Exchange Wallet"))
cursor.execute("INSERT INTO addresses (address, label) VALUES (?, ?)", (user_addr, "User Wallet"))
conn.commit()
print(f"Added addresses: Exchange={exchange_addr}, User={user_addr}")

# Add test assets
asset = "TESTASSET"
amount = 10.0
cursor.execute("""
INSERT INTO assets (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", (asset, "TESTER", amount, 0, True, False, "", 8))
# Also add EVR as an asset
cursor.execute("""
INSERT INTO assets (asset_name, issuer, total_supply, units, reissuable, has_ipfs, ipfs_hash, divisibility, last_updated)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
""", ("EVR", "SYSTEM", 21000000.0, 0, False, False, "", 8))
conn.commit()
print(f"Added assets: {asset} and EVR")

# Add test balances
cursor.execute("""
INSERT INTO balances (address, asset_name, balance, last_updated)
VALUES (?, ?, ?, datetime('now'))
""", (exchange_addr, asset, amount))
# Add EVR balances
cursor.execute("""
INSERT INTO balances (address, asset_name, balance, last_updated)
VALUES (?, ?, ?, datetime('now'))
""", (exchange_addr, "EVR", 100.0))
cursor.execute("""
INSERT INTO balances (address, asset_name, balance, last_updated)
VALUES (?, ?, ?, datetime('now'))
""", (user_addr, "EVR", 100.0))
conn.commit()
print(f"Added balances: {exchange_addr}={amount} {asset}, {exchange_addr}=100 EVR, {user_addr}=100 EVR")

# Create test order
order_id = str(uuid.uuid4())
price = 0.5
total_cost = amount * price
cursor.execute("""
INSERT INTO orders (order_id, seller_address, buyer_address, asset_name, amount, price, total_cost, status)
VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
""", (order_id, exchange_addr, user_addr, asset, amount, price, total_cost))
conn.commit()
print(f"Created order: {order_id} for {amount} {asset} at {price} EVR each (total: {total_cost} EVR)")

# Simulate payment
payment_txid = str(uuid.uuid4())
cursor.execute("""
INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
VALUES (?, ?, ?, datetime('now'), ?, ?)
""", (payment_txid, "0000000000000000000000000000000000000000000000000000000000000000", 12345, 6, 'confirmed'))
conn.commit()
print(f"Created payment transaction: {payment_txid}")

# Update order with payment
cursor.execute("""
UPDATE orders SET status = 'processing', payment_txid = ? WHERE order_id = ?
""", (payment_txid, order_id))
conn.commit()
print(f"Updated order {order_id} with payment")

# Simulate delivery
delivery_txid = str(uuid.uuid4())
cursor.execute("""
INSERT INTO transactions (txid, block_hash, block_height, timestamp, confirmations, status)
VALUES (?, ?, ?, datetime('now'), ?, ?)
""", (delivery_txid, "0000000000000000000000000000000000000000000000000000000000000000", 12346, 6, 'confirmed'))
conn.commit()
print(f"Created delivery transaction: {delivery_txid}")

# Update order with delivery
cursor.execute("""
UPDATE orders SET status = 'completed', delivery_txid = ? WHERE order_id = ?
""", (delivery_txid, order_id))
conn.commit()
print(f"Updated order {order_id} with delivery")

# Update balances
# Subtract asset from seller
cursor.execute("""
UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?
""", (amount, exchange_addr, asset))
# Add asset to buyer
cursor.execute("""
INSERT OR REPLACE INTO balances (address, asset_name, balance, last_updated)
VALUES (?, ?, ?, datetime('now'))
""", (user_addr, asset, amount))
# Subtract EVR from buyer
cursor.execute("""
UPDATE balances SET balance = balance - ? WHERE address = ? AND asset_name = ?
""", (total_cost, user_addr, "EVR"))
# Add EVR to seller
cursor.execute("""
UPDATE balances SET balance = balance + ? WHERE address = ? AND asset_name = ?
""", (total_cost, exchange_addr, "EVR"))

conn.commit()
print(f"Updated balances for completed order")

# Close connection
conn.close()
print("Test database initialized successfully") 