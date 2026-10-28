# Alpaca crypto PAPER execution setup

This replacement implements order submission and software-managed exits for a DEDICATED
Alpaca paper account. It does not change ChatGptTrader or submit real-money orders.
No account connection or order has been tested against your credentials in this build.

## What changed

- `alpaca_crypto.py`: check, plan and execution (`tick`) modes; fixed paper host;
  authenticated market/gtc quantity orders; broker client-ID lookup; scoped cancellation;
  order/fill reconciliation, fee-activity checks and a readable broker journal.
- `alpaca_config.json`: separate broker portfolio settings. The research `config.json`
  is intentionally unchanged so existing simulation ledgers retain their config hash.
- `.github/workflows/alpaca-crypto-paper.yml`: manual execution and an opt-in roughly
  five-minute schedule, one serialized runner, durable ledger pushes BEFORE each
  order attempt and checkpoint/report uploads even when a tick fails.
- `tests/test_journal_alpaca.py`: replaces the obsolete unconditional execution-block
  test with the dedicated-account execution gate test; retains reporting regressions.
- `tests/test_alpaca_execution.py`: deterministic broker fixtures, not market results.
- `.github/workflows/ci.yml`: also compiles the new adapter and reporting code.

## Upload the files

Unzip the replacement bundle. Copy each file into the SAME path in CryptoStrategyLab.
Do not put the Python files inside `.github/workflows`. Only the YAML workflows belong
there. Keep your existing research.yml and every file not present in this bundle.
The package is an overlay, not a replacement for your GitHub state branches.

New file: `alpaca_config.json` at repository root.
New test: `tests/test_alpaca_execution.py` in the existing tests directory.
Replace the old tests with their matching paths; do not leave old duplicate test files.

## Secrets (dedicated NEW crypto paper account)

In CryptoStrategyLab -> Settings -> Secrets and variables -> Actions -> Secrets:

| Secret | Value |
|---|---|
| ALPACA_PAPER_KEY_ID | New dedicated crypto PAPER account API key |
| ALPACA_PAPER_SECRET_KEY | Its matching PAPER API secret |

No OpenAI, Coinbase or live trading key is needed. Do not change ChatGptTrader secrets.
Do not put key values into files or workflow YAML.

## Variables

Under the same Actions settings, choose Variables:

| Variable | Value |
|---|---|
| ALPACA_EXPECTED_PAPER_ACCOUNT_ID | Your dedicated paper account API `id` (UUID), not account_number |
| ALPACA_CRYPTO_DEDICATED_ACCOUNT | true |
| ALPACA_CRYPTO_PAPER_ENABLED | true to permit tick orders AND enable scheduled ticks |
| ALPACA_CRYPTO_PAUSE_ENTRIES | false (true pauses new buys, still checks exits) |
| ALPACA_CRYPTO_STATE_BRANCH | optional; default alpaca-crypto-state |

The old ALPACA_SHARED_ACCOUNT_REVIEWED variable is no longer used. Keep the stock bot
on its original account. Dedicated-account mode refuses unrelated orders/positions;
it does not cancel, liquidate or adopt them.

## Browser start

1. Upload/commit these replacement files to main. Wait for Crypto lab tests to pass.
2. Leave ALPACA_CRYPTO_PAPER_ENABLED false for a read-only check if desired.
3. Actions -> Alpaca crypto PAPER bot -> Run workflow -> main -> mode check.
   If your successful earlier check already created the state branch for THIS account,
   leave initialize_new_state UNCHECKED. Only tick it when that branch does not exist.
4. Check the Summary. If the account matches, set the two enable/dedicated variables
   true. Run workflow again with mode tick. The first tick requires an EMPTY dedicated
   account (no positions/open orders). It initializes execution fields over the existing
   readiness observations without resetting them.
5. A tick evaluates exits, then signals, then submits eligible paper orders. A successful
   run with zero orders can be normal: no new eligible signal, no available allocation,
   unsupported coin, or unavailable data. It does not force a demonstration trade.
6. Subsequent scheduled ticks run approximately every five minutes while enabled.
   GitHub can delay/drop runs. This is periodic paper trading, not a continuous scalper.

Setting ENABLED=true also permits the next scheduled tick; do this only after the
files/tests/check are in place. Do not leave manual stock orders in the crypto account.

If the state branch belongs to the OLD account: do not delete it or edit its account ID.
Set ALPACA_CRYPTO_STATE_BRANCH to a NEW name, e.g. alpaca-crypto-state-new-account,
run check with first initialization checked, and continue with the new account.

