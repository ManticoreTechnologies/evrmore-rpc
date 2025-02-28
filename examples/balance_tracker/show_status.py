#!/usr/bin/env python3
"""
Show Balance Tracker Status

This script displays the current status of all orders and balances in the database.
Useful for checking the state after simulating payments and order completions.
"""

import sqlite3
from rich.console import Console
from rich.table import Table

console = Console()

def show_orders():
    """Display all orders in the database."""
    conn = sqlite3.connect('balance_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all orders
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    
    # Display results
    table = Table(title="Orders")
    table.add_column("Order ID", style="cyan")
    table.add_column("Asset", style="green")
    table.add_column("Amount", style="yellow")
    table.add_column("Price", style="yellow")
    table.add_column("Total", style="yellow")
    table.add_column("Status", style="red")
    table.add_column("Created At")
    table.add_column("Payment TX")
    table.add_column("Delivery TX")
    
    for order in orders:
        # Truncate long IDs
        order_id = order['order_id'][:10] + "..." if order['order_id'] else ""
        payment_tx = order['payment_txid'][:10] + "..." if order['payment_txid'] else ""
        delivery_tx = order['delivery_txid'][:10] + "..." if order['delivery_txid'] else ""
        
        table.add_row(
            order_id,
            order['asset_name'],
            f"{order['amount']:.6f}",
            f"{order['price']:.6f}",
            f"{order['total_cost']:.6f}",
            order['status'],
            order['created_at'],
            payment_tx,
            delivery_tx
        )
    
    console.print(table)
    conn.close()

def show_balances():
    """Display all balances in the database."""
    conn = sqlite3.connect('balance_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all addresses
    cursor.execute("""
        SELECT a.address, a.label, b.asset_name, b.balance 
        FROM addresses a
        LEFT JOIN balances b ON a.address = b.address
        ORDER BY a.address, b.asset_name
    """)
    balances = cursor.fetchall()
    
    # Display results
    table = Table(title="Balances")
    table.add_column("Address", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Asset", style="yellow")
    table.add_column("Balance", style="red")
    
    for balance in balances:
        # Truncate long addresses
        address = balance['address'][:10] + "..." if balance['address'] else ""
        
        table.add_row(
            address,
            balance['label'] or "",
            balance['asset_name'] or "",
            f"{balance['balance']:.6f}" if balance['balance'] is not None else "0.000000"
        )
    
    console.print(table)
    conn.close()

def show_transactions():
    """Display all transactions in the database."""
    conn = sqlite3.connect('balance_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all transactions
    cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
    transactions = cursor.fetchall()
    
    # Display results
    table = Table(title="Transactions")
    table.add_column("TXID", style="cyan")
    table.add_column("Block Hash", style="green")
    table.add_column("Block Height", style="yellow")
    table.add_column("Timestamp", style="yellow")
    table.add_column("Confirmations", style="red")
    table.add_column("Status", style="magenta")
    
    for tx in transactions:
        # Truncate long hashes
        txid = tx['txid'][:10] + "..." if tx['txid'] else ""
        block_hash = tx['block_hash'][:10] + "..." if tx['block_hash'] else ""
        
        table.add_row(
            txid,
            block_hash,
            str(tx['block_height']) if tx['block_height'] else "",
            tx['timestamp'] or "",
            str(tx['confirmations']) if tx['confirmations'] is not None else "0",
            tx['status'] or ""
        )
    
    console.print(table)
    conn.close()

if __name__ == "__main__":
    console.print("\n[bold cyan]Balance Tracker Status[/]\n")
    
    console.print("[bold yellow]Orders:[/]")
    show_orders()
    
    console.print("\n[bold yellow]Balances:[/]")
    show_balances()
    
    console.print("\n[bold yellow]Transactions:[/]")
    show_transactions()
    
    console.print("\n[bold green]Status check complete![/]") 