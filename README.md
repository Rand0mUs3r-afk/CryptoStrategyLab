# CryptoStrategyLab

Standalone crypto-only research and forward paper simulation. **No real orders,
exchange keys, leverage, short selling or connection to ChatGptTrader.** This
repository does not import or modify the stock project or its account state.

## Start in your browser

1. Open **Actions → Crypto lab tests** to inspect tests for the deployed commit.
2. Choose **Crypto strategy experiments → Run workflow → smoke** for BTC/ETH,
   15-minute/hourly backtests with 60 days of public Coinbase data. Select `full`
   for all six assets, four horizons and eight strategy families.
3. Choose **Crypto forward paper lab → Run workflow** and tick
   `initialize_new_state` for the FIRST run only. Later runs restore `paper-state`.
   No API secrets are required; enable Actions if GitHub requests it.
4. Optional recurring observation: Settings → Secrets and variables → Actions →
   Variables: set `CRYPTO_LAB_ENABLED=true`. Without this it is manual-only.
5. Pause new simulated entries while permitting observed exits by setting
   `CRYPTO_PAUSE_ENTRIES=true`.
6. Read the workflow Summary/download its artifact. Latest durable forward state
   and CSV reports are also committed on the dedicated `paper-state` branch.

If the repository's policy blocks writes, allow **contents: write** for the forward
workflow. State writes never force-push. Authentication/network failures do not
silently reset books; config/version changes fail until you explicitly archive
and initialize a new experiment.

## Experiments

| Family | Entry hypothesis |
|---|---|
| EMA crossover | EMA20 crosses EMA50 above EMA200 |
| Trend pullback | EMA20 pullback followed by prior-high break; trend/RSI filter |
| Donchian breakout | Prior 20-bar high breaks with trend/volume confirmation |
| Bollinger reversion | Lower-band breach returns inside; RSI/trend-floor filter |
| RSI rebound | RSI14 crosses back above 30; long-term trend floor |
| MACD momentum | MACD12/26 crosses its 9-period signal in an uptrend |
| Squeeze breakout | Low-bandwidth setup breaks prior channel with trend filter |
| Rolling VWAP reclaim | Rolling 20-bar VWAP reclaim with trend/volume confirmation |

| Bar | Maximum hold | Full-suite requested history |
|---|---|---|
| 5 minutes | 1 hour | 30 days |
| 15 minutes | 6 hours | 90 days |
| 1 hour | 3 days | 365 days |
| 6 hours | 7 days | 730 days |

Assets: BTC-USD, ETH-USD, SOL-USD, LINK-USD, LTC-USD, AVAX-USD. Product identity,
USD quote and online status are verified with the provider, never guessed.
192 registered asset/horizon/strategy hypotheses are evaluated separately. Each
has its OWN simulated $10,000 and one possible open position. These independent
books are NOT one funded account; do not sum their returns or capital.

## Evaluation safeguards

- Closed bars, past-only indicators and prior-bar breakout channels. Historical
  fills occur at the NEXT open, not at the signal-generating close.
- Chronological 60/20/20 train/validation/holdout with a maximum-hold purge between
  segments. Development walk-forward selects using earlier data and evaluates
  later folds; CASH is selected if no candidate meets its development filter.
- Every strategy/trial, losing result, stress case and data error is retained.
  Holdout metrics are descriptive. Tuning after viewing them requires a fresh
  future evaluation period; no multiple-testing-adjusted significance is claimed.
- Per-side research assumptions: 40 bps fee + 5 slippage + 5 half-spread. They are
  NOT your quoted personal exchange fee tier. Stress doubles modeled costs.
  Forward fills use observed bid/ask plus fee/slippage, no extra fake spread.
- Risk budget 0.5% per independent book, 20% notional cap, ATR1.5 stop, gross 2R
  target. Position sizing includes estimated roundtrip costs. Gaps can exceed
  modeled risk. No martingale, averaging down or stop widening.
- 2% daily marked-equity loss pauses new entries. 10% marked-equity drawdown
  permanently latches an entry pause in that experiment. Exits remain eligible.
- Both historical stop/target hit in one candle: stop first. Gap stop: worse open.
  Target gaps do not receive favorable price improvement. Boundary exits labeled.
- Metrics: net win rate, descriptive Wilson 95% interval, profit factor, expectancy
  in dollars/R, drawdown, total fees and sample size. Below 50 closed trades is
  labeled insufficient. Even 50 trades is not proof of an edge.
- All trials, trades, equity curves, configuration, dataset snapshots/hashes,
  timestamps and code SHA are exported. Missing candles are never forward-filled.
- Cash and cost-adjusted buy/hold benchmarks have DIFFERENT exposure from capped
  strategy books; no risk-normalized outperformance claim is made.

## Forward timing and cost limits

Optional GitHub schedule: **:07 and :37 each hour, 24/7**. It is coarse forward
observation, NOT continuous scalp execution. Five-minute strategies are primarily
historical experiments at this cadence; intermediate signals are not replayed.
GitHub may delay/drop jobs. A streaming host would be needed for precise
minute/second-level execution, and is outside this deployment.

Paper entries/exits use actual observation-time quotes. Historical intrabar level
touches never masquerade as executable forward fills; missed level-touch bars
are counted. Stale quotes leave books unevaluated rather than falsely closed.
Candle errors block entries but do not block exits at a fresh quote. A >2-hour
observation gap blocks new entries on the recovery run. One stale observation
can allow losses beyond a simulated stop; this is not an exchange-hosted stop.

Private-repository Actions minutes are shared with your OTHER private projects.
Recurring jobs can consume the allowance and affect those jobs. Scheduling is
therefore opt-in, not silently enabled. No billing settings are changed.
The ledger is hash-linked for accidental corruption detection; it is not external
tamper-proof attestation. Correlated trades and 192 hypotheses mean naive Wilson
intervals overstate independence. No automatic live promotion exists.

## Local development (optional)

```sh
python -m pip install -r requirements.txt
python -m pytest -q
python cryptolab.py research --products BTC-USD --timeframes 1h --days 60
python cryptolab.py paper --pause-entries
```

Configuration is `config.json`; engine and CLI are `cryptolab.py`. This deployment
was rebuilt from the earlier design because the previous sandbox archive did not
persist. This exact revision was re-tested: **37 mechanical tests passed**; actual
BTC hourly/60-day smoke data completed with zero errors; paused forward observation
validated six product quotes and all configured candle horizons with zero errors.
These checks do not prove profitability. Hosted workflow execution and recurring
scheduling must be verified separately in Actions; a commit is not a successful run.

## Method references

- [Coinbase candle API](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles): granularity, OHLCV layout, pagination and incomplete data caveats.
- [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
- [GitHub Actions billing](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions).
- [StockCharts price channels](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/price-channels).
- [Fidelity technical analysis](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/what-is-technical-analysis).

No guaranteed winning percentage or investment recommendation is made. Compare
net expectancy, loss magnitude and future evidence, not win percentage alone.
