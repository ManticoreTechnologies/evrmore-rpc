#!/usr/bin/env python3
"""
Real-time Asset Swap Platform

This example demonstrates how to create an asset swap platform with real-time updates
using the evrmore-rpc library's WebSockets functionality.

It extends the simple_swap.py example by adding:
1. Real-time notifications when new assets are created
2. Real-time updates when assets are transferred
3. Automatic offer matching
"""

import asyncio
import os
import json
import uuid
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from decimal import Decimal
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.status import Status

# Import the evrmore-rpc library
# As a new developer, I'm exploring more advanced features
from evrmore_rpc import EvrmoreAsyncRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

# Import WebSocket client if available
try:
    from evrmore_rpc.websockets.client import EvrmoreWebSocketClient
    from evrmore_rpc.websockets.models import WebSocketMessage
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    print("WebSockets support not available. Install with: pip install evrmore-rpc[websockets]")

# Create a console for pretty output
console = Console()

# Define the swap offer data structure
class SwapOffer:
    def __init__(self, 
                 offer_id: str,
                 owner_address: str,
                 asset_offered: str, 
                 amount_offered: Decimal,
                 asset_wanted: str,
                 amount_wanted: Decimal,
                 status: str = "open",
                 taker_address: Optional[str] = None,
                 txid_offer: Optional[str] = None,
                 txid_payment: Optional[str] = None):
        self.offer_id = offer_id
        self.owner_address = owner_address
        self.asset_offered = asset_offered
        self.amount_offered = amount_offered
        self.asset_wanted = asset_wanted
        self.amount_wanted = amount_wanted
        self.status = status
        self.taker_address = taker_address
        self.txid_offer = txid_offer
        self.txid_payment = txid_payment
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the offer to a dictionary for storage."""
        return {
            "offer_id": self.offer_id,
            "owner_address": self.owner_address,
            "asset_offered": self.asset_offered,
            "amount_offered": str(self.amount_offered),
            "asset_wanted": self.asset_wanted,
            "amount_wanted": str(self.amount_wanted),
            "status": self.status,
            "taker_address": self.taker_address,
            "txid_offer": self.txid_offer,
            "txid_payment": self.txid_payment,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SwapOffer':
        """Create an offer from a dictionary."""
        return cls(
            offer_id=data["offer_id"],
            owner_address=data["owner_address"],
            asset_offered=data["asset_offered"],
            amount_offered=Decimal(data["amount_offered"]),
            asset_wanted=data["asset_wanted"],
            amount_wanted=Decimal(data["amount_wanted"]),
            status=data["status"],
            taker_address=data.get("taker_address"),
            txid_offer=data.get("txid_offer"),
            txid_payment=data.get("txid_payment")
        )


class AssetSwapPlatform:
    """
    A real-time asset swap platform using the evrmore-rpc library.
    """
    
    def __init__(self, data_file: str = "swap_offers.json"):
        """Initialize the asset swap platform."""
        self.data_file = data_file
        self.offers: List[SwapOffer] = []
        self.monitored_assets: Set[str] = set()
        self.recent_transactions: List[Dict[str, Any]] = []
        self.recent_blocks: List[Dict[str, Any]] = []
        self.my_address = "EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your address
        self.auto_complete_swaps = False
        
        # Load existing offers if the data file exists
        self._load_offers()
        
    async def initialize(self):
        """Initialize the platform."""
        try:
            # Initialize the RPC client
            self.rpc_client = EvrmoreAsyncRPCClient()
            await self.rpc_client.initialize()
            
            # Initialize the ZMQ client
            self.zmq_client = EvrmoreZMQClient()
            self.zmq_client.on_transaction(self.handle_transaction)
            self.zmq_client.on_block(self.handle_block)
            
            # Initialize the WebSocket client if available
            if HAS_WEBSOCKETS:
                self.ws_client = EvrmoreWebSocketClient()
                try:
                    await self.ws_client.connect()
                    await self.ws_client.subscribe("blocks")
                    await self.ws_client.subscribe("transactions")
                    console.print("[green]Connected to WebSocket server[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not connect to WebSocket server: {e}[/yellow]")
                    console.print("[yellow]Continuing without WebSocket support[/yellow]")
                    self.ws_client = None
            else:
                self.ws_client = None
                console.print("[yellow]WebSocket support not available. Some real-time features will be limited.[/yellow]")
            
            # Load existing offers
            self._load_offers()
            
            console.print("[green]Platform initialized successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error initializing platform: {e}[/red]")
            raise
    
    async def start(self):
        """Start the platform."""
        try:
            # Start the ZMQ client
            # Create a task for the ZMQ client to run in the background
            self.zmq_task = asyncio.create_task(self.zmq_client.start())
            console.print("[green]ZMQ client started[/green]")
            
            # Start listening for WebSocket messages if available
            if self.ws_client:
                asyncio.create_task(self.listen_for_websocket_messages())
                console.print("[green]WebSocket listener started[/green]")
            
            # Get initial list of assets to monitor
            assets = await self.list_my_assets()
            self.monitored_assets = set(assets.keys())
            console.print(f"[green]Monitoring {len(self.monitored_assets)} assets[/green]")
            
            return self
        except Exception as e:
            console.print(f"[red]Error starting platform: {e}[/red]")
            raise
    
    async def stop(self):
        """Stop the platform."""
        try:
            # Stop the ZMQ client
            if hasattr(self, 'zmq_client') and self.zmq_client:
                await self.zmq_client.stop()
                if hasattr(self, 'zmq_task') and self.zmq_task:
                    self.zmq_task.cancel()
                    try:
                        await self.zmq_task
                    except asyncio.CancelledError:
                        pass
                console.print("[green]ZMQ client stopped[/green]")
            
            # Disconnect from WebSocket server if connected
            if hasattr(self, 'ws_client') and self.ws_client:
                await self.ws_client.disconnect()
                console.print("[green]WebSocket client disconnected[/green]")
            
            console.print("[green]Platform stopped successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error stopping platform: {e}[/red]")
            raise
    
    def _load_offers(self) -> None:
        """Load offers from the data file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.offers = [SwapOffer.from_dict(offer) for offer in data]
                console.print(f"[green]Loaded {len(self.offers)} offers from {self.data_file}[/green]")
            except Exception as e:
                console.print(f"[red]Error loading offers: {e}[/red]")
                self.offers = []
    
    def _save_offers(self) -> None:
        """Save offers to the data file."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([offer.to_dict() for offer in self.offers], f, indent=2)
            console.print(f"[green]Saved {len(self.offers)} offers to {self.data_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving offers: {e}[/red]")
    
    async def listen_for_websocket_messages(self):
        """Listen for WebSocket messages."""
        if not self.ws_client:
            console.print("[yellow]WebSocket client not available. Skipping WebSocket listener.[/yellow]")
            return
            
        try:
            console.print("[green]Listening for WebSocket messages...[/green]")
            async for message in self.ws_client:
                if message.type == "block":
                    console.print(f"[blue]New block via WebSocket: {message.data.hash[:8]}...[/blue]")
                    # Process block data if needed
                    
                elif message.type == "transaction":
                    console.print(f"[blue]New transaction via WebSocket: {message.data.txid[:8]}...[/blue]")
                    # Process transaction data if needed
                    
                elif message.type == "error":
                    console.print(f"[red]WebSocket error: {message.data.message}[/red]")
        except Exception as e:
            console.print(f"[red]Error in WebSocket listener: {e}[/red]")
            # Try to reconnect
            await asyncio.sleep(5)
            asyncio.create_task(self.listen_for_websocket_messages())
    
    async def handle_transaction(self, notification: ZMQNotification) -> None:
        """Handle transaction notifications from ZMQ."""
        try:
            # Handle differently based on notification topic
            if notification.topic == ZMQTopic.HASH_TX:
                # For HASH_TX, the notification.hex is the transaction ID
                txid = notification.hex
                console.print(f"[cyan]ZMQ Transaction (hash): {txid}[/cyan]")
                
                # Get transaction details
                tx = await self.rpc_client.getrawtransaction(txid, True)
                
                # Add to recent transactions
                self.recent_transactions.append({
                    "txid": txid,
                    "time": datetime.now().isoformat(),
                    "inputs": len(tx.get("vin", [])),
                    "outputs": len(tx.get("vout", []))
                })
                
                # Keep only the last 10 transactions
                if len(self.recent_transactions) > 10:
                    self.recent_transactions.pop(0)
                    
                # Check if this transaction affects any of our monitored assets
                await self.check_transaction_for_assets(tx)
                
            elif notification.topic == ZMQTopic.RAW_TX:
                # For RAW_TX, we need to compute the txid from the raw transaction
                # This is a simplified approach - in production you'd use proper tx parsing
                console.print(f"[cyan]ZMQ Transaction (raw received)[/cyan]")
                
                # Skip processing raw transactions for now
                # In a production environment, you would parse the raw transaction
                # and extract the txid and other details
                
        except Exception as e:
            console.print(f"[red]Error handling transaction: {e}[/red]")
    
    async def handle_block(self, notification: ZMQNotification) -> None:
        """Handle block notifications from ZMQ."""
        try:
            block_hash = notification.hex
            console.print(f"[cyan]ZMQ Block: {block_hash}[/cyan]")
            
            # Get block details
            block = await self.rpc_client.getblock(block_hash)
            
            # Add to recent blocks
            self.recent_blocks.append({
                "hash": block_hash,
                "height": block.get("height", 0),
                "time": block.get("time", 0),
                "tx_count": len(block.get("tx", []))
            })
            
            # Keep only the last 5 blocks
            if len(self.recent_blocks) > 5:
                self.recent_blocks.pop(0)
                
            # Check for matching offers after a new block
            await self.check_for_matching_offers()
            
        except Exception as e:
            console.print(f"[red]Error handling block: {e}[/red]")
    
    async def check_transaction_for_assets(self, tx_data: Any) -> None:
        """Check if a transaction affects any of our monitored assets."""
        try:
            # Get detailed transaction information
            tx_details = await self.rpc_client.getrawtransaction(tx_data.txid, True)
            
            # Check if this transaction is related to any of our swap offers
            for offer in self.offers:
                # Check if this is a payment transaction for an offer
                if offer.status == "open" and offer.asset_wanted in self.monitored_assets:
                    # Check outputs for the wanted asset being sent to the offer owner
                    for vout in tx_details.get("vout", []):
                        # Check if this output is an asset transfer
                        if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                            asset_info = vout["scriptPubKey"]["asset"]
                            asset_name = asset_info.get("name", "")
                            asset_amount = Decimal(asset_info.get("amount", 0))
                            
                            # Check if the asset and amount match what's wanted in the offer
                            if (asset_name == offer.asset_wanted and 
                                asset_amount >= offer.amount_wanted):
                                
                                # Check if the recipient is the offer owner
                                addresses = vout.get("scriptPubKey", {}).get("addresses", [])
                                if offer.owner_address in addresses:
                                    console.print(f"[green]Detected payment for offer {offer.offer_id[:8]}...[/green]")
                                    console.print(f"[green]Transaction {tx_data.txid[:8]}... sends {asset_amount} {asset_name} to {offer.owner_address[:8]}...[/green]")
                                    
                                    # Update the offer with the payment transaction
                                    offer.txid_payment = tx_data.txid
                                    offer.status = "payment_received"
                                    offer.updated_at = datetime.now().isoformat()
                                    self._save_offers()
                                    
                                    # Automatically complete the swap if configured
                                    if hasattr(self, "auto_complete_swaps") and self.auto_complete_swaps:
                                        asyncio.create_task(self.complete_swap_after_payment(offer))
                
                # Check if this is an asset transfer transaction for an offer
                elif offer.status == "payment_received" and offer.txid_payment and offer.asset_offered in self.monitored_assets:
                    # Check if this transaction completes a swap where payment was already received
                    for vout in tx_details.get("vout", []):
                        if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                            asset_info = vout["scriptPubKey"]["asset"]
                            asset_name = asset_info.get("name", "")
                            asset_amount = Decimal(asset_info.get("amount", 0))
                            
                            # Check if the asset and amount match what's offered in the offer
                            if (asset_name == offer.asset_offered and 
                                asset_amount >= offer.amount_offered):
                                
                                # Check if the recipient is the taker
                                addresses = vout.get("scriptPubKey", {}).get("addresses", [])
                                if offer.taker_address and offer.taker_address in addresses:
                                    console.print(f"[green]Detected asset transfer for offer {offer.offer_id[:8]}...[/green]")
                                    console.print(f"[green]Transaction {tx_data.txid[:8]}... sends {asset_amount} {asset_name} to {offer.taker_address[:8]}...[/green]")
                                    
                                    # Update the offer with the asset transfer transaction
                                    offer.txid_offer = tx_data.txid
                                    offer.status = "completed"
                                    offer.updated_at = datetime.now().isoformat()
                                    self._save_offers()
                                    
                                    console.print(f"[bold green]Swap offer {offer.offer_id[:8]}... completed successfully![/bold green]")
        except Exception as e:
            console.print(f"[red]Error checking transaction for assets: {e}[/red]")
    
    async def check_for_matching_offers(self) -> None:
        """Check for matching offers after a new block."""
        try:
            # Find offers that can be matched
            open_offers = [offer for offer in self.offers if offer.status == "open"]
            
            # Group offers by asset pairs
            asset_pairs = {}
            for offer in open_offers:
                pair_key = f"{offer.asset_offered}:{offer.asset_wanted}"
                reverse_key = f"{offer.asset_wanted}:{offer.asset_offered}"
                
                if pair_key not in asset_pairs:
                    asset_pairs[pair_key] = []
                asset_pairs[pair_key].append(offer)
                
                # Check for matching offers (where asset_offered and asset_wanted are reversed)
                if reverse_key in asset_pairs:
                    for potential_match in asset_pairs[reverse_key]:
                        # Skip if either offer is not open
                        if offer.status != "open" or potential_match.status != "open":
                            continue
                            
                        # Check if the amounts match or are compatible
                        if (offer.amount_offered >= potential_match.amount_wanted and
                            offer.amount_wanted <= potential_match.amount_offered):
                            
                            console.print(f"[bold green]Found matching offers![/bold green]")
                            console.print(f"Offer 1: {offer.offer_id[:8]}... - {offer.amount_offered} {offer.asset_offered} for {offer.amount_wanted} {offer.asset_wanted}")
                            console.print(f"Offer 2: {potential_match.offer_id[:8]}... - {potential_match.amount_offered} {potential_match.asset_offered} for {potential_match.amount_wanted} {potential_match.asset_wanted}")
                            
                            # Notify users about the match
                            # In a real application, you would notify the users and let them decide
                            # For this example, we'll just log the match
        except Exception as e:
            console.print(f"[red]Error checking for matching offers: {e}[/red]")
    
    async def list_my_assets(self) -> Dict[str, Decimal]:
        """List assets owned by the specified address."""
        try:
            # Get assets owned by the address
            assets = await self.rpc_client.listmyassets()
            
            # Display the assets
            console.print("\n[bold blue]Your Assets:[/bold blue]")
            
            if not assets:
                console.print("[yellow]No assets found.[/yellow]")
                return {}
            
            asset_table = Table(show_header=True)
            asset_table.add_column("Asset Name", style="cyan")
            asset_table.add_column("Balance", style="green")
            
            for name, balance in assets.items():
                asset_table.add_row(name, str(balance))
                # Add to monitored assets
                self.monitored_assets.add(name)
            
            console.print(asset_table)
            return assets
            
        except Exception as e:
            console.print(f"[red]Error listing assets: {e}[/red]")
            return {}
    
    async def create_swap_offer(self, 
                              owner_address: str,
                              asset_offered: str, 
                              amount_offered: Decimal,
                              asset_wanted: str,
                              amount_wanted: Decimal) -> Optional[SwapOffer]:
        """Create a new swap offer."""
        try:
            # Check if the user has enough of the offered asset
            assets = await self.rpc_client.listmyassets()
            
            if asset_offered not in assets:
                console.print(f"[red]You don't own the asset {asset_offered}[/red]")
                return None
            
            if assets[asset_offered] < amount_offered:
                console.print(f"[red]Insufficient balance of {asset_offered}. You have {assets[asset_offered]} but offered {amount_offered}[/red]")
                return None
            
            # Create the offer
            offer_id = str(uuid.uuid4())
            offer = SwapOffer(
                offer_id=offer_id,
                owner_address=owner_address,
                asset_offered=asset_offered,
                amount_offered=amount_offered,
                asset_wanted=asset_wanted,
                amount_wanted=amount_wanted
            )
            
            # Add the offer to the list
            self.offers.append(offer)
            
            # Save the offers
            self._save_offers()
            
            # Add both assets to monitored assets
            self.monitored_assets.add(asset_offered)
            self.monitored_assets.add(asset_wanted)
            
            console.print(f"[green]Created swap offer {offer_id}[/green]")
            console.print(f"[green]Now monitoring assets: {asset_offered}, {asset_wanted}[/green]")
            return offer
            
        except Exception as e:
            console.print(f"[red]Error creating swap offer: {e}[/red]")
            return None
    
    async def list_swap_offers(self, status: str = "open") -> None:
        """List all swap offers with the specified status."""
        filtered_offers = [offer for offer in self.offers if offer.status == status]
        
        console.print(f"\n[bold blue]Available Swap Offers ({status}):[/bold blue]")
        
        if not filtered_offers:
            console.print(f"[yellow]No {status} swap offers found.[/yellow]")
            return
        
        offer_table = Table(show_header=True)
        offer_table.add_column("ID", style="cyan")
        offer_table.add_column("Offered Asset", style="green")
        offer_table.add_column("Amount", style="green")
        offer_table.add_column("Wanted Asset", style="yellow")
        offer_table.add_column("Amount", style="yellow")
        offer_table.add_column("Owner", style="blue")
        
        for offer in filtered_offers:
            offer_table.add_row(
                offer.offer_id[:8],
                offer.asset_offered,
                str(offer.amount_offered),
                offer.asset_wanted,
                str(offer.amount_wanted),
                offer.owner_address[:10] + "..."
            )
        
        console.print(offer_table)
    
    async def get_transaction_confirmations(self, txid: str) -> int:
        """Get the number of confirmations for a transaction."""
        try:
            tx_info = await self.rpc_client.getrawtransaction(txid, True)
            return tx_info.get("confirmations", 0)
        except Exception:
            return 0
    
    async def wait_for_confirmation(self, txid: str, required_confirmations: int = 1) -> bool:
        """Wait for a transaction to be confirmed."""
        with console.status(f"[yellow]Waiting for transaction {txid[:8]}... to be confirmed...[/yellow]") as status:
            for i in range(30):  # Wait up to 30 * 10 seconds = 5 minutes
                confirmations = await self.get_transaction_confirmations(txid)
                if confirmations >= required_confirmations:
                    status.update(f"[green]Transaction {txid[:8]}... confirmed with {confirmations} confirmations[/green]")
                    return True
                status.update(f"[yellow]Waiting for transaction {txid[:8]}... ({confirmations}/{required_confirmations} confirmations)[/yellow]")
                await asyncio.sleep(10)  # Check every 10 seconds
            
            status.update(f"[red]Transaction {txid[:8]}... not confirmed after 5 minutes[/red]")
            return False
    
    async def execute_swap(self, offer_id: str, taker_address: str) -> bool:
        """Execute a swap offer."""
        # Find the offer
        offer = next((o for o in self.offers if o.offer_id == offer_id), None)
        
        if not offer:
            console.print(f"[red]Offer {offer_id} not found[/red]")
            return False
        
        if offer.status != "open":
            console.print(f"[red]Offer {offer_id} is not open (status: {offer.status})[/red]")
            return False
        
        try:
            # Check if the taker has enough of the wanted asset
            assets = await self.rpc_client.listmyassets()
            
            if offer.asset_wanted not in assets:
                console.print(f"[red]You don't own the asset {offer.asset_wanted}[/red]")
                return False
            
            if assets[offer.asset_wanted] < offer.amount_wanted:
                console.print(f"[red]Insufficient balance of {offer.asset_wanted}. You have {assets[offer.asset_wanted]} but need {offer.amount_wanted}[/red]")
                return False
            
            # Execute the swap on-chain
            console.print(f"[yellow]Executing swap for offer {offer_id}...[/yellow]")
            
            # Step 1: Taker sends the wanted asset to the offer owner
            console.print(f"[yellow]Step 1: Sending {offer.amount_wanted} {offer.asset_wanted} to {offer.owner_address}[/yellow]")
            txid_payment = await self.rpc_client.transfer(
                offer.asset_wanted,
                offer.amount_wanted,
                offer.owner_address,
                f"Payment for swap offer {offer_id}"
            )
            console.print(f"[green]Payment transaction sent: {txid_payment}[/green]")
            
            # Wait for the payment transaction to be confirmed
            if not await self.wait_for_confirmation(txid_payment):
                console.print(f"[red]Payment transaction not confirmed. Swap aborted.[/red]")
                return False
            
            # Update the offer with the payment transaction and taker address
            offer.txid_payment = txid_payment
            offer.taker_address = taker_address
            offer.status = "payment_received"
            offer.updated_at = datetime.now().isoformat()
            self._save_offers()
            
            # Step 2: Owner sends the offered asset to the taker
            console.print(f"[yellow]Step 2: Sending {offer.amount_offered} {offer.asset_offered} to {taker_address}[/yellow]")
            txid_offer = await self.rpc_client.transfer(
                offer.asset_offered,
                offer.amount_offered,
                taker_address,
                f"Asset transfer for swap offer {offer_id}"
            )
            console.print(f"[green]Asset transfer transaction sent: {txid_offer}[/green]")
            
            # Wait for the asset transfer transaction to be confirmed
            if not await self.wait_for_confirmation(txid_offer):
                console.print(f"[red]Asset transfer transaction not confirmed. Swap partially completed.[/red]")
                # We don't return False here because the payment was already made
            
            # Update the offer status
            offer.status = "completed"
            offer.txid_offer = txid_offer
            offer.updated_at = datetime.now().isoformat()
            
            # Save the offers
            self._save_offers()
            
            console.print(f"[green]Swap executed successfully![/green]")
            console.print(f"[green]Payment transaction: {txid_payment}[/green]")
            console.print(f"[green]Asset transfer transaction: {txid_offer}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error executing swap: {e}[/red]")
            return False
    
    async def complete_swap_after_payment(self, offer: SwapOffer) -> bool:
        """Complete a swap after payment has been received."""
        try:
            if offer.status != "payment_received" or not offer.taker_address:
                return False
                
            console.print(f"[yellow]Completing swap for offer {offer.offer_id[:8]}... after payment received[/yellow]")
            
            # Send the offered asset to the taker
            console.print(f"[yellow]Sending {offer.amount_offered} {offer.asset_offered} to {offer.taker_address}[/yellow]")
            txid_offer = await self.rpc_client.transfer(
                offer.asset_offered,
                offer.amount_offered,
                offer.taker_address,
                f"Asset transfer for swap offer {offer.offer_id}"
            )
            console.print(f"[green]Asset transfer transaction sent: {txid_offer}[/green]")
            
            # Wait for the asset transfer transaction to be confirmed
            if not await self.wait_for_confirmation(txid_offer):
                console.print(f"[red]Asset transfer transaction not confirmed. Swap partially completed.[/red]")
                return False
            
            # Update the offer status
            offer.status = "completed"
            offer.txid_offer = txid_offer
            offer.updated_at = datetime.now().isoformat()
            
            # Save the offers
            self._save_offers()
            
            console.print(f"[green]Swap completed automatically after payment![/green]")
            console.print(f"[green]Asset transfer transaction: {txid_offer}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error completing swap after payment: {e}[/red]")
            return False
    
    def display_recent_activity(self) -> None:
        """Display recent blockchain activity."""
        console.print("\n[bold blue]Recent Blocks:[/bold blue]")
        
        if not self.recent_blocks:
            console.print("[yellow]No recent blocks.[/yellow]")
        else:
            block_table = Table(show_header=True)
            block_table.add_column("Height", style="cyan")
            block_table.add_column("Hash", style="green")
            block_table.add_column("Time", style="yellow")
            block_table.add_column("Transactions", style="blue")
            
            for block in reversed(self.recent_blocks):
                block_table.add_row(
                    str(block["height"]),
                    block["hash"][:10] + "...",
                    datetime.fromtimestamp(block["time"]).strftime("%Y-%m-%d %H:%M:%S"),
                    str(block["tx_count"])
                )
            
            console.print(block_table)
        
        console.print("\n[bold blue]Recent Transactions:[/bold blue]")
        
        if not self.recent_transactions:
            console.print("[yellow]No recent transactions.[/yellow]")
        else:
            tx_table = Table(show_header=True)
            tx_table.add_column("TXID", style="cyan")
            tx_table.add_column("Time", style="green")
            tx_table.add_column("Inputs", style="yellow")
            tx_table.add_column("Outputs", style="blue")
            
            for tx in reversed(self.recent_transactions):
                tx_table.add_row(
                    tx["txid"][:10] + "...",
                    tx["time"].split("T")[0] + " " + tx["time"].split("T")[1][:8],
                    str(tx["inputs"]),
                    str(tx["outputs"])
                )
            
            console.print(tx_table)
    
    def view_completed_swaps(self) -> None:
        """View completed swap transactions."""
        completed_offers = [offer for offer in self.offers if offer.status == "completed"]
        
        console.print(f"\n[bold blue]Completed Swaps:[/bold blue]")
        
        if not completed_offers:
            console.print(f"[yellow]No completed swaps found.[/yellow]")
            return
        
        swap_table = Table(show_header=True)
        swap_table.add_column("ID", style="cyan")
        swap_table.add_column("Offered Asset", style="green")
        swap_table.add_column("Amount", style="green")
        swap_table.add_column("Wanted Asset", style="yellow")
        swap_table.add_column("Amount", style="yellow")
        swap_table.add_column("Owner", style="blue")
        swap_table.add_column("Taker", style="magenta")
        swap_table.add_column("Payment TX", style="cyan")
        swap_table.add_column("Asset TX", style="green")
        
        for offer in completed_offers:
            swap_table.add_row(
                offer.offer_id[:8],
                offer.asset_offered,
                str(offer.amount_offered),
                offer.asset_wanted,
                str(offer.amount_wanted),
                offer.owner_address[:10] + "...",
                offer.taker_address[:10] + "..." if offer.taker_address else "N/A",
                offer.txid_payment[:8] + "..." if offer.txid_payment else "N/A",
                offer.txid_offer[:8] + "..." if offer.txid_offer else "N/A"
            )
        
        console.print(swap_table)

    async def cancel_swap_offer(self, offer_id: str, owner_address: str) -> bool:
        """Cancel a swap offer."""
        # Find the offer
        offer = next((o for o in self.offers if o.offer_id == offer_id), None)
        
        if not offer:
            console.print(f"[red]Offer {offer_id} not found[/red]")
            return False
            
        if offer.status != "open":
            console.print(f"[red]Offer {offer_id} is not open (status: {offer.status})[/red]")
            return False
        
        if offer.owner_address != owner_address:
            console.print(f"[red]You are not the owner of offer {offer_id}[/red]")
            return False
        
        try:
            # Update the offer status
            offer.status = "cancelled"
            offer.updated_at = datetime.now().isoformat()
            
            # Save the offers
            self._save_offers()
            
            console.print(f"[green]Offer {offer_id} cancelled successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error cancelling offer: {e}[/red]")
            return False


async def main():
    """Main function to run the asset swap platform."""
    console.print(Panel.fit(
        "[bold blue]Real-time Asset Swap Platform[/bold blue]\n"
        "A demonstration of using evrmore-rpc with WebSockets for DeFi applications",
        title="Evrmore Asset Swap",
        subtitle="Press Ctrl+C to exit"
    ))
    
    try:
        # Initialize the platform
        platform = AssetSwapPlatform()
        await platform.initialize()
        
        # Start the platform
        await platform.start()
        
        # Set up signal handling for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(platform, loop)))
        
        # For demo purposes, let's use a fixed address
        my_address = "EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your address
        
        # Enable automatic completion of swaps after payment
        platform.auto_complete_swaps = True
        
        while True:
            console.print("\n[bold]Choose an option:[/bold]")
            console.print("1. List my assets")
            console.print("2. Create swap offer")
            console.print("3. List available swap offers")
            console.print("4. Execute swap")
            console.print("5. Cancel swap offer")
            console.print("6. View recent activity")
            console.print("7. View completed swaps")
            console.print("8. Exit")
            
            choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                assets = await platform.list_my_assets()
                if not assets:
                    console.print("[yellow]You don't have any assets.[/yellow]")
                
            elif choice == "2":
                # Get asset details
                asset_offered = Prompt.ask("Enter the asset you want to offer")
                amount_offered = Decimal(Prompt.ask("Enter the amount you want to offer"))
                asset_wanted = Prompt.ask("Enter the asset you want in return")
                amount_wanted = Decimal(Prompt.ask("Enter the amount you want in return"))
                
                # Create the swap offer
                offer = await platform.create_swap_offer(
                    my_address,
                    asset_offered,
                    amount_offered,
                    asset_wanted,
                    amount_wanted
                )
                
                if offer:
                    console.print(f"[green]Swap offer created with ID: {offer.offer_id}[/green]")
                
            elif choice == "3":
                await platform.list_swap_offers()
                
            elif choice == "4":
                offer_id = Prompt.ask("Enter the offer ID you want to execute")
                taker_address = Prompt.ask("Enter your address")
                
                success = await platform.execute_swap(offer_id, taker_address)
                if success:
                    console.print(f"[green]Swap executed successfully![/green]")
                
            elif choice == "5":
                offer_id = Prompt.ask("Enter the offer ID you want to cancel")
                owner_address = Prompt.ask("Enter your address")
                
                success = await platform.cancel_swap_offer(offer_id, owner_address)
                if success:
                    console.print(f"[green]Swap offer cancelled successfully![/green]")
                
            elif choice == "6":
                platform.display_recent_activity()
                
            elif choice == "7":
                platform.view_completed_swaps()
                
            elif choice == "8":
                break
                
            # Small pause to make the UI more readable
            await asyncio.sleep(1)
        
        # Clean shutdown
        await platform.stop()
        console.print("[bold green]Thank you for using the Asset Swap Platform![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        console.print("[yellow]Shutting down...[/yellow]")
        try:
            if 'platform' in locals():
                await platform.stop()
        except:
            pass


async def shutdown(platform, loop):
    """Gracefully shut down the platform."""
    console.print("[yellow]Shutting down...[/yellow]")
    await platform.stop()
    loop.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Program interrupted by user. Exiting...[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]") 