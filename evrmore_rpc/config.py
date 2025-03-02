from pathlib import Path
import os
from typing import Dict, Any, Optional, List, Tuple, Union
import re
import logging

logger = logging.getLogger(__name__)

DEFAULT_DATADIR = Path.home() / ".evrmore"

class EvrmoreConfig:
    """
    Parser for Evrmore configuration files.
    Reads and parses the evrmore.conf file to extract configuration options.
    """
    
    def __init__(self, datadir: Optional[Union[str, Path]] = None, testnet: bool = False):
        """
        Initialize the Evrmore configuration parser.
        
        Args:
            datadir: Path to the Evrmore data directory (defaults to ~/.evrmore)
            testnet: Whether to use testnet configuration
        """
        self.datadir = Path(datadir) if datadir else DEFAULT_DATADIR
        self.testnet = testnet
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load and parse the Evrmore configuration file."""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            logger.warning(f"Evrmore config file not found at {config_path}")
            return
            
        try:
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Handle key=value pairs
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert value to appropriate type
                        if value.lower() in ("true", "1", "yes", "y"):
                            value = True
                        elif value.lower() in ("false", "0", "no", "n"):
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r"^-?\d+\.\d+$", value):
                            value = float(value)
                            
                        self.config[key] = value
                    # Handle boolean flags (without value)
                    else:
                        self.config[line] = True
        except Exception as e:
            logger.error(f"Error parsing Evrmore config file: {e}")
    
    def _get_config_path(self) -> Path:
        """Get the path to the Evrmore configuration file."""
        if self.testnet:
            return self.datadir / "testnet3" / "evrmore.conf"
        return self.datadir / "evrmore.conf"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.config.get(key, default)
    
    def get_rpc_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Get RPC username and password."""
        return self.get("rpcuser"), self.get("rpcpassword")
    
    def get_rpc_connection_info(self) -> Tuple[str, int]:
        """Get RPC host and port."""
        host = self.get("rpcbind", "127.0.0.1")
        if host == "0.0.0.0":
            host = "127.0.0.1"  # Use localhost if binding to all interfaces
            
        port = self.get("rpcport", 8819 if not self.testnet else 18819)
        return host, port
    
    def get_zmq_endpoints(self) -> Dict[str, str]:
        """Get ZMQ endpoints configuration."""
        zmq_endpoints = {}
        for key, value in self.config.items():
            if key.startswith("zmqpub") and not key.endswith("hwm"):
                # Extract the notification type from the key
                # e.g., zmqpubhashtx -> hashtx
                notification_type = key[6:]
                zmq_endpoints[notification_type] = value
        return zmq_endpoints
    
    def get_zmq_hwm(self) -> Dict[str, int]:
        """Get ZMQ high water mark configuration."""
        zmq_hwm = {}
        for key, value in self.config.items():
            if key.startswith("zmqpub") and key.endswith("hwm"):
                # Extract the notification type from the key
                # e.g., zmqpubhashtxhwm -> hashtx
                notification_type = key[6:-3]
                zmq_hwm[notification_type] = int(value)
        return zmq_hwm
    
    def get_p2p_connection_info(self) -> Tuple[str, int]:
        """Get P2P host and port."""
        host = "127.0.0.1"  # P2P always binds to all interfaces
        port = self.get("port", 8820 if not self.testnet else 18820)
        return host, port
    
    def is_server_enabled(self) -> bool:
        """Check if the RPC server is enabled."""
        return self.get("server", False)
    
    def is_index_enabled(self, index_name: str) -> bool:
        """Check if a specific index is enabled."""
        return self.get(index_name, False)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration options."""
        return self.config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access to configuration options."""
        return self.config[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if a configuration option exists."""
        return key in self.config 