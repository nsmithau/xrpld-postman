#!/usr/bin/env python3
"""Generate the XRPLD & Clio Postman collection.

Every request targets the JSON-RPC interface and sends `api_version: 2`
inside the params object. Edit the METHOD definitions below and re-run:

    python3 build.py

Output: xrpld_postman_collection.json (Postman Collection v2.1).
"""
import json
from collections import OrderedDict

XRPLD_URL = "{{XRPLD_JSONRPC_URL}}"
CLIO_URL = "{{CLIO_JSONRPC_URL}}"
ADMIN_URL = "{{ADMIN_JSONRPC_URL}}"

# Per-network endpoints, used to generate Postman environment files.
NETWORKS = [
    ("Mainnet", "https://s1.ripple.com:51234/", "https://s2.ripple.com:51234/",
     "89a1e000-0000-4000-8000-000000000001"),
    ("Testnet", "https://s.altnet.rippletest.net:51234/", "https://clio.altnet.rippletest.net:51234/",
     "89a1e000-0000-4000-8000-000000000002"),
    ("Devnet", "https://s.devnet.rippletest.net:51234/", "https://clio.devnet.rippletest.net:51234/",
     "89a1e000-0000-4000-8000-000000000003"),
]
ADMIN_DEFAULT = "http://localhost:5005/"  # admin methods only work on a node you operate

# Well-known example values reused across requests.
ACC = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"          # a funded mainnet account
ISSUER = "rP9jPyP5kyvFRb6ZiRghAGw5u8SGAmU4bd"
NFT_ID = "000B013A95F14B0044F78A264E41713C64B5F89242540EE208C3098E00000D65"  # 64-hex NFTokenID
VAULT_ID = "9E48171960CD9F62C3A7B6559315A510AE544C3F51E02947B5D4DAC8AA66C3BA"  # Ledger Entry ID
MPT_ISSUANCE_ID = "05EECEBE97A7D635DE2393068691A015FED5A89AD203F5AA"  # MPTokenIssuance ID (48-hex)


def body(method, params):
    """Build a JSON-RPC request body with api_version 2 injected."""
    p = OrderedDict()
    p["api_version"] = 2
    for k, v in params.items():
        p[k] = v
    return OrderedDict([("method", method), ("params", [p])])


def request(name, method, params, description, clio=False):
    url = CLIO_URL if clio else XRPLD_URL
    raw = json.dumps(body(method, params), indent=2)
    return OrderedDict([
        ("name", name),
        ("request", OrderedDict([
            ("method", "POST"),
            ("header", [OrderedDict([
                ("key", "Content-Type"),
                ("value", "application/json"),
            ])]),
            ("url", OrderedDict([
                ("raw", url),
                ("host", [url]),
            ])),
            ("description", description),
            ("body", OrderedDict([
                ("mode", "raw"),
                ("raw", raw),
                ("options", {"raw": {"language": "json"}}),
            ])),
        ])),
    ])


def folder(name, items, description=None):
    f = OrderedDict()
    f["name"] = name
    if description:
        f["description"] = description
    f["item"] = items
    return f


def retarget(items, url):
    """Point every request in a folder tree at a different URL variable."""
    for it in items:
        if "request" in it:
            it["request"]["url"]["raw"] = url
            it["request"]["url"]["host"] = [url]
        if "item" in it:
            retarget(it["item"], url)
    return items


def environment(name, xrpld_url, clio_url, env_id):
    """Build a Postman environment file for one network."""
    def val(key, value):
        return OrderedDict([
            ("key", key), ("value", value),
            ("type", "default"), ("enabled", True),
        ])
    return OrderedDict([
        ("id", env_id),
        ("name", f"XRPLD & Clio — {name}"),
        ("values", [
            val("XRPLD_JSONRPC_URL", xrpld_url),
            val("CLIO_JSONRPC_URL", clio_url),
            val("ADMIN_JSONRPC_URL", ADMIN_DEFAULT),
        ]),
        ("_postman_variable_scope", "environment"),
    ])


