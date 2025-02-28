#!/usr/bin/env python3
"""
Example WebSocket server for Evrmore blockchain.

This script demonstrates how to run a WebSocket server that broadcasts
real-time blockchain events like new blocks and transactions.
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional

from evrmore_rpc import EvrmoreClient, EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("websocket-server-example")

# Global server instance for graceful shutdown
server: Optional[EvrmoreWebSocketServer] = None

async def main():
    """Run the WebSocket server example."""
    global server
    
    # Create RPC client
    rpc_client = EvrmoreClient(
        rpcuser="user",
        rpcpassword="password",
        rpchost="localhost",
        rpcport=8819,
    )
    
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient(
        host="localhost",
        port=28332,
    )
    
    # Create WebSocket server
    server = EvrmoreWebSocketServer(
        rpc_client=rpc_client,
        zmq_client=zmq_client,
        host="localhost",
        port=8765,
        ping_interval=30,
    )
    
    try:
        # Start the server
        await server.start()
        logger.info(f"WebSocket server started on ws://{server.host}:{server.port}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the server running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Stop the server
        if server:
            await server.stop()
            logger.info("WebSocket server stopped")

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the main function
    asyncio.run(main()) 