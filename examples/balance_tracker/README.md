# Balance Tracker Example

This directory contains an example implementation of a balance tracker for NFT exchange integration using the `evrmore-rpc` package.

## Features

- Complete SQLite database integration for tracking balances and orders
- RESTful API example with FastAPI for NFT exchange backend
- Transaction and order status tracking with real-time updates
- Advanced order and transaction lifecycle management

## Running the Example

To run the balance tracker example:

```bash
python examples/balance_tracker/main.py
```

## Requirements

This example requires additional dependencies:

```bash
pip install evrmore-rpc[full]
# or
pip install fastapi uvicorn sqlalchemy
```

## API Endpoints

The balance tracker exposes the following API endpoints:

- `GET /balances`: Get all balances
- `GET /balances/{address}`: Get balance for a specific address
- `GET /orders`: Get all orders
- `POST /orders`: Create a new order
- `GET /orders/{order_id}`: Get a specific order
- `PUT /orders/{order_id}`: Update an order
- `DELETE /orders/{order_id}`: Delete an order 