# --------------------------------------------------------------------------
# PUBLIC — Account Methods
# --------------------------------------------------------------------------
account_methods = [
    request("account_channels", "account_channels", {
        "account": ACC,
        "destination_account": ISSUER,
        "ledger_index": "validated",
    }, "Returns information about an account's Payment Channels, where the account is the channel's source."),
    request("account_currencies", "account_currencies", {
        "account": ACC,
        "ledger_index": "validated",
    }, "Retrieves the currencies an account can send or receive, based on its trust lines."),
    request("account_info", "account_info", {
        "account": ACC,
        "ledger_index": "current",
        "queue": True,
        "signer_lists": True,
    }, "Retrieves information about an account, its activity, and its XRP balance. "
       "(`queue` requires `ledger_index: current`.)"),
    request("account_lines", "account_lines", {
        "account": ACC,
        "ledger_index": "validated",
    }, "Returns information about an account's trust lines, including balances in all non-XRP currencies and assets."),
    request("account_nfts", "account_nfts", {
        "account": ACC,
        "ledger_index": "validated",
        "limit": 100,
    }, "Returns a list of NFToken objects for the specified account."),
    request("account_objects", "account_objects", {
        "account": ACC,
        "ledger_index": "validated",
        "type": "state",
        "limit": 10,
    }, "Returns the raw ledger objects owned by an account (trust lines, offers, escrows, signer lists, etc.)."),
    request("account_offers", "account_offers", {
        "account": ACC,
        "ledger_index": "validated",
    }, "Retrieves a list of outstanding offers made by an account as of a particular ledger version."),
    request("account_tx", "account_tx", {
        "account": ACC,
        "binary": False,
        "forward": False,
        "ledger_index_max": -1,
        "ledger_index_min": -1,
        "limit": 5,
    }, "Retrieves a list of transactions that involved the specified account."),
    request("gateway_balances", "gateway_balances", {
        "account": ISSUER,
        "ledger_index": "validated",
        "strict": True,
    }, "Calculates the total balances issued by a given account, optionally excluding operational addresses."),
    request("noripple_check", "noripple_check", {
        "account": ACC,
        "ledger_index": "current",
        "limit": 2,
        "role": "gateway",
        "transactions": True,
    }, "Provides recommended changes to an account's Default Ripple and No Ripple trust-line settings."),
]

# --------------------------------------------------------------------------
# PUBLIC — Ledger Methods
# --------------------------------------------------------------------------
ledger_methods = [
    request("ledger", "ledger", {
        "ledger_index": "validated",
        "transactions": False,
        "expand": False,
        "owner_funds": False,
    }, "Retrieves information about the public ledger. (The admin-only `accounts` and `full` "
       "fields are deprecated and intentionally omitted.)"),
    request("ledger_closed", "ledger_closed", {},
        "Returns the unique identifiers of the most recently closed ledger."),
    request("ledger_current", "ledger_current", {},
        "Returns the unique identifiers of the current in-progress ledger."),
    request("ledger_data", "ledger_data", {
        "ledger_index": "validated",
        "binary": True,
        "limit": 5,
    }, "Retrieves contents of the specified ledger, a page of ledger objects at a time."),
    request("ledger_entry", "ledger_entry", {
        "account_root": ACC,
        "ledger_index": "validated",
    }, "Returns a single ledger object in its raw format. This example fetches an AccountRoot; the method is polymorphic (offer, ripple_state, escrow, nft_page, amm, etc.)."),
    request("book_changes", "book_changes", {
        "ledger_index": "validated",
    }, "Returns a summary of the changes to order books (offer exchanges) that occurred within a single ledger version."),
]

