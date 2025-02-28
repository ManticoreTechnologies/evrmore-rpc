from typing import Dict, List, Optional, Any
import sys
import time
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from rich.align import Align
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.style import Style
import curses

from evrmore_rpc import EvrmoreRPCClient, EvrmoreRPCError

console = Console()

COMMAND_CATEGORIES = {
    "Addressindex": {
        "getaddressbalance": {
            "description": "Get balance for address(es)",
            "args": ["addresses"]
        },
        "getaddressdeltas": {
            "description": "Get all changes for address(es)",
            "args": ["addresses", "start", "end"]
        },
        "getaddressmempool": {
            "description": "Get all mempool entries for address(es)",
            "args": ["addresses"]
        },
        "getaddresstxids": {
            "description": "Get all transaction IDs for address(es)",
            "args": ["addresses", "start", "end"]
        },
        "getaddressutxos": {
            "description": "Get all unspent outputs for address(es)",
            "args": ["addresses", "chainInfo"]
        }
    },
    "Blockchain": [
        ("getblockchaininfo", "Get current blockchain information"),
        ("getblock", "Get block data by hash"),
        ("getblockcount", "Get current block height"),
        ("getblockhash", "Get block hash by height"),
        ("getdifficulty", "Get current mining difficulty"),
    ],
    "Control": [
        ("getinfo", "Get various state info about the server and wallet"),
        ("getmemoryinfo", "Get information about memory usage"),
        ("getrpcinfo", "Get runtime details of the RPC server"),
        ("help", "Get help for a command"),
        ("stop", "Stop Evrmore server"),
        ("uptime", "Get server uptime in seconds"),
    ],
    "Generating": [
        ("generate", "Mine blocks immediately to an address in the wallet"),
        ("generatetoaddress", "Mine blocks immediately to a specified address"),
        ("getgenerate", "Return if the server is set to generate coins"),
        ("setgenerate", "Set whether the server should generate coins"),
    ],
    "Messages": [
        ("clearmessages", "Clear all locally stored messages"),
        ("sendmessage", "Send a message to a channel"),
        ("subscribetochannel", "Subscribe to a message channel"),
        ("unsubscribefromchannel", "Unsubscribe from a message channel"),
        ("viewallmessagechannels", "View all message channels"),
        ("viewallmessages", "View all messages"),
    ],
    "Mining": [
        ("getblocktemplate", "Get block template for mining"),
        ("getevrprogpowhash", "Get EVR ProgPoW hash"),
        ("getmininginfo", "Get mining-related information"),
        ("getnetworkhashps", "Get network hashes per second"),
        ("pprpcsb", "Submit ProgPoW solution"),
        ("prioritisetransaction", "Prioritize a transaction"),
        ("submitblock", "Submit a new block to the network"),
    ],
    "Network": [
        ("addnode", "Add, remove or try a connection to a node"),
        ("clearbanned", "Clear all banned IPs"),
        ("disconnectnode", "Disconnect from a specified node"),
        ("getaddednodeinfo", "Get information about added nodes"),
        ("getconnectioncount", "Get the number of connections to other nodes"),
        ("getnettotals", "Get network traffic statistics"),
        ("getnetworkinfo", "Get network info"),
        ("getpeerinfo", "Get data about each connected node"),
        ("listbanned", "List all banned IPs/Subnets"),
        ("ping", "Request that a ping be sent to all other nodes"),
        ("setban", "Add or remove an IP/Subnet from the banned list"),
        ("setnetworkactive", "Enable/disable all P2P network activity"),
    ],
    "Assets": [
        ("listassets", "List all assets"),
        ("listmyassets", "List owned assets"),
        ("getassetdata", "Get data about an asset"),
        ("issue", "Issue a new asset"),
        ("transfer", "Transfer an asset"),
        ("reissue", "Reissue an existing asset"),
    ],
    "Raw Transactions": {
        "combinerawtransaction": {
            "description": "Combine multiple partially signed transactions into one transaction",
            "args": ["txs"]
        },
        "createrawtransaction": {
            "description": "Create a transaction spending the given inputs and creating new outputs",
            "args": ["inputs", "outputs", "locktime", "replaceable"]
        },
        "decoderawtransaction": {
            "description": "Return a JSON object representing the serialized, hex-encoded transaction",
            "args": ["hexstring", "iswitness"]
        },
        "decodescript": {
            "description": "Decode a hex-encoded script",
            "args": ["hexstring"]
        },
        "fundrawtransaction": {
            "description": "Add inputs to a transaction until it has enough in value to meet its out value",
            "args": ["hexstring", "options", "iswitness"]
        },
        "getrawtransaction": {
            "description": "Return the raw transaction data",
            "args": ["txid", "verbose", "blockhash"]
        },
        "sendrawtransaction": {
            "description": "Submits raw transaction (serialized, hex-encoded) to local node and network",
            "args": ["hexstring", "allowhighfees", "showcontractinfo"]
        },
        "signrawtransaction": {
            "description": "Sign inputs for raw transaction",
            "args": ["hexstring", "prevtxs", "privkeys", "sighashtype"]
        },
        "testmempoolaccept": {
            "description": "Returns result of mempool acceptance tests indicating if raw transaction would be accepted by mempool",
            "args": ["rawtxs", "allowhighfees", "showcontractinfo"]
        }
    },
}

