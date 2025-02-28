#!/usr/bin/env python3
"""
Simple Asset Swap Platform

This example demonstrates how to create a simple asset swap platform using the evrmore-rpc library.
It allows users to:
1. List their assets for trade
2. View available swap offers
3. Execute swaps between different assets

This is a basic example intended for new Evrmore developers to understand how to use the library
for building DeFi applications.
"""

import asyncio
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.status import Status

# Import the evrmore-rpc library
# As a new developer, I'm starting with the basic imports I think I'll need
from evrmore_rpc import EvrmoreRPCClient, EvrmoreAsyncRPCClient

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
    A simple asset swap platform using the evrmore-rpc library.
    """
    
    def __init__(self, data_file: str = "swap_offers.json"):
        """Initialize the asset swap platform."""
        self.data_file = data_file
        self.offers: List[SwapOffer] = []
        self.client = EvrmoreRPCClient()  # Using the synchronous client for simplicity
        
        # Load existing offers if the data file exists
        self._load_offers()
        
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
    
    def list_my_assets(self, address: Optional[str] = None) -> Dict[str, Decimal]:
        """List assets owned by the specified address."""
        try:
            # Get assets owned by the address
            assets = self.client.listmyassets()
            
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
            
            console.print(asset_table)
            return assets
            
        except Exception as e:
            console.print(f"[red]Error listing assets: {e}[/red]")
            return {}
    
    def create_swap_offer(self, 
                         owner_address: str,
                         asset_offered: str, 
                         amount_offered: Decimal,
                         asset_wanted: str,
                         amount_wanted: Decimal) -> Optional[SwapOffer]:
        """Create a new swap offer."""
        try:
            # Check if the user has enough of the offered asset
            assets = self.client.listmyassets()
            
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
            
            console.print(f"[green]Created swap offer {offer_id}[/green]")
            return offer
            
        except Exception as e:
            console.print(f"[red]Error creating swap offer: {e}[/red]")
            return None
    
    def list_swap_offers(self, status: str = "open") -> None:
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
    
    def get_transaction_confirmations(self, txid: str) -> int:
        """Get the number of confirmations for a transaction."""
        try:
            tx_info = self.client.getrawtransaction(txid, True)
            return tx_info.get("confirmations", 0)
        except Exception:
            return 0
    
    def wait_for_confirmation(self, txid: str, required_confirmations: int = 1) -> bool:
        """Wait for a transaction to be confirmed."""
        with Status(f"[yellow]Waiting for transaction {txid[:8]}... to be confirmed...[/yellow]") as status:
            for i in range(30):  # Wait up to 30 * 10 seconds = 5 minutes
                confirmations = self.get_transaction_confirmations(txid)
                if confirmations >= required_confirmations:
                    status.update(f"[green]Transaction {txid[:8]}... confirmed with {confirmations} confirmations[/green]")
                    return True
                status.update(f"[yellow]Waiting for transaction {txid[:8]}... ({confirmations}/{required_confirmations} confirmations)[/yellow]")
                time.sleep(10)  # Check every 10 seconds
            
            status.update(f"[red]Transaction {txid[:8]}... not confirmed after 5 minutes[/red]")
            return False
    
    def execute_swap(self, offer_id: str, taker_address: str) -> bool:
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
            assets = self.client.listmyassets()
            
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
            txid_payment = self.client.transfer(
                offer.asset_wanted,
                offer.amount_wanted,
                offer.owner_address,
                f"Payment for swap offer {offer_id}"
            )
            console.print(f"[green]Payment transaction sent: {txid_payment}[/green]")
            
            # Wait for the payment transaction to be confirmed
            if not self.wait_for_confirmation(txid_payment):
                console.print(f"[red]Payment transaction not confirmed. Swap aborted.[/red]")
                return False
            
            # Step 2: Owner sends the offered asset to the taker
            console.print(f"[yellow]Step 2: Sending {offer.amount_offered} {offer.asset_offered} to {taker_address}[/yellow]")
            txid_offer = self.client.transfer(
                offer.asset_offered,
                offer.amount_offered,
                taker_address,
                f"Asset transfer for swap offer {offer_id}"
            )
            console.print(f"[green]Asset transfer transaction sent: {txid_offer}[/green]")
            
            # Wait for the asset transfer transaction to be confirmed
            if not self.wait_for_confirmation(txid_offer):
                console.print(f"[red]Asset transfer transaction not confirmed. Swap partially completed.[/red]")
                # We don't return False here because the payment was already made
            
            # Update the offer status
            offer.status = "completed"
            offer.updated_at = datetime.now().isoformat()
            offer.taker_address = taker_address
            offer.txid_payment = txid_payment
            offer.txid_offer = txid_offer
            
            # Save the offers
            self._save_offers()
            
            console.print(f"[green]Swap executed successfully![/green]")
            console.print(f"[green]Payment transaction: {txid_payment}[/green]")
            console.print(f"[green]Asset transfer transaction: {txid_offer}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error executing swap: {e}[/red]")
            return False
    
    def cancel_swap_offer(self, offer_id: str, owner_address: str) -> bool:
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


async def main():
    """Main function to run the asset swap platform."""
    console.print(Panel.fit(
        "[bold blue]Simple Asset Swap Platform[/bold blue]\n"
        "A demonstration of using evrmore-rpc for DeFi applications",
        title="Evrmore Asset Swap",
        subtitle="Press Ctrl+C to exit"
    ))
    
    # Initialize the platform
    platform = AssetSwapPlatform()
    
    # For demo purposes, let's use a fixed address
    my_address = "EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your address
    
    while True:
        console.print("\n[bold]Choose an option:[/bold]")
        console.print("1. List my assets")
        console.print("2. Create swap offer")
        console.print("3. List available swap offers")
        console.print("4. Execute swap")
        console.print("5. Cancel swap offer")
        console.print("6. View completed swaps")
        console.print("7. Exit")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == "1":
            platform.list_my_assets()
            
        elif choice == "2":
            # First list assets to help the user choose
            assets = platform.list_my_assets()
            
            if not assets:
                continue
                
            asset_offered = Prompt.ask("Enter asset to offer")
            if asset_offered not in assets:
                console.print(f"[red]You don't own the asset {asset_offered}[/red]")
                continue
                
            amount_offered = Decimal(Prompt.ask("Enter amount to offer"))
            if amount_offered <= 0 or amount_offered > assets[asset_offered]:
                console.print(f"[red]Invalid amount. You have {assets[asset_offered]} {asset_offered}[/red]")
                continue
                
            asset_wanted = Prompt.ask("Enter asset you want")
            amount_wanted = Decimal(Prompt.ask("Enter amount you want"))
            
            if amount_wanted <= 0:
                console.print("[red]Amount must be greater than 0[/red]")
                continue
                
            platform.create_swap_offer(
                owner_address=my_address,
                asset_offered=asset_offered,
                amount_offered=amount_offered,
                asset_wanted=asset_wanted,
                amount_wanted=amount_wanted
            )
            
        elif choice == "3":
            platform.list_swap_offers()
            
        elif choice == "4":
            platform.list_swap_offers()
            
            offer_id = Prompt.ask("Enter the ID of the offer to execute")
            platform.execute_swap(offer_id, my_address)
            
        elif choice == "5":
            # List only my offers
            my_offers = [offer for offer in platform.offers 
                        if offer.owner_address == my_address and offer.status == "open"]
            
            console.print("\n[bold blue]Your Open Offers:[/bold blue]")
            
            if not my_offers:
                console.print("[yellow]You don't have any open offers.[/yellow]")
                continue
                
            offer_table = Table(show_header=True)
            offer_table.add_column("ID", style="cyan")
            offer_table.add_column("Offered Asset", style="green")
            offer_table.add_column("Amount", style="green")
            offer_table.add_column("Wanted Asset", style="yellow")
            offer_table.add_column("Amount", style="yellow")
            
            for offer in my_offers:
                offer_table.add_row(
                    offer.offer_id[:8],
                    offer.asset_offered,
                    str(offer.amount_offered),
                    offer.asset_wanted,
                    str(offer.amount_wanted)
                )
            
            console.print(offer_table)
            
            offer_id = Prompt.ask("Enter the ID of the offer to cancel")
            platform.cancel_swap_offer(offer_id, my_address)
            
        elif choice == "6":
            platform.view_completed_swaps()
            
        elif choice == "7":
            break
            
        # Small pause to make the UI more readable
        await asyncio.sleep(1)
    
    console.print("[bold green]Thank you for using the Asset Swap Platform![/bold green]")


if __name__ == "__main__":
    try:
        import time  # Import time for sleep functionality
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Program interrupted by user. Exiting...[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]") 