# --------------------------------------------------------------------------
# PUBLIC — Transaction Methods
# --------------------------------------------------------------------------
transaction_methods = [
    request("submit", "submit", {
        "tx_blob": "1200002280000000240000001E61400000000000...REPLACE_WITH_SIGNED_BLOB",
    }, "Applies a signed transaction (tx_blob) and sends it to the network to be included in a future ledger."),
    request("submit_multisigned", "submit_multisigned", {
        "tx_json": {
            "Account": ACC,
            "Fee": "30000",
            "Flags": 0,
            "Sequence": 360,
            "SigningPubKey": "",
            "TransactionType": "TrustSet",
            "LimitAmount": {"currency": "USD", "issuer": ISSUER, "value": "100"},
            "Signers": [],
        },
    }, "Applies a multi-signed transaction and sends it to the network."),
    request("transaction_entry", "transaction_entry", {
        "tx_hash": "C53ECF838647FA5A4C780377025FEC7999AB4182590510CA461444B207AB74A9",
        "ledger_index": "validated",
    }, "Retrieves information about a single transaction from a specific ledger version."),
    request("tx", "tx", {
        "transaction": "C53ECF838647FA5A4C780377025FEC7999AB4182590510CA461444B207AB74A9",
        "binary": False,
    }, "Retrieves information about a single transaction. In api_version 2 the response wraps transaction fields under tx_json."),
    request("simulate", "simulate", {
        "tx_json": {
            "TransactionType": "Payment",
            "Account": ACC,
            "Destination": ISSUER,
            "Amount": "1000000",
        },
        "binary": False,
    }, "Executes a dry run of an (unsigned) transaction to preview its metadata and results without submitting it."),
]

# --------------------------------------------------------------------------
# PUBLIC — Path and Order Book Methods
# --------------------------------------------------------------------------
path_methods = [
    request("amm_info", "amm_info", {
        "asset": {"currency": "XRP"},
        "asset2": {"currency": "USD", "issuer": ISSUER},
        "ledger_index": "validated",
    }, "Returns information about an Automated Market Maker (AMM) instance. Specify either amm_account or both asset and asset2."),
    request("book_offers", "book_offers", {
        "taker_gets": {"currency": "XRP"},
        "taker_pays": {"currency": "USD", "issuer": ISSUER},
        "ledger_index": "validated",
        "limit": 10,
    }, "Retrieves a list of offers between two currencies (an order book), also known as the offer book."),
    request("deposit_authorized", "deposit_authorized", {
        "source_account": ACC,
        "destination_account": ISSUER,
        "ledger_index": "validated",
    }, "Checks whether one account is authorized to send payments directly to another (Deposit Authorization)."),
    request("nft_buy_offers", "nft_buy_offers", {
        "nft_id": NFT_ID,
        "ledger_index": "validated",
    }, "Returns a list of buy offers for a specified NFToken."),
    request("nft_sell_offers", "nft_sell_offers", {
        "nft_id": NFT_ID,
        "ledger_index": "validated",
    }, "Returns a list of sell offers for a specified NFToken."),
    request("ripple_path_find", "ripple_path_find", {
        "source_account": ACC,
        "destination_account": ISSUER,
        "destination_amount": {"currency": "USD", "issuer": ISSUER, "value": "0.001"},
        "ledger_index": "validated",
    }, "A simplified, single-shot version of the path_find method for finding payment paths (path_find itself is WebSocket-only)."),
]

# --------------------------------------------------------------------------
# PUBLIC — Payment Channel Methods
# --------------------------------------------------------------------------
paychan_methods = [
    request("channel_verify", "channel_verify", {
        "amount": "1000000",
        "channel_id": "5DB01B7FFED6B67E6B0414DED11E051D2EE2B7619CE0EAA6286D67A3A4D5BDB3",
        "public_key": "aB44YfzW24VDEJQ2UuLPV2PvqcPCSoLnL7y5M1EzhdW4LnK5xMS3",
        "signature": "304402204EF0AFB78AC23ED1C472E74F4299C0C21F1B21D07EFC0A3838A420F76D783A400220154FB11B6F54320666E4C36CA7F686C16A3A0456800BBC43746F34AF50290064",
    }, "Verifies a signature that can be used to redeem a specific amount from a payment channel."),
]

