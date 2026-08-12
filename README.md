# XRPLD & Clio Postman Collection

A Postman collection for the **xrpld** (rippled) and **Clio** JSON-RPC APIs. Every
request sends `"api_version": 2`, so responses use the current v2 schema.

This is a from-scratch replacement for the old, unmaintained
[`goxrp/rippled-postman`](https://github.com/goxrp/rippled-postman) collection (which
predates api_version 2, NFTs, AMMs, Clio, vaults, and more).

## Usage

1. Import [`xrpld_postman_collection.json`](xrpld_postman_collection.json) into Postman.
2. Import the environments from [`environments/`](environments/) (Mainnet, Testnet,
   Devnet).
3. Pick an environment from the top-right dropdown to choose your network.
4. Open a request and hit **Send**.

Switching the environment repoints both the xrpld and Clio URLs to the same network
at once.

### Variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `XRPLD_JSONRPC_URL` | Public xrpld Methods | Public xrpld (rippled) endpoint |
| `CLIO_JSONRPC_URL` | Clio Methods | Clio endpoint |
| `ADMIN_JSONRPC_URL` | Admin xrpld Methods | A node **you operate**, admin port (default `http://localhost:5005/`) |

### Endpoints per environment

| Variable | Mainnet | Testnet | Devnet |
| --- | --- | --- | --- |
| `XRPLD_JSONRPC_URL` | `https://s1.ripple.com:51234/` | `https://s.altnet.rippletest.net:51234/` | `https://s.devnet.rippletest.net:51234/` |
| `CLIO_JSONRPC_URL` | `https://s2.ripple.com:51234/` | `https://clio.altnet.rippletest.net:51234/` | `https://clio.devnet.rippletest.net:51234/` |
| `ADMIN_JSONRPC_URL` | `http://localhost:5005/` | `http://localhost:5005/` | `http://localhost:5005/` |

## xrpld vs Clio: which URL?

Clio is a read-optimized API server backed by an xrpld node. It answers most read
methods from its own database and **forwards** anything it doesn't implement
(`submit`, `fee`, `ledger_current`, …) to that xrpld node. So:

- A **Clio** URL can answer both the public xrpld methods *and* the Clio-only methods
  (`nft_info`, `nft_history`, `nfts_by_issuer`) — you can point `XRPLD_JSONRPC_URL`
  and `CLIO_JSONRPC_URL` at the same Clio host if you want.
- A **bare xrpld** node does *not* implement the Clio-only methods — those must hit
  Clio. (On the public cluster, `s1`/`s2` are both Clio-fronted; the `altnet`/`devnet`
  `s.*` endpoints are bare rippled.)
- **Admin methods are never forwarded.** They only work against a node you operate,
  which is why they use a separate `ADMIN_JSONRPC_URL`.

## api_version 2

Each request body pins the API version inside the params object:

```json
{
  "method": "account_info",
  "params": [
    {
      "api_version": 2,
      "account": "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
      "ledger_index": "validated"
    }
  ]
}
```

Notable v2 differences vs v1: `tx` returns transaction fields under `tx_json`;
`server_info` reports `rippled_version` (and `clio_version` on Clio) instead of
`build_version`; `tx_history` and several legacy behaviors are removed; unknown /
invalid inputs return errors rather than being silently coerced. See the
[XRPL API breaking changes](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/request-formatting)
notes for the full list.

## What's included

**Public xrpld Methods**

- Account: `account_channels`, `account_currencies`, `account_info`, `account_lines`,
  `account_nfts`, `account_objects`, `account_offers`, `account_tx`,
  `gateway_balances`, `noripple_check`
- Ledger: `ledger`, `ledger_closed`, `ledger_current`, `ledger_data`, `ledger_entry`,
  `book_changes`
- Transaction: `submit`, `submit_multisigned`, `transaction_entry`, `tx`, `simulate`
- Path & Order Book: `amm_info`, `book_offers`, `deposit_authorized`,
  `nft_buy_offers`, `nft_sell_offers`, `ripple_path_find`
- Payment Channel: `channel_verify`
- Server Info: `fee`, `feature`, `manifest`, `server_definitions`, `server_info`,
  `server_state`
- Utility: `ping`, `random`, `version`
- Vault: `vault_info`

**Admin xrpld Methods**

- Key Generation: `wallet_propose`, `validation_create`
- Logging & Data Management: `can_delete`, `ledger_cleaner`, `ledger_request`,
  `log_level`, `logrotate`
- Server Control: `ledger_accept`, `stop`
- Signing: `sign`, `sign_for`, `channel_authorize`
- Peer Management: `connect`, `peer_reservations_add`, `peer_reservations_del`,
  `peer_reservations_list`, `peers`
- Status & Debugging: `consensus_info`, `fetch_info`, `get_counts`, `print`,
  `validator_info`, `validator_list_sites`, `validators`

**Clio Methods** (served by Clio): `server_info`, `ledger`, `ledger_index`,
`ledger_range`, `nft_info`, `nft_history`, `nfts_by_issuer`, `mpt_holders`

(`ledger_range` works on Clio but is undocumented on xrpl.org.)

### Notes

- **Admin methods** require an admin-permitted connection — the local/private
  JSON-RPC port on a server you operate (`ADMIN_JSONRPC_URL`) — and will be rejected
  by public endpoints and by Clio.
- **Signing methods** (`sign`, `sign_for`, `channel_authorize`) take a secret;
  placeholders are marked `REPLACE_WITH_SECRET`. Prefer signing offline / client-side
  in production.
- **WebSocket-only** methods (`subscribe`, `unsubscribe`, `path_find`) are omitted —
  they have no JSON-RPC equivalent.
- Example accounts, NFT IDs, and hashes are illustrative; swap in live values before
  sending.

## Regenerating

The collection and environment files are generated from [`build.py`](build.py):

```bash
python3 build.py
```

Edit the method definitions (or the `NETWORKS` list) in `build.py` and re-run to
update `xrpld_postman_collection.json` and the files under `environments/`.

## License

[ISC](LICENSE) © 2026 Neil Smith
