# Journal fixes and Alpaca PAPER setup

## Implemented

- Readable open/closed journals with separate coin, timeframe and strategy columns.
- Entry, quantity, entry dollars plus fee, TP, SL, UTC timestamps and full-precision CSVs.
- Realized profit separated from estimated open net profit including modeled exit costs.
- Marked equity before selling costs and estimated liquidation equity after costs.
- Missing/stale current-run quotes display n/a. Existing state and strategy configuration retained.
- Manual Alpaca PAPER read-only account/crypto checks. No order writes or live host.

## Important shared-account blocker

Verified in the unchanged [stock coordinator](https://github.com/Rand0mUs3r-afk/ChatGptTrader/blob/main/portfolio_paper.py)
`book()`: any open order outside the stock bot's ownership set raises `Unmanaged open order`;
any position without exactly one stock-bot owner raises `Position ownership mismatch`.
Crypto orders/positions in the same account would therefore halt stock reconciliation.

To honor the requirement to leave ChatGptTrader unchanged, **shared-account crypto
execution is blocked in code**. The HTTP client supports GET only. Repository variables
cannot enable orders. This is readiness integration, NOT completed broker execution.
Future execution needs an explicitly approved cross-bot coordinator change or a separate
paper account, plus tested ownership, allocation, fill, fee and exit reconciliation.
No keys, schedules or settings are changed in the stock repository.

## Secrets to add

In **CryptoStrategyLab -> Settings -> Secrets and variables -> Actions -> Secrets**:

| Name | Value |
|---|---|
| `ALPACA_PAPER_KEY_ID` | Existing Alpaca PAPER account API key |
| `ALPACA_PAPER_SECRET_KEY` | Matching PAPER secret key |

Secrets are repository-scoped. Enter the same values separately here; no access to their
plaintext values is needed or attempted. Never paste keys into chat or commit them.
No live API keys, Coinbase key, OpenAI key or custom GitHub token is required.

Under **Variables**:

| Name | Value |
|---|---|
| `ALPACA_EXPECTED_PAPER_ACCOUNT_ID` | Same paper account API UUID used by the stock repo; not the human account number |
| `CRYPTO_LAB_ENABLED` | Optional `true` for Coinbase simulation schedule; unrelated to Alpaca orders |
| `CRYPTO_PAUSE_ENTRIES` | Optional `true` to pause simulated entries while evaluating quote exits |

Do not set `ALPACA_CRYPTO_PAPER_ENABLED` or `ALPACA_SHARED_ACCOUNT_REVIEWED` to true.
The new workflow explicitly sets them false and there is no write-capable code path.

## Run in the browser

1. Wait for Crypto lab tests to pass for this commit; local tests do not prove hosted execution.
2. Run **Crypto forward paper lab** to regenerate journals. Leave initialization unchecked
   when paper-state already exists. Existing virtual positions are NOT converted to broker trades.
3. Read [paper-state/journal.md](https://github.com/Rand0mUs3r-afk/CryptoStrategyLab/blob/paper-state/journal.md)
   after the next successful observation. CSVs: open_positions.csv, closed_trades.csv,
   account_books.csv; original state.json/trades.csv remain intact.
4. After adding paper secrets and expected account UUID, run **Alpaca crypto PAPER readiness**:
   mode `check`, initialize_new_state=true on its FIRST run only if alpaca-crypto-state is absent.
5. `plan` reads account inventory, supported crypto assets and Alpaca quotes; it submits NOTHING.
   Account verification does not mean shared-account trading is approved.
6. Read workflow Summary or alpaca-crypto-state/status.json. Missing credentials, unexpected
   accounts, bad state or network errors fail closed. Initialization never occurs silently after
   authentication/network errors. No workflow uses force-push.

## Scope and limits

Research/virtual signals still use public Coinbase candles and quotes, not Alpaca fills.
192 independent simulated books are experiments, not a combined Alpaca portfolio.
The fixed Alpaca hosts are paper-api.alpaca.markets and data.alpaca.markets; redirects and
all POST/DELETE requests are refused. Diagnostics do not claim broker fees/net profit or
manufacture trade fills. Existing stock positions are neither adopted nor touched.

Optional GitHub simulation scheduling is twice-hourly, potentially delayed. Software
TP/SL is checked only at observations: not standing exchange protection, not continuous
scalping. Prices can cross levels between checks. No guaranteed win rate or profitability.
Trading costs in virtual reports are model assumptions, not actual personal fee tiers.
