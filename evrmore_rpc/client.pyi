"""
Ultra-minimal stub file for EvrmoreClient - VS CODE OPTIMIZED
Only shows Evrmore RPC commands in intellisense.
"""

from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

# This is a special class that only defines the RPC methods
class EvrmoreClient:
    """Evrmore RPC Client."""
    
    # ===== ADDRESSINDEX METHODS =====
    
    def getaddressbalance(self, addresses: List[str]) -> Dict[str, int]:
        """Get the balance for addresses."""
        pass
    
    def getaddressdeltas(self, addresses: List[str], start: Optional[int] = None, end: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all changes for an address."""
        pass
    
    def getaddressmempool(self, addresses: List[str]) -> List[Dict[str, Any]]:
        """Get all mempool deltas for an address."""
        pass
    
    def getaddresstxids(self, addresses: List[str], start: Optional[int] = None, end: Optional[int] = None) -> List[str]:
        """Get all txids for an address."""
        pass
    
    def getaddressutxos(self, addresses: List[str], chainInfo: bool = False) -> List[Dict[str, Any]]:
        """Get all unspent outputs for an address."""
        pass
    
    # ===== BLOCKCHAIN METHODS =====
    
    def clearmempool(self) -> None:
        """Removes all transaction from the mempool."""
        pass
    
    def decodeblock(self, blockhex: str) -> Dict[str, Any]:
        """Decode a hex-encoded block."""
        pass
    
    def getbestblockhash(self) -> str: 
        """Get the hash of the best (tip) block in the most-work fully-validated chain."""
        pass
    
    def getblock(self, blockhash: str, verbosity: int = 1) -> Any: 
        """Get block data for a specific block hash."""
        pass
    
    def getblockchaininfo(self) -> Dict[str, Any]: 
        """Returns an object containing various state info regarding blockchain processing."""
        pass
    
    def getblockcount(self) -> int: 
        """Returns the height of the most-work fully-validated chain."""
        pass
    
    def getblockhash(self, height: int) -> str: 
        """Returns hash of block in best-block-chain at height provided."""
        pass
    
    def getblockhashes(self, timestamp: int, blockhash: Optional[str] = None) -> List[str]:
        """Returns array of hashes of blocks within the timestamp range provided."""
        pass
    
    def getblockheader(self, blockhash: str, verbose: bool = True) -> Any: 
        """Get block header data for a specific block hash."""
        pass
    
    def getchaintips(self) -> List[Dict[str, Any]]: 
        """Return information about all known tips in the block tree."""
        pass
    
    def getchaintxstats(self, nblocks: Optional[int] = None, blockhash: Optional[str] = None) -> Dict[str, Any]:
        """Compute statistics about the total number and rate of transactions in the chain."""
        pass
    
    def getdifficulty(self) -> float: 
        """Returns the proof-of-work difficulty as a multiple of the minimum difficulty."""
        pass
    
    def getmempoolancestors(self, txid: str, verbose: bool = False) -> Any:
        """If txid is in the mempool, returns all in-mempool ancestors."""
        pass
    
    def getmempooldescendants(self, txid: str, verbose: bool = False) -> Any:
        """If txid is in the mempool, returns all in-mempool descendants."""
        pass
    
    def getmempoolentry(self, txid: str) -> Dict[str, Any]:
        """Returns mempool data for given transaction."""
        pass
    
    def getmempoolinfo(self) -> Dict[str, Any]: 
        """Returns details on the active state of the TX memory pool."""
        pass
    
    def getrawmempool(self, verbose: bool = False) -> Any: 
        """Returns all transaction ids in memory pool as a json array of string transaction ids."""
        pass
    
    def getspentinfo(self, txid: str, index: int) -> Dict[str, Any]:
        """Returns the txid and index where an output is spent."""
        pass
    
    def gettxout(self, txid: str, n: int, include_mempool: bool = True) -> Any: 
        """Returns details about an unspent transaction output."""
        pass
    
    def gettxoutproof(self, txids: List[str], blockhash: Optional[str] = None) -> str:
        """Returns a hex-encoded proof that 'txid' was included in a block."""
        pass
    
    def gettxoutsetinfo(self) -> Dict[str, Any]: 
        """Returns statistics about the unspent transaction output set."""
        pass
    
    def preciousblock(self, blockhash: str) -> None:
        """Treats a block as if it were received before others with the same work."""
        pass
    
    def pruneblockchain(self, height: int) -> int:
        """Prune blockchain up to specified height or timestamp."""
        pass
    
    def savemempool(self) -> None:
        """Dumps the mempool to disk."""
        pass
    
    def verifychain(self, checklevel: int = 3, nblocks: int = 6) -> bool: 
        """Verifies blockchain database."""
        pass
    
    def verifytxoutproof(self, proof: str) -> List[str]:
        """Verifies that a proof points to a transaction in a block."""
        pass
    
    # ===== ASSET METHODS =====
    
    def getassetdata(self, asset_name: str) -> Dict[str, Any]: 
        """Returns asset data for a specific asset."""
        pass
    
    def getcacheinfo(self) -> Dict[str, Any]: 
        """Returns information about the asset cache."""
        pass
    
    def getsnapshot(self, asset_name: str, block_height: int) -> Dict[str, Any]:
        """Get a snapshot of asset ownership."""
        pass
    
    def listaddressesbyasset(self, asset_name: str, onlytotal: bool = False, count: int = 100, start: int = 0) -> Any:
        """List all addresses that own a specific asset."""
        pass
    
    def listassetbalancesbyaddress(self, address: str, onlytotal: bool = False, count: int = 100, start: int = 0) -> Any:
        """List all asset balances for a specific address."""
        pass
    
    def listassets(self, asset: str = "*", verbose: bool = False, count: int = 100, start: int = 0) -> Any: 
        """Returns a list of all assets."""
        pass
    
    def listmyassets(self, asset: str = "*", verbose: bool = False, count: int = 100, start: int = 0, confs: int = 0) -> Any: 
        """Returns a list of all asset that are owned by this wallet."""
        pass
    
    def purgesnapshot(self, asset_name: str, block_height: int) -> None:
        """Purge a snapshot."""
        pass
    
    def issue(self, asset_name: str, qty: Union[int, float, Decimal], to_address: Optional[str] = None, 
              change_address: Optional[str] = None, units: int = 0, reissuable: bool = True, 
              has_ipfs: bool = False, ipfs_hash: Optional[str] = None) -> str: 
        """Issue an asset, subasset or unique asset."""
        pass
    
    def issuequalifierasset(self, asset_name: str, qty: Union[int, float, Decimal], to_address: Optional[str] = None,
                           change_address: Optional[str] = None, has_ipfs: bool = False, 
                           ipfs_hash: Optional[str] = None) -> str: 
        """Issue a qualifier asset."""
        pass
    
    def issuerestrictedasset(self, asset_name: str, qty: Union[int, float, Decimal], verifier: str, 
                             to_address: str, change_address: Optional[str] = None, units: int = 0, 
                             reissuable: bool = True, has_ipfs: bool = False, 
                             ipfs_hash: Optional[str] = None) -> str: 
        """Issue a restricted asset."""
        pass
    
    def issueunique(self, root_name: str, asset_tags: List[str], ipfs_hashes: Optional[List[str]] = None,
                   to_address: Optional[str] = None, change_address: Optional[str] = None) -> str: 
        """Issue unique assets."""
        pass
    
    def reissue(self, asset_name: str, qty: Union[int, float, Decimal], to_address: str, 
               change_address: Optional[str] = None, reissuable: bool = True, 
               new_units: int = -1, new_ipfs: Optional[str] = None) -> str: 
        """Reissue an existing asset."""
        pass
    
    def reissuerestrictedasset(self, asset_name: str, qty: Union[int, float, Decimal], to_address: str,
                              change_verifier: bool = False, new_verifier: Optional[str] = None,
                              change_address: Optional[str] = None, new_units: int = -1,
                              reissuable: bool = True, new_ipfs: Optional[str] = None) -> str: 
        """Reissue a restricted asset."""
        pass
    
    def transfer(self, asset_name: str, qty: Union[int, float, Decimal], to_address: str, 
                message: Optional[str] = None, expire_time: Optional[int] = None,
                change_address: Optional[str] = None, asset_change_address: Optional[str] = None) -> str: 
        """Transfer an asset."""
        pass
    
    def transferfromaddress(self, asset_name: str, from_address: str, qty: Union[int, float, Decimal], 
                           to_address: str, message: Optional[str] = None, expire_time: Optional[int] = None,
                           evr_change_address: Optional[str] = None, asset_change_address: Optional[str] = None) -> str:
        """Transfer an asset from a specific address."""
        pass
    
    def transferfromaddresses(self, asset_name: str, from_addresses: List[str], qty: Union[int, float, Decimal],
                             to_address: str, message: Optional[str] = None, expire_time: Optional[int] = None,
                             evr_change_address: Optional[str] = None, asset_change_address: Optional[str] = None) -> str:
        """Transfer an asset from multiple addresses."""
        pass
    
    def transferqualifier(self, qualifier_name: str, qty: Union[int, float, Decimal], to_address: str,
                         change_address: Optional[str] = None, message: Optional[str] = None,
                         expire_time: Optional[int] = None) -> str:
        """Transfer a qualifier asset."""
        pass
    
    # ===== NETWORK METHODS =====
    
    def getnetworkinfo(self) -> Dict[str, Any]: 
        """Returns an object containing various state info regarding P2P networking."""
        pass
    
    def getpeerinfo(self) -> List[Dict[str, Any]]: 
        """Returns data about each connected network node as a json array of objects."""
        pass
    
    def getconnectioncount(self) -> int: 
        """Returns the number of connections to other nodes."""
        pass
    
    def ping(self) -> None: 
        """Requests that a ping be sent to all other nodes, to measure ping time."""
        pass
    
    def addnode(self, node: str, command: str) -> None:
        """Attempts to add or remove a node from the addnode list."""
        pass
    
    def clearbanned(self) -> None:
        """Clear all banned IPs."""
        pass
    
    def disconnectnode(self, address: Optional[str] = None, nodeid: Optional[int] = None) -> None:
        """Immediately disconnects from the specified peer node."""
        pass
    
    def getaddednodeinfo(self, node: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns information about the given added node, or all added nodes."""
        pass
    
    def getnettotals(self) -> Dict[str, Any]:
        """Returns information about network traffic."""
        pass
    
    def listbanned(self) -> List[Dict[str, Any]]:
        """List all banned IPs/Subnets."""
        pass
    
    def setban(self, subnet: str, command: str, bantime: int = 0, absolute: bool = False) -> None:
        """Attempts to add or remove an IP/Subnet from the banned list."""
        pass
    
    def setnetworkactive(self, state: bool) -> bool:
        """Disable/enable all p2p network activity."""
        pass
    
    # ===== CONTROL METHODS =====
    
    def getinfo(self) -> Dict[str, Any]:
        """Returns an object containing various state info."""
        pass
    
    def getmemoryinfo(self, mode: str = "stats") -> Dict[str, Any]:
        """Returns an object containing information about memory usage."""
        pass
    
    def getrpcinfo(self) -> Dict[str, Any]:
        """Returns details of the RPC server."""
        pass
    
    def help(self, command: Optional[str] = None) -> str:
        """List all commands, or get help for a specified command."""
        pass
    
    def stop(self) -> str:
        """Stop Evrmore server."""
        pass
    
    def uptime(self) -> int:
        """Returns the total uptime of the server."""
        pass
    
    # ===== GENERATING METHODS =====
    
    def generate(self, nblocks: int, maxtries: int = 1000000) -> List[str]:
        """Mine blocks immediately."""
        pass
    
    def generatetoaddress(self, nblocks: int, address: str, maxtries: int = 1000000) -> List[str]:
        """Mine blocks immediately to a specified address."""
        pass
    
    def getgenerate(self) -> bool:
        """Return if the server is set to generate coins or not."""
        pass
    
    def setgenerate(self, generate: bool, genproclimit: Optional[int] = None) -> None:
        """Set generation on or off."""
        pass
    
    # ===== MINING METHODS =====
    
    def getblocktemplate(self, template_request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns data needed to construct a block to work on."""
        pass
    
    def getevrprogpowhash(self, header_hash: str, mix_hash: str, nonce: int, height: int, target: str) -> str:
        """Returns the EVR ProgPoW hash for the given parameters."""
        pass
    
    def getmininginfo(self) -> Dict[str, Any]:
        """Returns a json object containing mining-related information."""
        pass
    
    def getnetworkhashps(self, nblocks: int = 120, height: int = -1) -> float:
        """Returns the estimated network hashes per second."""
        pass
    
    def pprpcsb(self, header_hash: str, mix_hash: str, nonce: str) -> Dict[str, Any]:
        """Checks if the given parameters create a valid block."""
        pass
    
    def prioritisetransaction(self, txid: str, dummy_value: int, fee_delta: int) -> bool:
        """Accepts the transaction into mined blocks at a higher (or lower) priority."""
        pass
    
    def submitblock(self, hexdata: str, dummy: Optional[str] = None) -> Optional[str]:
        """Attempts to submit new block to network."""
        pass
    
    # ===== RAWTRANSACTIONS METHODS =====
    
    def combinerawtransaction(self, txs: List[str]) -> str:
        """Combine multiple partially signed transactions into one transaction."""
        pass
    
    def createrawtransaction(self, inputs: List[Dict[str, Any]], outputs: Dict[str, Any], locktime: int = 0, replaceable: bool = False) -> str:
        """Create a transaction spending the given inputs and creating new outputs."""
        pass
    
    def decoderawtransaction(self, hexstring: str) -> Dict[str, Any]:
        """Return a JSON object representing the serialized, hex-encoded transaction."""
        pass
    
    def decodescript(self, hexstring: str) -> Dict[str, Any]:
        """Decode a hex-encoded script."""
        pass
    
    def fundrawtransaction(self, hexstring: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add inputs to a transaction until it has enough in value to meet its out value."""
        pass
    
    def getrawtransaction(self, txid: str, verbose: bool = False) -> Any:
        """Return the raw transaction data."""
        pass
    
    def sendrawtransaction(self, hexstring: str, allowhighfees: bool = False) -> str:
        """Submits raw transaction (serialized, hex-encoded) to local node and network."""
        pass
    
    def signrawtransaction(self, hexstring: str, prevtxs: Optional[List[Dict[str, Any]]] = None, 
                          privkeys: Optional[List[str]] = None, sighashtype: str = "ALL") -> Dict[str, Any]:
        """Sign inputs for raw transaction (serialized, hex-encoded)."""
        pass
    
    def testmempoolaccept(self, rawtxs: List[str], allowhighfees: bool = False) -> List[Dict[str, Any]]:
        """Returns result of mempool acceptance tests indicating if raw transaction would be accepted by mempool."""
        pass
    
    # ===== UTIL METHODS =====
    
    def createmultisig(self, nrequired: int, keys: List[str]) -> Dict[str, Any]:
        """Creates a multi-signature address with n signature of m keys required."""
        pass
    
    def estimatefee(self, nblocks: int) -> float:
        """Estimates the approximate fee per kilobyte needed for a transaction to begin confirmation within nblocks blocks."""
        pass
    
    def estimatesmartfee(self, conf_target: int, estimate_mode: str = "CONSERVATIVE") -> Dict[str, Any]:
        """Estimates the approximate fee per kilobyte needed for a transaction to begin confirmation within conf_target blocks."""
        pass
    
    def signmessagewithprivkey(self, privkey: str, message: str) -> str:
        """Sign a message with the private key of an address."""
        pass
    
    def validateaddress(self, address: str) -> Dict[str, Any]:
        """Return information about the given evrmore address."""
        pass
    
    def verifymessage(self, address: str, signature: str, message: str) -> bool:
        """Verify a signed message."""
        pass
    
    # ===== WALLET METHODS =====
    
    def abandontransaction(self, txid: str) -> None: 
        """Mark in-wallet transaction as abandoned."""
        pass
    
    def abortrescan(self) -> bool:
        """Stops current wallet rescan."""
        pass
    
    def addmultisigaddress(self, nrequired: int, keys: List[str], account: str = "") -> str:
        """Add a nrequired-to-sign multisignature address to the wallet."""
        pass
    
    def addwitnessaddress(self, address: str) -> str:
        """Add a witness address for a script (with pubkey or redeemscript known)."""
        pass
    
    def backupwallet(self, destination: str) -> None:
        """Safely copies current wallet file to destination filename."""
        pass
    
    def dumpprivkey(self, address: str) -> str:
        """Reveals the private key corresponding to 'address'."""
        pass
    
    def dumpwallet(self, filename: str) -> str:
        """Dumps all wallet keys in a human-readable format to a server-side file."""
        pass
    
    def encryptwallet(self, passphrase: str) -> str:
        """Encrypts the wallet with 'passphrase'."""
        pass
    
    def getaccount(self, address: str) -> str:
        """DEPRECATED. Returns the account associated with the given address."""
        pass
    
    def getaccountaddress(self, account: str) -> str:
        """DEPRECATED. Returns the current Evrmore address for receiving payments to this account."""
        pass
    
    def getaddressesbyaccount(self, account: str) -> List[str]:
        """DEPRECATED. Returns the list of addresses for the given account."""
        pass
    
    def getbalance(self, account: str = "*", minconf: int = 1, include_watchonly: bool = False) -> float: 
        """Returns the server's total available balance."""
        pass
    
    def getmasterkeyinfo(self) -> Dict[str, Any]:
        """Get wallet HD master key information."""
        pass
    
    def getmywords(self, account: Optional[str] = None) -> str:
        """Get the BIP39 mnemonic for this wallet if HD and mnemonic is available."""
        pass
    
    def getnewaddress(self, account: str = "") -> str: 
        """Returns a new Evrmore address for receiving payments."""
        pass
    
    def getrawchangeaddress(self) -> str: 
        """Returns a new Evrmore address, for receiving change."""
        pass
    
    def getreceivedbyaccount(self, account: str, minconf: int = 1) -> float:
        """DEPRECATED. Returns the total amount received by addresses with <account>."""
        pass
    
    def getreceivedbyaddress(self, address: str, minconf: int = 1) -> float: 
        """Returns the total amount received by the given address."""
        pass
    
    def gettransaction(self, txid: str, include_watchonly: bool = False) -> Dict[str, Any]: 
        """Get detailed information about in-wallet transaction."""
        pass
    
    def getunconfirmedbalance(self) -> float: 
        """Returns the server's total unconfirmed balance."""
        pass
    
    def getwalletinfo(self) -> Dict[str, Any]: 
        """Returns an object containing various wallet state info."""
        pass
    
    def importaddress(self, address: str, label: str = "", rescan: bool = True, p2sh: bool = False) -> None:
        """Adds an address or script to the wallet."""
        pass
    
    def importmulti(self, requests: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Import addresses/scripts (with private or public keys, redeem script), rescanning blockchain."""
        pass
    
    def importprivkey(self, privkey: str, label: str = "", rescan: bool = True) -> None:
        """Adds a private key to your wallet."""
        pass
    
    def importprunedfunds(self, rawtransaction: str, txoutproof: str) -> None:
        """Imports funds without rescan."""
        pass
    
    def importpubkey(self, pubkey: str, label: str = "", rescan: bool = True) -> None:
        """Adds a public key to your wallet."""
        pass
    
    def importwallet(self, filename: str) -> None:
        """Imports keys from a wallet dump file."""
        pass
    
    def keypoolrefill(self, newsize: int = 100) -> None:
        """Fills the keypool."""
        pass
    
    def listaccounts(self, minconf: int = 1, include_watchonly: bool = False) -> Dict[str, float]:
        """DEPRECATED. Returns Object that has account names as keys, account balances as values."""
        pass
    
    def listaddressgroupings(self) -> List[List[List[Any]]]: 
        """Lists groups of addresses which have had their common ownership made public by common use as inputs or as the resulting change in past transactions."""
        pass
    
    def listlockunspent(self) -> List[Dict[str, Any]]:
        """Returns list of temporarily unspendable outputs."""
        pass
    
    def listreceivedbyaccount(self, minconf: int = 1, include_empty: bool = False, include_watchonly: bool = False) -> List[Dict[str, Any]]:
        """DEPRECATED. List balances by account."""
        pass
    
    def listreceivedbyaddress(self, minconf: int = 1, include_empty: bool = False, include_watchonly: bool = False) -> List[Dict[str, Any]]:
        """List balances by receiving address."""
        pass
    
    def listsinceblock(self, blockhash: Optional[str] = None, target_confirmations: int = 1, include_watchonly: bool = False, include_removed: bool = True) -> Dict[str, Any]:
        """Get all transactions in blocks since block [blockhash]."""
        pass
    
    def listtransactions(self, account: str = "*", count: int = 10, skip: int = 0, include_watchonly: bool = False) -> List[Dict[str, Any]]:
        """Returns up to 'count' most recent transactions."""
        pass
    
    def listunspent(self, minconf: int = 1, maxconf: int = 9999999, 
                   addresses: Optional[List[str]] = None, 
                   include_unsafe: bool = True, 
                   query_options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]: 
        """Returns array of unspent transaction outputs."""
        pass
    
    def listwallets(self) -> List[str]:
        """Returns a list of currently loaded wallets."""
        pass
    
    def lockunspent(self, unlock: bool, transactions: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Updates list of temporarily unspendable outputs."""
        pass
    
    def move(self, fromaccount: str, toaccount: str, amount: Union[int, float, Decimal], minconf: int = 1, comment: str = "") -> bool:
        """DEPRECATED. Move a specified amount from one account in your wallet to another."""
        pass
    
    def removeprunedfunds(self, txid: str) -> None:
        """Deletes the specified transaction from the wallet."""
        pass
    
    def rescanblockchain(self, start_height: Optional[int] = None, stop_height: Optional[int] = None) -> Dict[str, int]:
        """Rescan the local blockchain for wallet related transactions."""
        pass
    
    def sendfrom(self, fromaccount: str, toaddress: str, amount: Union[int, float, Decimal], minconf: int = 1, comment: str = "", comment_to: str = "") -> str:
        """Send an amount from an account to a evrmore address."""
        pass
    
    def sendfromaddress(self, from_address: str, to_address: str, amount: Union[int, float, Decimal], 
                       comment: str = "", comment_to: str = "", subtractfeefromamount: bool = False,
                       replaceable: bool = False, conf_target: int = 1, estimate_mode: str = "UNSET") -> str:
        """Send an amount from a specific address to a evrmore address."""
        pass
    
    def sendmany(self, fromaccount: str, amounts: Dict[str, Union[int, float, Decimal]], minconf: int = 1, comment: str = "", subtractfeefrom: Optional[List[str]] = None, replaceable: bool = False, conf_target: int = 1, estimate_mode: str = "UNSET") -> str:
        """Send multiple times. Amounts are double-precision floating point numbers."""
        pass
    
    def sendtoaddress(self, address: str, amount: Union[int, float, Decimal], 
                     comment: str = "", comment_to: str = "", 
                     subtractfeefromamount: bool = False, 
                     replaceable: bool = False, 
                     conf_target: int = 1, 
                     estimate_mode: str = "UNSET") -> str: 
        """Send an amount to a given address."""
        pass
    
    def setaccount(self, address: str, account: str) -> None:
        """DEPRECATED. Sets the account associated with the given address."""
        pass
    
    def settxfee(self, amount: Union[int, float, Decimal]) -> bool:
        """Set the transaction fee per kB for this wallet."""
        pass
    
    def signmessage(self, address: str, message: str) -> str:
        """Sign a message with the private key of an address."""
        pass
    
    def walletlock(self) -> None:
        """Removes the wallet encryption key from memory, locking the wallet."""
        pass
    
    def walletpassphrase(self, passphrase: str, timeout: int) -> None:
        """Stores the wallet decryption key in memory for 'timeout' seconds."""
        pass
    
    def walletpassphrasechange(self, oldpassphrase: str, newpassphrase: str) -> None:
        """Changes the wallet passphrase from 'oldpassphrase' to 'newpassphrase'."""
        pass
    
    # ===== MESSAGING METHODS =====
    
    def clearmessages(self) -> None: 
        """Clear all locally stored messages."""
        pass
    
    def sendmessage(self, channel_name: str, ipfs_hash: str, expire_time: Optional[int] = None) -> str: 
        """Send a message to a channel."""
        pass
    
    def subscribetochannel(self, channel_name: str) -> None: 
        """Subscribe to a message channel."""
        pass
    
    def unsubscribefromchannel(self, channel_name: str) -> None: 
        """Unsubscribe from a message channel."""
        pass
    
    def viewallmessagechannels(self) -> List[str]: 
        """View all message channels."""
        pass
    
    def viewallmessages(self) -> List[Dict[str, Any]]: 
        """View all messages."""
        pass
    
    def viewmyrestrictedaddresses(self) -> Dict[str, List[str]]: 
        """View all restricted addresses owned by this wallet."""
        pass
    
    def viewmytaggedaddresses(self) -> Dict[str, List[str]]: 
        """View all tagged addresses owned by this wallet."""
        pass
    
    # ===== RESTRICTED ASSET METHODS =====
    
    def addtagtoaddress(self, tag_name: str, to_address: str, 
                       change_address: Optional[str] = None, 
                       asset_data: Optional[str] = None) -> str: 
        """Add a tag to an address."""
        pass
    
    def checkaddressrestriction(self, address: str, restricted_name: str) -> bool: 
        """Check if an address has a restriction."""
        pass
    
    def checkaddresstag(self, address: str, tag_name: str) -> bool: 
        """Check if an address has a tag."""
        pass
    
    def checkglobalrestriction(self, restricted_name: str) -> bool: 
        """Check if a global restriction exists."""
        pass
    
    def freezeaddress(self, asset_name: str, address: str, 
                     change_address: Optional[str] = None, 
                     asset_data: Optional[str] = None) -> str: 
        """Freeze an address for a restricted asset."""
        pass
    
    def freezerestrictedasset(self, asset_name: str, 
                             change_address: Optional[str] = None, 
                             asset_data: Optional[str] = None) -> str: 
        """Freeze a restricted asset globally."""
        pass
    
    def getverifierstring(self, restricted_name: str) -> str: 
        """Get the verifier string for a restricted asset."""
        pass
    
    def isvalidverifierstring(self, verifier_string: str) -> bool: 
        """Check if a verifier string is valid."""
        pass
    
    def listaddressesfortag(self, tag_name: str) -> List[str]: 
        """List addresses that have a specific tag."""
        pass
    
    def listaddressrestrictions(self, address: str) -> Dict[str, bool]: 
        """List restrictions for an address."""
        pass
    
    def listglobalrestrictions(self) -> Dict[str, bool]: 
        """List all global restrictions."""
        pass
    
    def listtagsforaddress(self, address: str) -> List[str]: 
        """List all tags for an address."""
        pass
    
    def removetagfromaddress(self, tag_name: str, to_address: str, 
                            change_address: Optional[str] = None, 
                            asset_data: Optional[str] = None) -> str: 
        """Remove a tag from an address."""
        pass
    
    def unfreezeaddress(self, asset_name: str, address: str, 
                       change_address: Optional[str] = None, 
                       asset_data: Optional[str] = None) -> str: 
        """Unfreeze an address for a restricted asset."""
        pass
    
    def unfreezerestrictedasset(self, asset_name: str, 
                               change_address: Optional[str] = None, 
                               asset_data: Optional[str] = None) -> str: 
        """Unfreeze a restricted asset globally."""
        pass
    
    # ===== SNAPSHOT METHODS =====
    
    def cancelsnapshotrequest(self, asset_name: str, block_height: int) -> None: 
        """Cancel a snapshot request."""
        pass
    
    def distributereward(self, asset_name: str, snapshot_height: int, distribution_asset_name: str, 
                        gross_distribution_amount: Union[int, float, Decimal], 
                        exception_addresses: Optional[List[str]] = None, 
                        change_address: Optional[str] = None, 
                        dry_run: bool = False) -> Dict[str, Any]: 
        """Distribute rewards based on a snapshot."""
        pass
    
    def getdistributestatus(self, asset_name: str, snapshot_height: int, distribution_asset_name: str, 
                           gross_distribution_amount: Union[int, float, Decimal], 
                           exception_addresses: Optional[List[str]] = None) -> Dict[str, Any]: 
        """Get the status of a distribution."""
        pass
    
    def getsnapshotrequest(self, asset_name: str, block_height: int) -> Dict[str, Any]: 
        """Get a snapshot request."""
        pass
    
    def listsnapshotrequests(self, asset_names: Optional[List[str]] = None, 
                            block_heights: Optional[List[int]] = None) -> List[Dict[str, Any]]: 
        """List all snapshot requests."""
        pass
    
    def requestsnapshot(self, asset_name: str, block_height: int) -> None: 
        """Request a snapshot of asset ownership."""
        pass
    
    # Core methods - these are needed but kept at the end to prioritize RPC commands
    def reset(self) -> None: 
        """Reset the client state."""
        pass
    
    def close(self) -> None: 
        """Close the client and release resources."""
        pass 