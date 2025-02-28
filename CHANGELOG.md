# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full WebSockets support:
  - `EvrmoreWebSocketClient` for connecting to WebSocket servers
  - `EvrmoreWebSocketServer` for broadcasting blockchain events
  - Comprehensive data models for WebSocket messages
  - Real-time block and transaction notifications
  - Interactive dashboard example
  - WebSocket simulator for testing
  - Unit tests for WebSockets functionality
- Full async/await support via new EvrmoreAsyncRPCClient
- Parallel request execution with asyncio.gather
- Async context manager support
- Examples demonstrating async usage
- Tests for async functionality
- Documentation for async API
- New `balance_tracker` example for NFT exchange integration:
  - Complete SQLite database integration for tracking balances and orders
  - RESTful API example with FastAPI for NFT exchange backend
  - Transaction and order status tracking with real-time updates
- Advanced blockchain analytics capabilities:
  - Transaction pattern recognition system for identifying specific transaction types
  - Statistical anomaly detection for unusual blockchain activities
  - Machine learning integration for transaction analysis (via scikit-learn)
  - Z-score based transaction value analysis
- Real-time WebSocket support for live dashboard updates
- Comprehensive pattern matching:
  - Asset type pattern detection
  - Value-based transaction filtering
  - Address pattern recognition
  - Multi-input/output analysis
- Interactive rich console visualization with live updates
- Historical blockchain data analysis for establishing statistical baselines
- Advanced order and transaction lifecycle management

## [1.2.1] - 2025-03-02

### Added
- Comprehensive documentation with MkDocs
- Improved WebSockets support
- Enhanced asset swap platform examples
- Fixed package distribution issues

### Changed
- Updated dependencies to latest versions
- Improved error handling in WebSocket connections
- Better documentation for all components

## [1.2.0] - 2025-03-01

### Added
- WebSockets support for real-time blockchain events:
  - Client for connecting to WebSocket servers
  - Server for broadcasting blockchain events
  - Data models for WebSocket messages
  - Examples demonstrating WebSockets usage
  - Interactive dashboard for monitoring blockchain activity
  - WebSocket simulator for testing without a real node
- Enhanced async/await support:
  - Improved error handling and reconnection logic
  - Better performance with parallel requests
  - More comprehensive examples
- Updated documentation with WebSockets examples
- Improved test coverage

### Changed
- Updated dependencies to latest versions
- Improved package organization with dedicated directories for components
- Enhanced error handling and logging
- Better type hints and docstrings

## [1.1.0] - 2025-02-19

### Added
- ZMQ support for real-time blockchain notifications
- New examples demonstrating ZMQ and RPC usage:
  - Blockchain explorer
  - Asset monitor
  - Wallet tracker
  - Network monitor
  - Reward distributor
- Improved error handling and logging
- Better type hints and docstrings
- Optional development dependencies

### Changed
- Updated dependencies to latest versions
- Improved async/await support
- Enhanced documentation with ZMQ examples
- Better package organization

## [1.0.2] - 2025-02-18

### Changed
- Renamed package to `evrmore-rpc` on PyPI while keeping `evrmore_rpc` as the Python module name
- Improved ZMQ module with better documentation and examples
- Enhanced error handling and logging
- Updated dependencies to latest versions

### Added
- Comprehensive ZMQ module documentation
- Integration examples for blockchain explorer and wallet monitoring
- Better type hints and docstrings
- Command-line interface for ZMQ testing

### Fixed
- ZMQ notification handling and validation
- Configuration loading edge cases
- Error messages and logging format

## [1.0.1] - 2025-02-16

### Added
- Initial release with basic RPC functionality
- ZMQ support for real-time notifications
- Comprehensive model validation
- Basic documentation 