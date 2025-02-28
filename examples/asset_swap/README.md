# Evrmore Asset Swap Platform Example

This example demonstrates how to build a fully functional DeFi application using the `evrmore-rpc` library. The asset swap platform allows users to trade Evrmore assets directly with each other through on-chain transactions.

## Features

- **Basic Version (`simple_swap.py`)**:
  - List your assets and balances
  - Create swap offers for trading assets
  - View available swap offers from other users
  - Execute swaps with on-chain transactions
  - Cancel your own swap offers

- **Real-time Version (`realtime_swap.py`)**:
  - All features from the basic version
  - Real-time monitoring of new assets and transfers via WebSockets
  - ZMQ notifications for new transactions and blocks
  - Automatic offer matching for compatible trades
  - Automatic completion of swaps after payment detection
  - Transaction confirmation monitoring

## Requirements

- Python 3.7+
- `evrmore-rpc` library
- `rich` library for console UI
- Running Evrmore node with RPC access
- For the real-time version: WebSocket and ZMQ enabled on your Evrmore node

## Installation

```bash
pip install evrmore-rpc rich
```

## Configuration

Ensure your Evrmore node is configured with the following settings in `evrmore.conf`:

```
server=1
rpcuser=your_username
rpcpassword=your_password
rpcallowip=127.0.0.1
```

For the real-time version, also add:

```
# WebSocket configuration
rpcbind=0.0.0.0
rpcallowip=0.0.0.0/0
websocket=1
websocketport=8443

# ZMQ configuration
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
```

## Usage

### Basic Version

Run the basic asset swap platform:

```bash
python simple_swap.py
```

This will start an interactive console application where you can:
1. List your assets
2. Create swap offers
3. View available offers
4. Execute swaps with on-chain transactions
5. Cancel your offers

### Real-time Version

Run the real-time asset swap platform:

```bash
python realtime_swap.py
```

This version provides all the functionality of the basic version plus:
1. Real-time notifications of new assets and transfers
2. Automatic detection of matching offers
3. Automatic completion of swaps after payment detection
4. Monitoring of transaction confirmations
5. View completed swaps with transaction IDs

## How It Works

### Basic Version

1. **Asset Management**: The platform uses the `evrmore-rpc` library to interact with your Evrmore node and manage assets.
2. **Swap Offers**: Users can create offers to swap one asset for another, specifying the amounts.
3. **On-chain Transactions**: When executing a swap, the platform performs two on-chain transactions:
   - First, the taker sends the wanted asset to the offer owner
   - Then, the owner sends the offered asset to the taker
4. **Transaction Confirmation**: The platform monitors transaction confirmations to ensure swaps are completed securely.
5. **Data Persistence**: Swap offers are stored in a JSON file (`swap_offers.json`).
6. **Interactive UI**: The platform provides a user-friendly console interface using the `rich` library.

### Real-time Version

In addition to the basic functionality:

1. **WebSocket Connection**: Establishes a WebSocket connection to the Evrmore node for real-time updates.
2. **ZMQ Notifications**: Listens for ZMQ notifications about new transactions and blocks.
3. **Transaction Monitoring**: Automatically checks transactions for asset transfers related to swap offers.
4. **Automatic Offer Matching**: Identifies compatible swap offers and notifies users.
5. **Automatic Swap Completion**: After detecting a payment transaction, automatically completes the swap by sending the offered asset.

## Transaction Flow

The asset swap platform implements a secure transaction flow:

1. **Offer Creation**: User A creates an offer to swap Asset X for Asset Y
2. **Offer Discovery**: User B discovers the offer and decides to take it
3. **Payment Transaction**: User B sends Asset Y to User A (first on-chain transaction)
4. **Payment Confirmation**: The platform waits for the payment transaction to be confirmed
5. **Asset Transfer**: User A (or the platform automatically) sends Asset X to User B (second on-chain transaction)
6. **Swap Completion**: The offer is marked as completed with both transaction IDs recorded

## Learning Points

This example demonstrates:

1. How easy it is to build DeFi applications with the `evrmore-rpc` library
2. The power of combining synchronous and asynchronous APIs
3. How to use WebSockets for real-time blockchain monitoring
4. How to process ZMQ notifications for transaction and block events
5. Implementing secure on-chain transaction flows
6. Monitoring transaction confirmations for security
7. Building user-friendly interfaces for blockchain applications

## Next Steps

After understanding this example, you might want to:

1. Add a web interface using a framework like Flask or FastAPI
2. Implement more sophisticated trading features like partial fills or auctions
3. Add user authentication and multiple wallet support
4. Implement a decentralized order book using Evrmore's messaging capabilities
5. Create a mobile app that connects to this platform

## Security Considerations

This example is for educational purposes. In a production environment, you would need to:

1. Implement proper error handling for network issues and transaction failures
2. Add more robust security measures for user authentication
3. Consider using multisignature transactions for added security
4. Implement rate limiting and other anti-abuse measures
5. Add comprehensive logging and monitoring 