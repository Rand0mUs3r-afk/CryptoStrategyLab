"""Isolated long-only crypto research. Public GET data; no real-order adapter."""
import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

STRATEGIES = ('ema_cross', 'trend_pullback', 'donchian_breakout', 'bollinger_reversion',
              'rsi_rebound', 'macd_momentum', 'squeeze_breakout', 'rolling_vwap_reclaim')
COLUMNS = ['time', 'low', 'high', 'open', 'close', 'volume']
ENGINE_VERSION = 1


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def config(path='config.json'):
    c = json.loads(Path(path).read_text())
    if c['mode'] != 'simulation_only':
        raise ValueError('Only simulation_only is supported')
    if not c['products'] or len(set(c['products'])) != len(c['products']):
        raise ValueError('Products must be unique and nonempty')
    if any(not p.endswith('-USD') or not p.replace('-', '').isalnum() for p in c['products']):
        raise ValueError('Only explicit USD spot product identifiers are supported')
    if not c['strategies'] or not set(c['strategies']) <= set(STRATEGIES):
        raise ValueError('Unknown strategy')
    if len(set(c['strategies'])) != len(c['strategies']):
        raise ValueError('Duplicate strategy')
    if not c['timeframes'] or any(t['seconds'] not in [60, 300, 900, 3600, 21600, 86400]
                                or t['hold'] < 1 or t['days'] < 1 for t in c['timeframes'].values()):
        raise ValueError('Invalid timeframes')
    for k in ['risk_fraction', 'notional_cap', 'min_stop', 'max_stop', 'daily_loss_pause', 'drawdown_pause']:
        if not 0 < c[k] < 1:
            raise ValueError(f'Invalid {k}')
    if not 0 < c['min_stop'] < c['max_stop'] < 1 or c['warmup'] < 210:
        raise ValueError('Invalid stop bounds or warmup')
    for k in ['initial_equity', 'stop_atr', 'target_r', 'min_review_trades', 'max_quote_age',
              'max_spread_bps', 'max_observation_gap']:
        if not math.isfinite(c[k]) or c[k] <= 0:
            raise ValueError(f'Invalid {k}')
    if c['stress_multiplier'] < 1:
        raise ValueError('Stress multiplier must be at least one')
    for k in ['fee_bps', 'slippage_bps', 'half_spread_bps']:
        if not 0 <= c[k] < 1000:
            raise ValueError(f'Invalid {k}')
    return c


def atomic_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=p.parent, prefix='.pending-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, allow_nan=False)
            f.write('\n')
        os.replace(temp, p)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def csv(rows, path):
    pd.DataFrame(rows if rows else [], columns=None if rows else ['status']).to_csv(path, index=False)


def normalize(rows, seconds, start, end):
    if not rows or any(not isinstance(r, (list, tuple)) or len(r) != 6 for r in rows):
        raise ValueError('Empty/unexpected candle schema')
    d = pd.DataFrame(rows, columns=COLUMNS).apply(pd.to_numeric, errors='raise')
    if not np.isfinite(d.to_numpy()).all() or (d.time % seconds != 0).any():
        raise ValueError('Nonfinite or off-grid candles')
    if (d[['low', 'high', 'open', 'close']] <= 0).any().any() or (d.volume < 0).any():
        raise ValueError('Invalid price or volume')
    if ((d.high < d[['low', 'open', 'close']].max(axis=1)) |
        (d.low > d[['high', 'open', 'close']].min(axis=1))).any():
        raise ValueError('Inconsistent OHLC')
    dup = d[d.duplicated('time', keep=False)]
    if len(dup) and (dup.groupby('time')[COLUMNS[1:]].nunique() > 1).any().any():
        raise ValueError('Conflicting duplicates')
    d = d.drop_duplicates('time').sort_values('time')
    d = d[(d.time >= start) & (d.time + seconds <= end)].reset_index(drop=True)
    if d.empty:
        raise ValueError('No closed candles')
    d['time'] = d.time.astype('int64')
    if (d.time.diff().dropna() != seconds).any():
        raise ValueError('Missing candles; no fabricated fills or forward filling')
    return d