# --------------------------------------------------------------------------
# PUBLIC — Server Info Methods
# --------------------------------------------------------------------------
serverinfo_methods = [
    request("fee", "fee", {},
        "Reports the current state of the open-ledger requirements for the transaction cost (fee escalation)."),
    request("feature", "feature", {},
        "Returns information about protocol amendments the server knows about, and whether they are enabled."),
    request("manifest", "manifest", {
        "public_key": "nHUFE9prPXPrHcG3SkwP1UzAQbSphqyQkQK9ATXLZsfkezhhda3p",
    }, "Reports the current manifest (public info) for a known validator."),
    request("server_definitions", "server_definitions", {},
        "Returns an enumeration of transaction types, fields, and errors (SField/TxType/error definitions) used by the server."),
    request("server_info", "server_info", {},
        "Reports a human-readable version of various information about the server's current state and configuration."),
    request("server_state", "server_state", {},
        "Reports a machine-readable version of the server's current state and configuration."),
]

# --------------------------------------------------------------------------
# PUBLIC — Utility Methods
# --------------------------------------------------------------------------
utility_methods = [
    request("ping", "ping", {}, "Confirms connectivity with the server; returns an empty result on success."),
    request("random", "random", {}, "Returns a random number, for use as a source of entropy for random number generation by clients."),
    request("version", "version", {}, "Returns the API versions the server supports (first, last, and default good version)."),
]

# --------------------------------------------------------------------------
# PUBLIC — Vault Methods
# --------------------------------------------------------------------------
vault_methods = [
    request("vault_info", "vault_info", {
        "vault_id": VAULT_ID,
        "ledger_index": "validated",
    }, "Returns information about a Single Asset Vault. Specify either vault_id, or owner + seq. "
       "Requires the SingleAssetVault amendment (rippled 3.1.0+)."),
]

# --------------------------------------------------------------------------
# ADMIN — grouped folders
# --------------------------------------------------------------------------
admin_keygen = [
    request("wallet_propose", "wallet_propose", {
        "key_type": "secp256k1",
    }, "Generates a key pair and address for a new account (or from a supplied passphrase/seed)."),
    request("validation_create", "validation_create", {},
        "Generates cryptographic keys for a rippled validator to use."),
]

admin_logging = [
    request("can_delete", "can_delete", {
        "can_delete": "now",
    }, "Allows online deletion of ledgers up to a specific ledger (requires online_delete configured)."),
    request("ledger_cleaner", "ledger_cleaner", {
        "ledger": 1000000,
        "full": True,
    }, "Instructs the ledger cleaner service to check for corrupted or missing data and repair it."),
    request("ledger_request", "ledger_request", {
        "ledger_index": 1000000,
    }, "Queries connected peers to retrieve a specific ledger version from the network."),
    request("log_level", "log_level", {
        "severity": "debug",
    }, "Gets or sets the log verbosity of the server (optionally per partition)."),
    request("logrotate", "logrotate", {},
        "Closes and reopens the log file, for use with an external log-rotation tool."),
]

admin_control = [
    request("ledger_accept", "ledger_accept", {},
        "Closes and advances the ledger (stand-alone mode only)."),
    request("stop", "stop", {},
        "Gracefully shuts down the server."),
]

admin_signing = [
    request("sign", "sign", {
        "tx_json": {
            "TransactionType": "Payment",
            "Account": ACC,
            "Destination": ISSUER,
            "Amount": "1000000",
        },
        "secret": "REPLACE_WITH_SECRET",
    }, "Signs a transaction locally using a supplied secret (admin/private servers only). Prefer signing offline in production."),
    request("sign_for", "sign_for", {
        "account": ACC,
        "tx_json": {
            "TransactionType": "TrustSet",
            "Account": ACC,
            "LimitAmount": {"currency": "USD", "issuer": ISSUER, "value": "100"},
            "Sequence": 360,
            "Fee": "30000",
        },
        "secret": "REPLACE_WITH_SECRET",
    }, "Provides one signature for a multi-signed transaction (admin/private servers only)."),
    request("channel_authorize", "channel_authorize", {
        "channel_id": "5DB01B7FFED6B67E6B0414DED11E051D2EE2B7619CE0EAA6286D67A3A4D5BDB3",
        "amount": "1000000",
        "secret": "REPLACE_WITH_SECRET",
    }, "Creates a signature that can be used to redeem a specific amount from a payment channel (admin only)."),
]