## Sizing and strategy arbitration

All eight uploaded strategy families can signal. Coinbase supplies CLOSED OHLCV candles;
Alpaca's tradable asset list and fresh bid/ask quotes control broker eligibility/pricing.
This explicitly uses different data venues. An entry is skipped if its current Alpaca ask
is more than 3% from the signal candle close, or the spread is above 50 bps.

Default priority: 15m, 1h, 6h, 5m; within a timeframe, the configured strategy order.
Only ONE broker position per coin is allowed. The first eligible candidate takes that
coin's slot; these are not 192 simultaneously funded Alpaca books, not a trained winner
selector, and not a proven profitable ensemble. The old virtual experiments still run
independently through paper.yml/paper_report.py and are NOT converted into broker orders.

Sizing defaults in alpaca_config.json: up to $200 per entry, $1,200 total marked exposure
plus pending buy reservations, up to six active coin slots, no borrowed buying power,
and a 0.5% account-equity estimated risk budget (the smaller limit controls size).
These are sizing targets before market-price changes, not guaranteed hard loss or
execution-value limits. Crypto cannot be shorted by this adapter.

A gross target is 2x the ATR-based stop distance. TP/SL use ACTUAL broker average fill
prices, not assumed quote fills. A partial buy is tracked and a stale pending order is
canceled by its own broker ID before residual filled inventory can be sold on a later tick.
Exit quantities never intentionally exceed reconciled available broker inventory.

## Journal

Open the selected execution state branch:
- journal.md / summary.md: coin, timeframe, strategy, entry, filled quantity, entry dollars,
  remaining quantity, TP, SL and status.
- orders.csv: requested quantity vs ACTUAL filled quantity/price/time, client ID, broker
  order ID, entry/exit side and status.
- open_positions.csv / closed_trades.csv: position/cycle records and close reasons.
- fees.csv: actual CFEE activities reported by Alpaca; fee posting can be delayed.
- alpaca_state.json: durable execution ledger, all intent payloads and observations.
- status.json: latest workflow result and reason when blocked.

P&L is deliberately labeled cashflow BEFORE USD fees; base-unit fees reduce sellable
inventory. No final net win rate or fabricated fee attribution is reported. The original
virtual reporting still uses its explicit modeled trading-cost assumptions.

## Operational limits and recovery

TP/SL are SOFTWARE triggers checked when the workflow runs. No native bracket/OCO
order is installed. There is no second-by-second protection; market exits may be worse
than the displayed stop, and a stopped runner cannot execute exits.

Missing/stale quotes block quote-triggered exits; missing candles block only new entries.
Known broker/position inconsistencies also stop execution until reconciled. If a crypto
fee changes inventory before its CFEE activity is available, the bot waits for matching
broker activity rather than treating that unexplained reduction as an owned fill.
Sub-minimum/rounding residuals remain visible as dust and can block that coin's next
trade. They are NOT silently counted as closed or profitable. Manual review may be needed.

Before each new order, the precise intent and client ID are pushed to the execution
state branch. If the POST result is lost, the next run queries that ID. If no broker order
can be found for an attempted intent, execution halts for manual inspection instead of
blindly submitting it again. Do not clear attempted flags or wipe the ledger to bypass
this ambiguity. Inspect the broker order history and restore/reconcile the exact order.

FAILED_CLOSED does NOT mean the tick submitted zero orders: an earlier order may have
succeeded before a later error. Always inspect orders.csv, the saved intent and Alpaca.
The scoped state never force-pushes. Do not run another copy concurrently on this account.

To stop NEW entries but keep managing exits: ALPACA_CRYPTO_PAUSE_ENTRIES=true.
To stop all automatic runs: ALPACA_CRYPTO_PAPER_ENABLED=false; existing positions then
need attention because workflow-based exits will no longer run automatically.
The 10% high-water drawdown entry pause stays latched in the ledger; the 2% daily loss
entry pause resets at the next UTC day. Neither pause cancels existing positions.

Schedule costs: about 288 scheduled launches/day, plus any manual runs. Private Actions
minutes are shared with your other projects. No billing setting is changed by this bundle.

## Validation and references

Read TEST_RESULTS.md for the actual local results and limits. Mechanical fixtures are
not market-performance evidence. This package has not authenticated to your broker,
submitted a test order or verified a hosted Actions run.

Official order support: https://docs.alpaca.markets/us/docs/crypto-orders
Crypto quantities/fees: https://docs.alpaca.markets/us/docs/crypto-trading
Client-order lookup: https://docs.alpaca.markets/us/reference/getorderbyclientorderid