class PublicMarket:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'CryptoStrategyLab/1 research'
        self.last = 0.0

    def get(self, path, params=None):
        if not path.startswith('/products/') or '..' in path or '?' in path:
            raise ValueError('Only public product GET endpoints allowed')
        for attempt in range(4):
            time.sleep(max(0, .15 - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            try:
                r = self.session.get('https://api.exchange.coinbase.com' + path, params=params,
                                     timeout=(5, 25), allow_redirects=False)
                if (r.status_code == 429 or r.status_code >= 500) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                r.raise_for_status()
                if r.status_code != 200:
                    raise ValueError('Unexpected response status')
                return r.json()
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError('Market request exhausted')

    def product(self, symbol):
        p = self.get('/products/' + symbol)
        if (p.get('id') != symbol or p.get('quote_currency') != 'USD'
                or p.get('base_currency') != symbol.split('-')[0]):
            raise ValueError('Product identity mismatch')
        if p.get('status') != 'online' or p.get('trading_disabled') or p.get('cancel_only'):
            raise ValueError('Product unavailable')
        return {k: p[k] for k in ['id', 'base_currency', 'quote_currency', 'status']}

    def quote(self, symbol, max_age):
        q = self.get('/products/' + symbol + '/ticker')
        now = time.time()
        bid, ask = float(q['bid']), float(q['ask'])
        stamp = datetime.fromisoformat(q['time'].replace('Z', '+00:00')).timestamp()
        if not np.isfinite([bid, ask, stamp]).all() or not 0 < bid <= ask:
            raise ValueError('Invalid quote')
        if not -30 <= now - stamp <= max_age:
            raise ValueError('Stale/future quote')
        return dict(bid=bid, ask=ask, provider_time=stamp, observed_at=now,
                    spread_bps=(ask-bid)/((ask+bid)/2)*10000)

    def candles(self, symbol, seconds, start, end):
        start, end = int(start // seconds * seconds), int(end // seconds * seconds)
        rows, cursor = [], start
        while cursor < end:
            stop = min(end, cursor + 299 * seconds)
            iso = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat()
            rows.extend(self.get('/products/' + symbol + '/candles',
                                 dict(start=iso(cursor), end=iso(stop), granularity=seconds)))
            cursor = stop
        d = normalize(rows, seconds, start, end)
        if d.iloc[0].time != start or d.iloc[-1].time + seconds != end:
            raise ValueError('Incomplete requested candle coverage')
        return d


def features(d):
    x = d.copy()
    for n in [12, 20, 26, 50, 200]:
        x[f'e{n}'] = x.close.ewm(span=n, adjust=False, min_periods=n).mean()
    tr = pd.concat([x.high-x.low, (x.high-x.close.shift()).abs(),
                    (x.low-x.close.shift()).abs()], axis=1).max(axis=1)
    x['atr'] = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    delta = x.close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    x['rsi'] = 100-100/(1+gain/loss.replace(0, np.nan))
    x.loc[(gain > 0) & (loss == 0), 'rsi'] = 100
    x.loc[(gain == 0) & (loss == 0), 'rsi'] = 50
    avg, sd = x.close.rolling(20).mean(), x.close.rolling(20).std(ddof=0)
    x['upper'], x['lower'], x['width'] = avg+2*sd, avg-2*sd, 4*sd/avg
    x['width_floor'] = x.width.shift().rolling(100).quantile(.2)
    x['high20'], x['high10'] = x.high.shift().rolling(20).max(), x.high.shift().rolling(10).max()
    x['vol_ratio'] = x.volume/x.volume.shift().rolling(20).mean().replace(0, np.nan)
    x['macd'] = x.e12-x.e26
    x['macd_signal'] = x.macd.ewm(span=9, adjust=False, min_periods=9).mean()
    x['vwap'] = (((x.high+x.low+x.close)/3)*x.volume).rolling(20).sum()/x.volume.rolling(20).sum().replace(0, np.nan)
    x['regime'] = np.where((x.close > x.e200) & (x.e20 > x.e50), 'up',
                           np.where((x.close < x.e200) & (x.e20 < x.e50), 'down', 'range'))
    return x


def signals(x, name):
    trend = (x.close > x.e200) & (x.e20 > x.e50)
    rules = {
        'ema_cross': (x.e20 > x.e50) & (x.e20.shift() <= x.e50.shift()) & (x.close > x.e200),
        'trend_pullback': trend & (x.low.shift() <= x.e20.shift()) & (x.close > x.high.shift()) & x.rsi.between(40, 70),
        'donchian_breakout': trend & (x.close > x.high20) & (x.vol_ratio >= 1.2),
        'bollinger_reversion': (x.close.shift() < x.lower.shift()) & (x.close > x.lower) & (x.rsi < 45) & (x.close > x.e200*.95),
        'rsi_rebound': (x.rsi.shift() < 30) & (x.rsi >= 30) & (x.close > x.e200*.95),
        'macd_momentum': trend & (x.macd > x.macd_signal) & (x.macd.shift() <= x.macd_signal.shift()),
        'squeeze_breakout': (x.width.shift() <= x.width_floor.shift()) & (x.close > x.high10) & (x.close > x.upper.shift()) & trend,
        'rolling_vwap_reclaim': trend & (x.close.shift() <= x.vwap.shift()) & (x.close > x.vwap) & (x.vol_ratio >= 1.2),
    }
    if name not in rules:
        raise ValueError('Unknown strategy')
    return (rules[name] & x.e200.notna() & x.atr.notna()).fillna(False)


def new_book(c):
    seed = c['initial_equity']
    return dict(cash=float(seed), position=None, high_water=float(seed), day=None,
                day_start=float(seed), daily_paused=False, drawdown_paused=False,
                consumed_signal=None, curve=[dict(time=0, equity=float(seed))],
                last_candle=None, missed_level_bars=0)


def equity(b, mark):
    return b['cash'] + (b['position']['qty']*mark if b['position'] else 0)


def risk(b, mark, stamp, c):
    eq = equity(b, mark)
    day = datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
    if day != b['day']:
        b.update(day=day, day_start=eq, daily_paused=False)
    b['high_water'] = max(eq, b['high_water'])
    b['daily_paused'] |= eq <= b['day_start']*(1-c['daily_loss_pause'])
    b['drawdown_paused'] |= eq <= b['high_water']*(1-c['drawdown_pause'])
    return eq


def friction(c, stress=1, quoted=False):
    return (c['slippage_bps'] + (0 if quoted else c['half_spread_bps']))*stress/10000


def enter(b, ref, atr, signal_time, now, regime, c, stress=1, quoted=False):
    if b['position'] or b['daily_paused'] or b['drawdown_paused']:
        return False
    if not np.isfinite([ref, atr]).all() or ref <= 0 or atr <= 0:
        return False
    fill = ref*(1+friction(c, stress, quoted))
    distance = max(atr*c['stop_atr'], fill*c['min_stop'])
    if distance/fill > c['max_stop']:
        return False
    fee_rate = c['fee_bps']*stress/10000
    unit_risk = distance + 2*fill*(fee_rate+friction(c, stress, quoted))
    qty = min(b['cash']*c['risk_fraction']/unit_risk,
              b['cash']*c['notional_cap']/fill, b['cash']/(fill*(1+fee_rate)))
    if not math.isfinite(qty) or qty <= 0:
        return False
    fee = qty*fill*fee_rate
    b['cash'] -= qty*fill+fee
    b['position'] = dict(qty=qty, entry=fill, entry_fee=fee, stop=fill-distance,
                         target=fill+distance*c['target_r'], signal_time=int(signal_time),
                         entry_time=float(now), risk_usd=qty*unit_risk, regime=str(regime), bars=0)
    return True


def exit_trade(b, ref, now, reason, c, stress=1, quoted=False):
    p = b['position']
    if p is None:
        raise ValueError('Cannot close an empty book')
    fill = ref*(1-friction(c, stress, quoted))
    fee = p['qty']*fill*c['fee_bps']*stress/10000
    proceeds = p['qty']*fill-fee
    pnl = proceeds-p['qty']*p['entry']-p['entry_fee']
    b['cash'] += proceeds
    b['position'] = None
    return dict(p, exit=fill, exit_fee=fee, exit_time=float(now), reason=reason,
                net_pnl=pnl, net_r=pnl/p['risk_usd'])


def bar_exit(p, bar, hold):
    if bar.open <= p['stop']:
        return float(bar.open), 'gap_stop'
    if bar.low <= p['stop']:
        return p['stop'], 'stop'
    if bar.high >= p['target']:
        return p['target'], 'target'
    if p['bars'] >= hold:
        return float(bar.close), 'time'
    return None


def backtest(x, sig, lo, hi, tf, c, stress=1):
    b, trades = new_book(c), []
    for i in range(lo, hi):
        row = x.iloc[i]
        now = int(row.time)
        risk(b, float(row.open), now, c)
        if not b['position'] and i > lo and bool(sig.iloc[i-1]):
            prior = x.iloc[i-1]
            enter(b, float(row.open), float(prior.atr), int(prior.time+tf['seconds']),
                  now, prior.regime, c, stress)
        if b['position']:
            b['position']['bars'] += 1
            hit = bar_exit(b['position'], row, tf['hold'])
            if hit:
                trades.append(exit_trade(b, hit[0], now+tf['seconds'], hit[1], c, stress))
        b['curve'].append(dict(time=now+tf['seconds'], equity=risk(b, float(row.close), now, c)))
    if b['position']:
        row = x.iloc[hi-1]
        trades.append(exit_trade(b, float(row.close), int(row.time+tf['seconds']), 'evaluation_boundary', c, stress))
        b['curve'][-1]['equity'] = b['cash']
    return trades, b['curve']


def metrics(trades, curve, c):
    n = len(trades)
    pnl = np.array([t['net_pnl'] for t in trades], dtype=float)
    values = np.array([p['equity'] for p in curve], dtype=float)
    wins = int((pnl > 0).sum())
    wr, low, high = (wins/n if n else None), None, None
    if n:
        z, denom = 1.96, 1+1.96**2/n
        center = (wr+z*z/(2*n))/denom
        half = z*math.sqrt(wr*(1-wr)/n+z*z/(4*n*n))/denom
        low, high = max(0, center-half), min(1, center+half)
    losses, gains = float(-pnl[pnl < 0].sum()), float(pnl[pnl > 0].sum())
    pf = gains/losses if losses else None
    expectancy = float(pnl.mean()) if n else None
    status = 'INSUFFICIENT_SAMPLE' if n < c['min_review_trades'] else (
        'RESEARCH_ONLY_NOT_LIVE_APPROVAL' if expectancy > 0 and gains > losses else 'NO_OBSERVED_NET_EDGE')
    return dict(closed_trades=n, wins=wins, win_rate=wr, win_rate_low95=low, win_rate_high95=high,
                net_pnl=float(pnl.sum()), net_return=float(values[-1]/c['initial_equity']-1),
                expectancy_usd=expectancy, profit_factor=pf,
                expectancy_r=float(np.mean([t['net_r'] for t in trades])) if n else None,
                max_drawdown=float(np.max(1-values/np.maximum.accumulate(values))),
                total_fees=float(sum(t['entry_fee']+t['exit_fee'] for t in trades)),
                boundary_exits=sum(t['reason'] == 'evaluation_boundary' for t in trades), review=status)


def splits(n, warm, purge):
    a, b = warm+int((n-warm)*.6), warm+int((n-warm)*.8)
    parts = [('train', warm, a-purge), ('validation', a, b-purge), ('holdout', b, n)]
    if min(hi-lo for _, lo, hi in parts) < max(30, purge):
        raise ValueError('Insufficient data for purged chronological split')
    return parts


def walk_forward(x, sigs, tf, c):
    warm, n, out = c['warmup'], len(x), []
    usable = n-warm
    for fraction in [.4, .5, .6, .7]:
        start = warm+int(usable*fraction)
        end = min(warm+int(usable*.8), warm+int(usable*(fraction+.1)))
        train_start = max(warm, start-int(usable*.3))
        train_end = start-tf['hold']-1
        if train_end-train_start < 30 or end-start < 10:
            continue
        candidates = []
        for name, sig in sigs.items():
            t, curve = backtest(x, sig, train_start, train_end, tf, c)
            m = metrics(t, curve, c)
            if m['closed_trades'] >= 10 and m['expectancy_usd'] > 0 and (m['profit_factor'] or 0) > 1:
                candidates.append((m['net_return']-m['max_drawdown'], name))
        chosen = max(candidates)[1] if candidates else 'CASH'
        if chosen == 'CASH':
            t, curve = [], new_book(c)['curve']
        else:
            t, curve = backtest(x, sigs[chosen], start, end, tf, c)
        out.append(dict(fold=len(out)+1, selected_strategy=chosen,
                        selection_end=int(x.iloc[train_end-1].time+tf['seconds']),
                        test_start=int(x.iloc[start].time), test_end=int(x.iloc[end-1].time+tf['seconds']),
                        **metrics(t, curve, c)))
    return out


def research(c, output, products=None, timeframes=None, days=None):
    out = Path(output)
    (out/'market_data').mkdir(parents=True, exist_ok=True)
    market = PublicMarket()
    now = int(time.time())
    rows, trades, curves, folds, datasets, errors = [], [], [], [], [], []
    for product in products or c['products']:
        for label in timeframes or c['timeframes']:
            tf = c['timeframes'][label]
            try:
                identity = market.product(product)
                end = now//tf['seconds']*tf['seconds']
                start = end-int(days or tf['days'])*86400
                d = market.candles(product, tf['seconds'], start, end)
                snapshot = d.to_csv(index=False)
                (out/'market_data'/f'{product}-{label}.csv').write_text(snapshot)
                x = features(d)
                parts = splits(len(x), c['warmup'], tf['hold']+1)
                sigs = {name: signals(x, name) for name in c['strategies']}
                for name, sig in sigs.items():
                    for split, lo, hi in parts:
                        for scenario, stress in [('base', 1), ('stress', c['stress_multiplier'])]:
                            t, curve = backtest(x, sig, lo, hi, tf, c, stress)
                            meta = dict(product=product, timeframe=label, strategy=name, split=split, scenario=scenario)
                            rows.append(dict(**meta, **metrics(t, curve, c)))
                            trades.extend(dict(**meta, **r) for r in t)
                            curves.extend(dict(**meta, **r) for r in curve)
                for split, lo, hi in parts:
                    fee = c['fee_bps']/10000
                    buy = float(x.iloc[lo].open)*(1+friction(c))
                    sell = float(x.iloc[hi-1].close)*(1-friction(c))
                    for name, ret in [('cash', 0), ('buy_and_hold', sell*(1-fee)/(buy*(1+fee))-1)]:
                        rows.append(dict(product=product, timeframe=label, strategy=name, split=split,
                                         scenario='base', net_return=ret, review='BENCHMARK_DIFFERENT_EXPOSURE'))
                folds.extend(dict(product=product, timeframe=label, **r) for r in walk_forward(x, sigs, tf, c))
                datasets.append(dict(product=product, timeframe=label, identity=identity, start=start, end=end,
                                     rows=len(d), sha256=hashlib.sha256(snapshot.encode()).hexdigest()))
            except Exception as exc:
                errors.append(dict(product=product, timeframe=label, error=str(exc)))
    for name, data in [('metrics', rows), ('trades', trades), ('equity', curves), ('walk_forward', folds), ('errors', errors)]:
        csv(data, out/f'{name}.csv')
    atomic_json(out/'manifest.json', dict(mode='simulation_only', generated_at=time.time(), engine_version=ENGINE_VERSION,
        code_sha=os.getenv('GITHUB_SHA', 'local'), config_hash=digest(c), configuration=c, datasets=datasets, errors=errors,
        hypotheses=len(c['strategies'])*len(products or c['products'])*len(timeframes or c['timeframes']),
        warning='Descriptive trials, no multiple-testing-adjusted significance or live promotion.'))
    lines = ['# Crypto research', '', 'Independent simulated books. No proven winning percentage.',
             f'Completed datasets: {len(datasets)}. Quarantined errors: {len(errors)}.', '',
             '| Product | Bar | Strategy | Trades | Win rate | Net return | Drawdown | Status |',
             '|---|---|---|---:|---:|---:|---:|---|']
    for r in rows:
        if r['split'] == 'holdout' and r['scenario'] == 'base' and r['strategy'] in c['strategies']:
            wr = 'n/a' if r['win_rate'] is None else f"{r['win_rate']:.1%}"
            lines.append(f"| {r['product']} | {r['timeframe']} | {r['strategy']} | {r['closed_trades']} | {wr} | {r['net_return']:.2%} | {r['max_drawdown']:.2%} | {r['review']} |")
    lines += ['', 'All trials, fees, stress scenarios and errors are in CSV. Repeated holdout tuning contaminates it.',
              'Wilson intervals do not correct for correlated trades or multiple testing. Do not sum independent books.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    if not datasets:
        raise RuntimeError('No valid datasets. No results invented; see errors.csv')


def event(state, payload):
    payload = dict(payload, previous_hash=state['tail_hash'])
    h = digest(payload)
    state['events'].append(dict(payload, hash=h))
    state['tail_hash'] = h


def load_state(path, c):
    if not Path(path).exists():
        return dict(engine_version=ENGINE_VERSION, config_hash=digest(c), books={}, trades=[], events=[],
                    tail_hash='0'*64, last_run=None, runs=0)
    s = json.loads(Path(path).read_text())
    if s.get('engine_version') != ENGINE_VERSION or s.get('config_hash') != digest(c):
        raise ValueError('Experiment version/config changed: archive and explicitly start new state')
    previous = '0'*64
    for e in s['events']:
        payload = {k: v for k, v in e.items() if k != 'hash'}
        if payload.get('previous_hash') != previous or digest(payload) != e['hash']:
            raise ValueError('Ledger integrity mismatch')
        previous = e['hash']
    if previous != s['tail_hash']:
        raise ValueError('Ledger tail mismatch')
    return s


def paper(c, state_path, output, paused=False, market=None):
    state = load_state(state_path, c)
    market = market or PublicMarket()
    started = time.time()
    if state['last_run'] and started <= state['last_run']:
        raise ValueError('Non-increasing observation timestamp')
    gap = started-state['last_run'] if state['last_run'] else None
    gap_block = gap is not None and gap > c['max_observation_gap']
    rows, quotes, observations, errors = [], [], [], []
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    for product in c['products']:
        try:
            market.product(product)
        except Exception as exc:
            errors.append(dict(product=product, stage='identity', error=str(exc)))
            continue
        prepared = {}
        for label, tf in c['timeframes'].items():
            try:
                end = int(time.time()//tf['seconds']*tf['seconds'])
                d = market.candles(product, tf['seconds'], end-(c['warmup']+5)*tf['seconds'], end)
                x = features(d)
                prepared[label] = (x, {name: signals(x, name) for name in c['strategies']})
            except Exception as exc:
                errors.append(dict(product=product, timeframe=label, stage='candles', error=str(exc)))
        try:
            q = market.quote(product, c['max_quote_age'])
            quotes.append(dict(product=product, **q))
        except Exception as exc:
            errors.append(dict(product=product, stage='quote', error=str(exc)))
            continue
        now = q['observed_at']
        for label, tf in c['timeframes'].items():
            data = prepared.get(label)
            for strategy in c['strategies']:
                key = f'{product}|{label}|{strategy}'
                b = state['books'].setdefault(key, new_book(c))
                risk(b, q['bid'], now, c)
                closed = False
                p = b['position']
                if p:
                    p['bars'] = int((now-p['entry_time'])//tf['seconds'])
                    reason = ('observed_quote_stop' if q['bid'] <= p['stop'] else
                              'observed_quote_target' if q['bid'] >= p['target'] else
                              'observed_quote_time' if now-p['entry_time'] >= tf['seconds']*tf['hold'] else None)
                    if data:
                        x = data[0]
                        unseen = x[(x.time >= p['entry_time']) & (x.time > (b['last_candle'] or 0))]
                        b['missed_level_bars'] += int(((unseen.low <= p['stop']) | (unseen.high >= p['target'])).sum())
                    if reason:
                        t = exit_trade(b, q['bid'], now, reason, c, quoted=True)
                        state['trades'].append(dict(book=key, **t))
                        event(state, dict(kind='close', book=key, trade=t))
                        closed = True
                if data:
                    x, sigs = data
                    stamp = int(x.iloc[-1].time+tf['seconds'])
                    if bool(sigs[strategy].iloc[-1]) and b['consumed_signal'] != stamp:
                        b['consumed_signal'] = stamp
                        fresh = 0 <= now-stamp <= min(tf['seconds'], 1200)
                        accepted = False
                        if fresh and not gap_block and not paused and not closed and q['spread_bps'] <= c['max_spread_bps']:
                            accepted = enter(b, q['ask'], float(x.iloc[-1].atr), stamp, now, x.iloc[-1].regime, c, quoted=True)
                        observation = dict(book=key, signal_time=stamp, observed_at=now, delay_seconds=now-stamp,
                                           accepted=accepted, fresh=fresh, paused=paused or gap_block, spread_bps=q['spread_bps'])
                        observations.append(observation)
                        event(state, dict(kind='signal_observation', **observation))
                        if accepted:
                            event(state, dict(kind='open', book=key, position=b['position'].copy()))
                    b['last_candle'] = int(x.iloc[-1].time)
                eq = risk(b, q['bid'], now, c)
                b['curve'].append(dict(time=now, equity=eq))
                ts = [t for t in state['trades'] if t['book'] == key]
                rows.append(dict(book=key, equity=eq, cash=b['cash'], position=b['position'] is not None,
                                 missed_level_bars=b['missed_level_bars'], daily_paused=b['daily_paused'],
                                 drawdown_paused=b['drawdown_paused'], **metrics(ts, b['curve'], c)))
    state.update(last_run=started, runs=state['runs']+1)
    event(state, dict(kind='heartbeat', observed_at=started, gap_seconds=gap, entry_pause=paused or gap_block,
                     fresh_products=len(quotes), errors=len(errors), code_sha=os.getenv('GITHUB_SHA', 'local')))
    atomic_json(state_path, state)
    for name, data in [('books', rows), ('trades', state['trades']), ('quotes', quotes), ('signals', observations), ('errors', errors)]:
        csv(data, out/f'{name}.csv')
    atomic_json(out/'status.json', dict(mode='simulation_only', observed_at=started, fresh_products=len(quotes),
                                      errors=errors, runs=state['runs'], entries_paused=paused or gap_block))
    lines = ['# Forward paper observation', '', 'Independent simulated books; no real orders.',
             f'Fresh products: {len(quotes)}. Errors: {len(errors)}. Entries paused: {paused or gap_block}.', '',
             '| Book | Open | Trades | Win rate | Net P&L | Equity |', '|---|---|---:|---:|---:|---:|']
    for r in rows:
        wr = 'n/a' if r['win_rate'] is None else f"{r['win_rate']:.1%}"
        lines.append(f"| {r['book']} | {r['position']} | {r['closed_trades']} | {wr} | {r['net_pnl']:.2f} | {r['equity']:.2f} |")
    lines += ['', 'Quotes determine fills, not historical intrabar touches. Missing quotes leave positions unevaluated.',
              'This coarse observation is NOT continuous scalp execution. No guaranteed win rate.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    if not quotes:
        raise RuntimeError('No fresh quotes. Heartbeat persisted; no invented executions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config.json')
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('research')
    r.add_argument('--products', nargs='+')
    r.add_argument('--timeframes', nargs='+')
    r.add_argument('--days', type=int)
    r.add_argument('--output', default='output/research')
    p = sub.add_parser('paper')
    p.add_argument('--state', default='state/state.json')
    p.add_argument('--output', default='output/paper')
    p.add_argument('--pause-entries', action='store_true')
    args = parser.parse_args()
    c = config(args.config)
    if args.command == 'research':
        if args.products and not set(args.products) <= set(c['products']):
            parser.error('Products must be configured explicit identifiers')
        if args.timeframes and not set(args.timeframes) <= set(c['timeframes']):
            parser.error('Unknown timeframe')
        if args.days is not None and not 1 <= args.days <= 1460:
            parser.error('Days must be 1..1460')
        research(c, args.output, args.products, args.timeframes, args.days)
    else:
        paper(c, args.state, args.output, args.pause_entries or os.getenv('CRYPTO_PAUSE_ENTRIES', '').lower() == 'true')


if __name__ == '__main__':
    main()