admin_peers = [
    request("connect", "connect", {
        "ip": "192.170.145.88",
        "port": 51235,
    }, "Forces the server to connect to a specific peer (stand-alone/admin)."),
    request("peer_reservations_add", "peer_reservations_add", {
        "public_key": "n9MqiExBcoG19UXwoLjBJnhsxEhAZMuWwJDRdkyDz1zwjbFhkKq5",
        "description": "Example reservation",
    }, "Adds or updates a reserved slot for a specific peer."),
    request("peer_reservations_del", "peer_reservations_del", {
        "public_key": "n9MqiExBcoG19UXwoLjBJnhsxEhAZMuWwJDRdkyDz1zwjbFhkKq5",
    }, "Removes a reserved slot for a specific peer."),
    request("peer_reservations_list", "peer_reservations_list", {},
        "Lists the reserved peer slots configured on the server."),
    request("peers", "peers", {},
        "Returns information about the peer-to-peer connections the server currently has."),
]

admin_debug = [
    request("consensus_info", "consensus_info", {},
        "Provides information about the state of the consensus process as it happens."),
    request("fetch_info", "fetch_info", {
        "clear": False,
    }, "Returns information about the server's sync with the network, including ledgers being fetched."),
    request("get_counts", "get_counts", {
        "min_count": 100,
    }, "Provides statistics about the server's internal counters and memory usage."),
    request("print", "print", {},
        "Returns the current internal state of various server subsystems (admin/debug)."),
    request("validator_info", "validator_info", {},
        "Returns the validation settings of the server, if it is configured as a validator."),
    request("validator_list_sites", "validator_list_sites", {},
        "Returns information about the sites the server uses to fetch validator lists (UNLs)."),
    request("validators", "validators", {},
        "Returns human-readable information about the current validators the server trusts."),
]

# --------------------------------------------------------------------------
# CLIO Methods (served by Clio, not rippled/xrpld) — use CLIO url
# --------------------------------------------------------------------------
clio_methods = [
    request("server_info (Clio)", "server_info", {},
        "Clio's server_info includes an extra `clio` section describing the Clio server, plus the `rippled` section it proxies.", clio=True),
    request("ledger (Clio)", "ledger", {
        "ledger_index": "validated",
        "transactions": True,
        "expand": False,
    }, "Clio serves ledger data directly from its database. Same interface as rippled's ledger method.", clio=True),
    request("nft_info", "nft_info", {
        "nft_id": NFT_ID,
        "ledger_index": "validated",
    }, "Clio-only. Returns the current state of an individual NFToken (owner, URI, flags, issuer, taxon).", clio=True),
    request("nft_history", "nft_history", {
        "nft_id": NFT_ID,
        "ledger_index_min": -1,
        "ledger_index_max": -1,
        "binary": False,
        "forward": False,
        "limit": 20,
    }, "Clio-only. Returns the transaction history for a specified NFToken.", clio=True),
    request("nfts_by_issuer", "nfts_by_issuer", {
        "issuer": ISSUER,
        "ledger_index": "validated",
        "limit": 50,
    }, "Clio-only. Returns a list of NFTokens issued by the specified account, optionally filtered by taxon.", clio=True),
    request("mpt_holders", "mpt_holders", {
        "mpt_issuance_id": MPT_ISSUANCE_ID,
        "ledger_index": "validated",
        "limit": 50,
    }, "Clio-only. Returns all holders of a given Multi-Purpose Token (MPT) issuance and their balances.", clio=True),
    request("ledger_index", "ledger_index", {
        "date": "2026-01-01T00:00:00Z",
    }, "Clio-only. Returns the ledger index (and hash) that was current at the given ISO 8601 timestamp.", clio=True),
    request("ledger_range", "ledger_range", {},
        "Clio-only (undocumented on xrpl.org). Returns the min and max ledger indexes available in the Clio node's database.", clio=True),
]