def create_menu() -> Table:
    """Create the main menu table."""
    table = Table(title="Evrmore RPC Interactive Menu", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Commands", style="green")
    
    for category, commands in COMMAND_CATEGORIES.items():
        commands_text = "\n".join(f"• {cmd[0]}" for cmd in commands)
        table.add_row(category, commands_text)
    
    return table

def show_command_help(category: str, command: str) -> Panel:
    """Show detailed help for a command."""
    cmd_info = next((cmd for cmd in COMMAND_CATEGORIES[category] if cmd[0] == command), None)
    if not cmd_info:
        return Panel(f"Command {command} not found", title="Error", border_style="red")
    
    help_text = Text()
    help_text.append(f"Command: ", style="bold cyan")
    help_text.append(command, style="green")
    help_text.append("\n\nDescription: ", style="bold cyan")
    help_text.append(cmd_info[1])
    
    # Add parameter information based on the command
    params = get_command_params(command)
    if params:
        help_text.append("\n\nParameters:", style="bold cyan")
        for param, desc in params.items():
            help_text.append(f"\n• {param}: ", style="yellow")
            help_text.append(desc)
    
    return Panel(help_text, title=f"Help: {command}", border_style="blue")

def get_command_params(command: str) -> Dict[str, str]:
    """Get parameters for a command."""
    params = {
        "getaddressbalance": {
            "addresses": "Single address or list of addresses to get balance for"
        },
        "getaddressdeltas": {
            "addresses": "Single address or list of addresses to get deltas for",
            "start": "(optional) Start height",
            "end": "(optional) End height"
        },
        "getaddressmempool": {
            "addresses": "Single address or list of addresses to get mempool entries for"
        },
        "getaddresstxids": {
            "addresses": "Single address or list of addresses to get txids for",
            "start": "(optional) Start height",
            "end": "(optional) End height"
        },
        "getaddressutxos": {
            "addresses": "Single address or list of addresses to get UTXOs for",
            "chainInfo": "(optional) Include chain info in response"
        },
        "getblock": {
            "blockhash": "The hash of the block to get",
            "verbosity": "0 for hex, 1 for json (default), 2 for json with tx data"
        },
        "getblockhash": {
            "height": "The height of the block to get the hash for"
        },
        "getmemoryinfo": {
            "mode": "(optional) Memory info mode (default: 'stats')"
        },
        "help": {
            "command": "(optional) The command to get help for"
        },
        "generate": {
            "nblocks": "How many blocks to generate immediately",
            "maxtries": "(optional) How many iterations to try (default: 1000000)"
        },
        "generatetoaddress": {
            "nblocks": "How many blocks to generate immediately",
            "address": "The address to send the newly generated EVR to",
            "maxtries": "(optional) How many iterations to try (default: 1000000)"
        },
        "setgenerate": {
            "generate": "Set to true to turn on generation, false to turn off",
            "genproclimit": "(optional) Set the processor limit for when generation is on"
        },
        "sendmessage": {
            "channel_name": "Name of the channel to send a message to",
            "ipfs_hash": "The IPFS hash of the message",
            "expire_time": "(optional) UTC timestamp of when the message expires"
        },
        "subscribetochannel": {
            "channel_name": "Name of the channel to subscribe to"
        },
        "unsubscribefromchannel": {
            "channel_name": "Name of the channel to unsubscribe from"
        },
        "getblocktemplate": {
            "template_request": "(optional) Format of block template"
        },
        "getevrprogpowhash": {
            "header_hash": "The hash of the block header",
            "mix_hash": "The mix hash",
            "nonce": "The nonce value",
            "height": "The block height",
            "target": "The target difficulty"
        },
        "getnetworkhashps": {
            "nblocks": "(optional) Number of blocks to average (default: 120)",
            "height": "(optional) Block height (default: -1)"
        },
        "pprpcsb": {
            "header_hash": "The hash of the block header",
            "mix_hash": "The mix hash",
            "nonce": "The nonce value"
        },
        "prioritisetransaction": {
            "txid": "The transaction ID",
            "dummy_value": "API-Compatibility value (ignored)",
            "fee_delta": "The fee value (in satoshis) to add or subtract"
        },
        "submitblock": {
            "hexdata": "The hex-encoded block data to submit",
            "dummy": "(optional) Dummy value, for compatibility with BIP22"
        },
        "addnode": {
            "node": "The node IP address and port (e.g. 1.2.3.4:8819)",
            "command": "add|remove|onetry"
        },
        "disconnectnode": {
            "address": "(optional) The node IP address",
            "nodeid": "(optional) The node ID"
        },
        "getaddednodeinfo": {
            "node": "(optional) The node IP address"
        },
        "setban": {
            "subnet": "The IP/Subnet (see getpeerinfo for nodes)",
            "command": "add|remove",
            "bantime": "(optional) Time in seconds how long (or until when if [absolute] is set) the IP is banned",
            "absolute": "(optional) If set, the bantime must be an absolute timestamp in seconds since epoch"
        },
        "setnetworkactive": {
            "state": "true to enable networking, false to disable"
        },
        "listassets": {
            "asset": "(optional) Asset name filter",
            "verbose": "(optional) Get detailed asset information",
            "count": "(optional) Number of results to return",
            "start": "(optional) Start from this position"
        },
        "issue": {
            "asset_name": "Name of the asset to create",
            "qty": "Amount of the asset to create",
            "to_address": "(optional) Address to send the asset to",
            "change_address": "(optional) Address for change",
            "units": "(optional) Units of the asset",
            "reissuable": "(optional) Whether the asset can be reissued",
            "has_ipfs": "(optional) Whether the asset has IPFS data",
            "ipfs_hash": "(optional) IPFS hash of the asset data"
        }
    }
    return params.get(command, {})

def execute_command(client: EvrmoreRPCClient, command: str, params: Dict[str, Any]) -> None:
    """Execute a command with given parameters."""
    try:
        result = getattr(client, command)(**params)
        if result is not None:
            if isinstance(result, dict):
                table = Table(show_header=True)
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")
                for key, value in result.items():
                    table.add_row(str(key), str(value))
                console.print(table)
            else:
                console.print(Panel(str(result), title="Result", border_style="green"))
    except EvrmoreRPCError as e:
        console.print(Panel(str(e), title="Error", border_style="red"))
    except Exception as e:
        console.print(Panel(f"Unexpected error: {str(e)}", title="Error", border_style="red"))

def prompt_params(command: str) -> Dict[str, Any]:
    """Prompt for command parameters."""
    params = {}
    param_info = get_command_params(command)
    
    for param, desc in param_info.items():
        optional = "(optional)" in desc
        if optional:
            if Confirm.ask(f"Do you want to specify {param}?"):
                value = Prompt.ask(f"Enter {param}")
                params[param] = value
        else:
            value = Prompt.ask(f"Enter {param}")
            params[param] = value
            
    return params

def interactive_menu():
    """Run the interactive menu."""
    client = EvrmoreRPCClient()
    
    while True:
        console.clear()
        menu = create_menu()
        console.print(menu)
        console.print("\nType 'exit' to quit")
        
        category = Prompt.ask(
            "Select category",
            choices=list(COMMAND_CATEGORIES.keys()) + ["exit"],
            default="exit"
        )
        
        if category.lower() == "exit":
            break
            
        console.clear()
        commands = [cmd[0] for cmd in COMMAND_CATEGORIES[category]]
        command = Prompt.ask(
            "Select command",
            choices=commands + ["back"],
            default="back"
        )
        
        if command == "back":
            continue
            
        console.clear()
        console.print(show_command_help(category, command))
        
        if Confirm.ask("Do you want to execute this command?"):
            params = prompt_params(command)
            execute_command(client, command, params)
            
        if not Confirm.ask("Do you want to try another command?"):
            break
            
        console.print("\nPress Enter to continue...")
        input()

class EvrmoreInteractive:
    def __init__(self):
        self.client = EvrmoreRPCClient()
        self.console = Console()
        self.layout = self._create_layout()
        self.current_category = None
        self.current_command = None
        self.command_output = None
        self.error_message = None
        self.selected_index = 0
        self.mode = "category"  # category, command, or execute
        
    def _create_layout(self) -> Layout:
        """Create the main layout."""
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
            Layout(name="right", ratio=2)
        )
        
        # Split right panel into command info and output
        layout["right"].split(
            Layout(name="command_info", size=10),
            Layout(name="output")
        )
        
        return layout
    
    def _render_header(self) -> Panel:
        """Render the header panel."""
        grid = Table.grid(padding=1)
        grid.add_column(style="green", justify="center")
        grid.add_row("Evrmore RPC Interactive Console")
        return Panel(grid, style="bold white on blue")
    
    def _render_footer(self) -> Panel:
        """Render the footer panel with controls help."""
        controls = {
            "category": "↑/↓: Navigate  Enter: Select  Q: Quit",
            "command": "↑/↓: Navigate  Enter: Select  Backspace: Back  Q: Quit",
            "execute": "Enter: Execute  Backspace: Back  Q: Quit"
        }
        return Panel(controls[self.mode], style="bold white on blue")
    
    def _render_categories(self) -> Panel:
        """Render the categories panel."""
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Categories")
        
        categories = list(COMMAND_CATEGORIES.keys())
        for i, category in enumerate(categories):
            if self.mode == "category" and i == self.selected_index:
                style = Style(color="black", bgcolor="cyan")
            elif category == self.current_category:
                style = Style(color="cyan")
            else:
                style = Style(color="white")
            table.add_row(category, style=style)
            
        return Panel(table, title="Command Categories", border_style="blue")
    
    def _render_commands(self) -> Panel:
        """Render the commands panel."""
        if not self.current_category:
            return Panel("Select a category", title="Commands")
            
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Command")
        table.add_column("Description")
        
        commands = list(COMMAND_CATEGORIES[self.current_category].items())
        for i, (cmd, info) in enumerate(commands):
            if self.mode == "command" and i == self.selected_index:
                style = Style(color="black", bgcolor="green")
            elif cmd == self.current_command:
                style = Style(color="green")
            else:
                style = Style(color="white")
            table.add_row(cmd, info["description"], style=style)
            
        return Panel(table, title=f"Commands - {self.current_category}", border_style="blue")
    
    def _render_command_info(self) -> Panel:
        """Render the command info panel."""
        if not self.current_command:
            return Panel("Select a command", title="Command Info")
            
        info = COMMAND_CATEGORIES[self.current_category][self.current_command]
        text = Text()
        text.append(f"Command: ", style="bold cyan")
        text.append(self.current_command, style="green")
        text.append("\n\nDescription: ", style="bold cyan")
        text.append(info["description"])
        text.append("\n\nArguments: ", style="bold cyan")
        for arg in info["args"]:
            text.append(f"\n• {arg}")
            
        return Panel(text, title="Command Info", border_style="blue")
    
    def _render_output(self) -> Panel:
        """Render the output panel."""
        if self.error_message:
            return Panel(
                Text(self.error_message, style="red"),
                title="Error",
                border_style="red"
            )
            
        if not self.command_output:
            return Panel(
                "Command output will appear here",
                title="Output",
                border_style="blue"
            )
            
        if isinstance(self.command_output, (dict, list)):
            syntax = Syntax(
                json.dumps(self.command_output, indent=2),
                "json",
                theme="monokai",
                word_wrap=True
            )
            return Panel(syntax, title="Output", border_style="green")
        
        return Panel(
            str(self.command_output),
            title="Output",
            border_style="green"
        )
    
    def _handle_input(self, key: int) -> bool:
        """Handle keyboard input. Returns True if should continue, False to exit."""
        if key == ord('q'):
            return False
            
        if self.mode == "category":
            categories = list(COMMAND_CATEGORIES.keys())
            if key == curses.KEY_UP and self.selected_index > 0:
                self.selected_index -= 1
            elif key == curses.KEY_DOWN and self.selected_index < len(categories) - 1:
                self.selected_index += 1
            elif key == ord('\n'):  # Enter key
                self.current_category = categories[self.selected_index]
                self.mode = "command"
                self.selected_index = 0
                
        elif self.mode == "command":
            commands = list(COMMAND_CATEGORIES[self.current_category].keys())
            if key == curses.KEY_UP and self.selected_index > 0:
                self.selected_index -= 1
            elif key == curses.KEY_DOWN and self.selected_index < len(commands) - 1:
                self.selected_index += 1
            elif key == ord('\n'):  # Enter key
                self.current_command = commands[self.selected_index]
                self.mode = "execute"
            elif key == curses.KEY_BACKSPACE:
                self.mode = "category"
                self.current_category = None
                self.current_command = None
                self.selected_index = 0
                
        elif self.mode == "execute":
            if key == ord('\n'):  # Enter key
                self._handle_command_execution()
                self.mode = "command"
            elif key == curses.KEY_BACKSPACE:
                self.mode = "command"
                self.current_command = None
                
        return True
    
    def _handle_command_execution(self):
        """Handle command execution."""
        if not self.current_command:
            return
            
        try:
            # Get command arguments
            args = {}
            command_info = COMMAND_CATEGORIES[self.current_category][self.current_command]
            
            for arg in command_info["args"]:
                # Check if argument is optional
                is_optional = any(opt in arg.lower() for opt in ["optional", "opt", "[", "]"])
                prompt = f"Enter {arg}"
                if is_optional:
                    prompt += " (optional, press Enter to skip)"
                
                value = Prompt.ask(prompt, default="" if is_optional else None)
                if value:
                    # Try to convert to appropriate type
                    if "amount" in arg.lower() or "qty" in arg.lower():
                        value = Decimal(value)
                    elif "height" in arg.lower() or "count" in arg.lower():
                        value = int(value)
                    elif "true" in value.lower():
                        value = True
                    elif "false" in value.lower():
                        value = False
                    args[arg] = value
            
            # Execute command with spinner
            with console.status(
                f"[bold green]Executing {self.current_command}...",
                spinner="dots"
            ):
                result = getattr(self.client, self.current_command)(**args)
                self.command_output = result
                self.error_message = None
                
        except EvrmoreRPCError as e:
            self.error_message = str(e)
            self.command_output = None
        except Exception as e:
            self.error_message = f"Unexpected error: {str(e)}"
            self.command_output = None
    
    def _update_display(self):
        """Update the display with current state."""
        self.layout["header"].update(self._render_header())
        self.layout["footer"].update(self._render_footer())
        self.layout["left"].update(self._render_categories())
        self.layout["right"]["command_info"].update(self._render_command_info())
        self.layout["right"]["output"].update(self._render_output())
    
    def run(self):
        """Run the interactive console."""
        def curses_main(stdscr):
            curses.start_color()
            curses.use_default_colors()
            stdscr.nodelay(0)  # Make getch() blocking
            
            with Live(self.layout, refresh_per_second=10, screen=True):
                while True:
                    self._update_display()
                    key = stdscr.getch()
                    if not self._handle_input(key):
                        break
        
        curses.wrapper(curses_main)

def main():
    """Main entry point for the interactive menu."""
    try:
        EvrmoreInteractive().run()
    except KeyboardInterrupt:
        console.print("\nGoodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main() 