# --------------------------------------------------------------------------
# Assemble collection
# --------------------------------------------------------------------------
collection = OrderedDict([
    ("info", OrderedDict([
        ("name", "XRPLD & Clio JSON-RPC API (v2)"),
        ("description",
         "Postman collection for the xrpld (rippled) and Clio JSON-RPC APIs. "
         "Every request sends `\"api_version\": 2`.\n\n"
         "Select an environment (Mainnet / Testnet / Devnet) to switch networks — it sets:\n"
         "- `XRPLD_JSONRPC_URL` — public xrpld endpoint (Public folder).\n"
         "- `CLIO_JSONRPC_URL` — Clio endpoint (Clio folder).\n"
         "- `ADMIN_JSONRPC_URL` — your own node's admin port (Admin folder; default http://localhost:5005/).\n\n"
         "Clio forwards writes/queries it doesn't serve to its xrpld node, so a Clio URL can also "
         "answer the public methods; you can point XRPLD and CLIO at the same Clio host if you like. "
         "Admin methods are never forwarded — they need a node you operate.\n\n"
         "WebSocket-only methods (subscribe, unsubscribe, path_find) are intentionally omitted."),
        ("schema", "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"),
    ])),
    ("item", [
        folder("Public xrpld Methods", [
            folder("Account Methods", account_methods),
            folder("Ledger Methods", ledger_methods),
            folder("Transaction Methods", transaction_methods),
            folder("Path and Order Book Methods", path_methods),
            folder("Payment Channel Methods", paychan_methods),
            folder("Server Info Methods", serverinfo_methods),
            folder("Utility Methods", utility_methods),
            folder("Vault Methods", vault_methods),
        ]),
        folder("Admin xrpld Methods", retarget([
            folder("Key Generation Methods", admin_keygen),
            folder("Logging and Data Management Methods", admin_logging),
            folder("Server Control Methods", admin_control),
            folder("Signing Methods", admin_signing),
            folder("Peer Management Methods", admin_peers),
            folder("Status and Debugging Methods", admin_debug),
        ], ADMIN_URL),
            "Admin methods require an admin-permitted connection on a node you operate "
            "(these requests use the {{ADMIN_JSONRPC_URL}} variable, default "
            "http://localhost:5005/). Public endpoints and Clio reject them."),
        folder("Clio Methods", clio_methods,
               "Methods served by Clio. These requests use the {{CLIO_JSONRPC_URL}} variable."),
    ]),
    ("variable", [
        OrderedDict([("key", "XRPLD_JSONRPC_URL"), ("value", "https://s1.ripple.com:51234/"), ("type", "string")]),
        OrderedDict([("key", "CLIO_JSONRPC_URL"), ("value", "https://s2.ripple.com:51234/"), ("type", "string")]),
        OrderedDict([("key", "ADMIN_JSONRPC_URL"), ("value", ADMIN_DEFAULT), ("type", "string")]),
    ]),
])


def count(items):
    n = 0
    for it in items:
        if "item" in it:
            n += count(it["item"])
        else:
            n += 1
    return n


if __name__ == "__main__":
    import os

    with open("xrpld_postman_collection.json", "w") as f:
        json.dump(collection, f, indent=4)
        f.write("\n")
    print(f"Wrote xrpld_postman_collection.json with {count(collection['item'])} requests.")

    os.makedirs("environments", exist_ok=True)
    for name, xrpld_url, clio_url, env_id in NETWORKS:
        env = environment(name, xrpld_url, clio_url, env_id)
        path = os.path.join("environments", f"{name.lower()}.postman_environment.json")
        with open(path, "w") as f:
            json.dump(env, f, indent=4)
            f.write("\n")
        print(f"Wrote {path}")
