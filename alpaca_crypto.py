"""Dedicated-account Alpaca crypto PAPER execution; never routes to a live host."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import requests
from paper_report import table, write_csv

PAPER = 'https://paper-api.alpaca.markets'
DATA = 'https://data.alpaca.markets'
TERMINAL = {'filled', 'canceled', 'expired', 'rejected'}
PREFIX = 'csl2-'


class SafetyError(RuntimeError):
    pass


class BrokerHTTPError(SafetyError):
    def __init__(self, status):
        self.status = status
        super().__init__(f'Broker HTTP {status}; response body withheld')


def number(value, positive=False):
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise SafetyError('Invalid numeric broker value')
    return result


def dec(value):
    number(value)
    return Decimal(str(value))


def symbol(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Z0-9]{2,12}/USD', value):
        raise SafetyError('Only explicit crypto USD pairs allowed')
    return value


def canonical(value):
    return value.replace('/', '').replace('-', '')


def utc(stamp):
    return datetime.fromtimestamp(stamp, timezone.utc).isoformat(timespec='seconds')


def stamp(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()


def load(path):
    if not Path(path).exists():
        return dict(version=1, paper_only=True, observations=[])
    state = json.loads(Path(path).read_text())
    if (state.get('version') != 1 or state.get('paper_only') is not True
            or not isinstance(state.get('observations'), list)):
        raise SafetyError('Broker state invalid; never reset automatically')
    for key, kind in [('orders', dict), ('cycles', list), ('seen', dict)]:
        if key in state and not isinstance(state[key], kind):
            raise SafetyError('Malformed execution ledger')
    return state


def settings(path='alpaca_config.json'):
    from cryptolab import STRATEGIES
    c = json.loads(Path(path).read_text())
    if c.get('paper_only') is not True:
        raise SafetyError('Only paper execution supported')
    for s in c['symbols']:
        symbol(s)
    if not c['symbols'] or len(set(c['symbols'])) != len(c['symbols']):
        raise SafetyError('Symbols must be nonempty and unique')
    if not c['strategies'] or not set(c['strategies']) <= set(STRATEGIES):
        raise SafetyError('Unknown strategy')
    if not c['timeframes'] or not set(c['timeframes']) <= {'5m', '15m', '1h', '6h'}:
        raise SafetyError('Unknown timeframe')
    for k in ('max_trade_notional_usd', 'max_total_notional_usd', 'max_positions',
              'max_quote_age', 'max_spread_bps', 'pending_timeout_seconds'):
        number(c[k], True)
    if not 0 < c['risk_fraction'] < 1 or not 0 < c['daily_loss_pause'] < 1:
        raise SafetyError('Invalid risk fraction')
    if not 0 < c['drawdown_pause'] < 1 or not 0 <= c['estimated_fee_bps'] < 1000:
        raise SafetyError('Invalid drawdown or estimated fee')
    if c['max_quote_age'] > 30 or not 0 < c['max_signal_price_deviation'] < 1:
        raise SafetyError('Invalid quote age or venue-deviation filter')
    return c


class API:
    def __init__(self, key, secret, writes=False):
        if not key or not secret:
            raise SafetyError('Missing paper credentials')
        self.session = requests.Session()
        self.session.headers.update({'APCA-API-KEY-ID': key, 'APCA-API-SECRET-KEY': secret})
        self.verified = False
        self.writes = writes
        self.max_quote_age = 30

    def call(self, method, path, params=None, data=False, payload=None):
        reads = {'/v2/account', '/v2/assets', '/v2/orders', '/v2/positions',
                 '/v2/orders:by_client_order_id', '/v2/account/activities/CFEE',
                 '/v1beta3/crypto/us/latest/quotes'}
        order_path = bool(re.fullmatch(r'/v2/orders/[a-fA-F0-9-]{32,36}', path))
        allowed = (method == 'GET' and (path in reads or order_path)
                   or method == 'POST' and path == '/v2/orders'
                   or method == 'DELETE' and order_path)
        if not allowed or data != path.startswith('/v1beta3/'):
            raise SafetyError('Endpoint or method not permitted')
        if method != 'GET':
            if not self.verified or not self.writes:
                raise SafetyError('Paper account verification and execution mode required')
            if method == 'POST':
                self.validate_order(payload)
        try:
            kwargs = dict(params=params, timeout=(5, 25), allow_redirects=False)
            if payload is not None:
                kwargs['json'] = payload
            response = self.session.request(method, (DATA if data else PAPER)+path, **kwargs)
        except requests.RequestException:
            raise SafetyError('Broker transport error; order outcome may be unknown; reconcile next run') from None
        if response.status_code not in (200, 201, 204):
            raise BrokerHTTPError(response.status_code)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            raise SafetyError('Unexpected broker JSON; reconcile before any new order') from None

    @staticmethod
    def validate_order(payload):
        if not isinstance(payload, dict):
            raise SafetyError('Order payload required')
        if set(payload) != {'symbol', 'side', 'qty', 'type', 'time_in_force', 'client_order_id'}:
            raise SafetyError('Only explicit simple crypto quantity orders permitted')
        symbol(payload['symbol'])
        if (payload['side'] not in ('buy', 'sell') or payload['type'] != 'market'
                or payload['time_in_force'] != 'gtc'
                or not re.fullmatch(r'csl2-[a-f0-9]{32}', payload['client_order_id'])):
            raise SafetyError('Invalid crypto order')
        number(payload['qty'], True)

    def account(self, expected):
        self.verified = False
        if not expected or not re.fullmatch(r'[a-fA-F0-9-]{32,36}', expected):
            raise SafetyError('Expected paper account API id required')
        account = self.call('GET', '/v2/account')
        if (account.get('id') != expected or account.get('status') != 'ACTIVE'
                or account.get('crypto_status') != 'ACTIVE' or account.get('currency') != 'USD'
                or any(account.get(k) is not False for k in
                       ('trading_blocked', 'account_blocked', 'trade_suspended_by_user'))):
            raise SafetyError('Paper account identity or crypto permissions not verified')
        number(account['equity'], True)
        number(account['cash'])
        self.verified = True
        return account

    def assets(self):
        rows = self.call('GET', '/v2/assets', params={'status': 'active', 'asset_class': 'crypto'})
        return {symbol(row['symbol']): row for row in rows if row.get('class') == 'crypto'
                and row.get('status') == 'active' and row.get('tradable') is True
                and row.get('symbol', '').endswith('/USD')}

    def latest(self, symbols, now):
        wanted = [symbol(s) for s in symbols]
        if not wanted:
            return {}
        raw = self.call('GET', '/v1beta3/crypto/us/latest/quotes',
                        params={'symbols': ','.join(wanted)}, data=True)
        result = {}
        for s in wanted:
            q = raw.get('quotes', {}).get(s)
            if not q:
                continue
            bid, ask = number(q['bp'], True), number(q['ap'], True)
            age = now-stamp(q['t'])
            if ask >= bid and 0 <= age <= self.max_quote_age:
                result[s] = dict(symbol=s, bid=bid, ask=ask, provider_time_utc=q['t'],
                                 spread_bps=(ask-bid)/((ask+bid)/2)*10000)
        return result

    def lookup(self, cid):
        try:
            return self.call('GET', '/v2/orders:by_client_order_id', params={'client_order_id': cid})
        except BrokerHTTPError as exc:
            if exc.status == 404:
                return None
            raise

    def snapshot(self):
        positions = self.call('GET', '/v2/positions')
        orders = self.call('GET', '/v2/orders', params={'status': 'open', 'limit': 500, 'nested': 'false'})
        if len(orders) >= 500:
            raise SafetyError('Open order snapshot may be truncated')
        return positions, orders

    def fees(self, after):
        rows, token = [], None
        for _ in range(100):
            params = dict(after=after, direction='asc', page_size=100)
            if token:
                params['page_token'] = token
            page = self.call('GET', '/v2/account/activities/CFEE', params=params)
            if not isinstance(page, list):
                raise SafetyError('Invalid fee response')
            rows.extend(page)
            if len(page) < 100:
                return rows
            next_token = page[-1]['id']
            if next_token == token:
                break
            token = next_token
        raise SafetyError('Fee pagination incomplete')


def inventory(api):
    positions, orders = api.snapshot() if isinstance(api, API) else (
        api.call('GET', '/v2/positions'),
        api.call('GET', '/v2/orders', params={'status': 'open', 'limit': 500, 'nested': 'false'}))
    if len(orders) >= 500:
        raise SafetyError('Open order snapshot may be truncated; manual review required')
    crypto = lambda row: row.get('asset_class') == 'crypto' or '/' in row.get('symbol', '')
    return dict(total_positions=len(positions), total_open_orders=len(orders),
                crypto_positions=sum(map(crypto, positions)), crypto_open_orders=sum(map(crypto, orders)))


class Store:
    def __init__(self, path, state, checkpoint_script=None):
        self.path, self.state, self.script = path, state, checkpoint_script

    def save(self, remote=False):
        from cryptolab import atomic_json
        atomic_json(self.path, self.state)
        if remote and os.getenv('GITHUB_ACTIONS') == 'true' and not self.script:
            raise SafetyError('Durable checkpoint script required on GitHub before an order')
        if remote and self.script:
            result = subprocess.run(['bash', self.script], capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise SafetyError('Remote ledger checkpoint failed; no further broker writes')


def client_id(account_id, key):
    return PREFIX+hashlib.sha256((account_id+'|'+key).encode()).hexdigest()[:32]


def apply_order(local, raw):
    payload = local['payload']
    if (raw.get('client_order_id') != payload['client_order_id']
            or canonical(raw.get('symbol', '')) != canonical(payload['symbol'])
            or raw.get('side') != payload['side'] or raw.get('type') != 'market'
            or raw.get('time_in_force') != 'gtc'
            or dec(raw['qty']) != dec(payload['qty'])):
        raise SafetyError('Broker order identity mismatch')
    filled = dec(raw.get('filled_qty') or '0')
    if filled < dec(local.get('filled_qty', 0)) or not 0 <= filled <= dec(payload['qty']):
        raise SafetyError('Non-monotonic or invalid order fills')
    price = number(raw['filled_avg_price'], True) if filled else None
    local.update(broker_order_id=raw['id'], status=raw['status'], filled_qty=str(filled),
                 filled_avg_price=price, filled_at=raw.get('filled_at'),
                 broker_updated_at=raw.get('updated_at'))


def reconcile_orders(api, store):
    for cid, local in store.state['orders'].items():
        if local.get('status') in TERMINAL:
            continue
        raw = api.lookup(cid)
        if raw is not None:
            apply_order(local, raw)
        elif local.get('attempted'):
            raise SafetyError('Ambiguous submitted order '+cid+'; inspect broker before retrying; no automatic resubmission')
        else:
            local['status'] = 'canceled'
    store.save()


def submit_intent(api, store, payload, cycle_id, now):
    API.validate_order(payload)
    cid = payload['client_order_id']
    orders = store.state['orders']
    if cid not in orders:
        orders[cid] = dict(payload=payload, cycle_id=cycle_id, status='queued',
                           created_at=now, attempted=False, filled_qty='0')
    elif orders[cid]['payload'] != payload:
        raise SafetyError('Client id reused for different order')
    local = orders[cid]
    if local.get('status') in TERMINAL or local.get('attempted'):
        return local
    raw = api.lookup(cid)
    if raw is not None:
        apply_order(local, raw)
        store.save(remote=True)
        return local
    local['attempted'] = True
    store.save(remote=True)
    try:
        raw = api.call('POST', '/v2/orders', payload=payload)
    except BrokerHTTPError as exc:
        raw = api.lookup(cid)
        if raw is None:
            local['last_http_error'] = exc.status
            if exc.status in (400, 401, 403, 404):
                local['status'] = 'rejected'
            store.save(remote=True)
            raise
    if raw is None:
        raise SafetyError('Unknown order result; automatic new orders blocked')
    apply_order(local, raw)
    store.save(remote=True)
    return local


def round_qty(qty, increment):
    step = dec(increment)
    if step <= 0:
        raise SafetyError('Invalid broker quantity increment')
    return (dec(qty)/step).to_integral_value(rounding=ROUND_DOWN)*step


def update_fees(api, store):
    s = store.state
    rows = api.fees(s['fee_after'])
    ignored = set(s['baseline_fee_ids'])
    s['fees'] = {r['id']: r for r in rows if r['id'] not in ignored}


def owned_positions(api, store):
    s = store.state
    positions, opened = api.snapshot()
    if any(o.get('client_order_id') not in s['orders'] for o in opened):
        raise SafetyError('Foreign open order in dedicated account; not canceled or adopted')
    expected = {}
    for o in s['orders'].values():
        p = o['payload']
        key = canonical(p['symbol'])
        expected[key] = expected.get(key, Decimal(0)) + dec(o.get('filled_qty', 0))*(1 if p['side'] == 'buy' else -1)
    for f in s.get('fees', {}).values():
        q = dec(f.get('qty') or '0')
        if q:
            key = canonical(f.get('symbol', ''))
            if key not in expected:
                raise SafetyError('Unattributable crypto fee activity')
            expected[key] += q
    actual = {}
    for p in positions:
        key = canonical(p['symbol'])
        qty = dec(p['qty'])
        if key in actual or qty < 0:
            raise SafetyError('Duplicate or short broker position')
        actual[key] = p
    for key in set(expected) | set(actual):
        qty = dec(actual[key]['qty']) if key in actual else Decimal(0)
        if abs(qty-expected.get(key, Decimal(0))) > Decimal('0.00000001'):
            raise SafetyError('Position/fee reconciliation mismatch for '+key+'; wait for fees or review manual activity')
    return actual, opened


def activate(api, store, positions, orders, now):
    s = store.state
    if s.get('execution_initialized'):
        return
    if positions or orders:
        raise SafetyError('First execution requires an empty dedicated paper account; no adoption')
    after = datetime.fromtimestamp(now, timezone.utc).strftime('%Y-%m-%dT00:00:00Z')
    baseline = api.fees(after)
    s.update(execution_initialized=True, activated_at=now, fee_after=after,
             baseline_fee_ids=[r['id'] for r in baseline], fees={}, orders={}, cycles=[], seen={})
    store.save(remote=True)


def cycle_orders(state, cycle):
    return [o for o in state['orders'].values() if o['cycle_id'] == cycle['id']]


def refresh_cycles(state, actual, now):
    for c in state['cycles']:
        if c['status'] == 'closed':
            continue
        orders = cycle_orders(state, c)
        buy = next((o for o in orders if o['payload']['side'] == 'buy'), None)
        if not buy:
            continue
        q = number(buy.get('filled_qty', 0))
        if q:
            entry = number(buy['filled_avg_price'], True)
            c.update(entry_price=entry, entry_qty=q, entry_notional_usd=entry*q, tp=entry+c['distance']*c['target_r'],
                     sl=entry-c['distance'], entry_time_utc=buy.get('filled_at') or utc(buy['created_at']))
        pos = actual.get(canonical(c['symbol']))
        c['remaining_qty'] = number(pos['qty']) if pos else 0.
        if any(o['status'] not in TERMINAL for o in orders):
            c['status'] = 'pending'
        elif not q:
            c.update(status='closed', exit_reason='unfilled_entry', closed_at=utc(now))
        elif pos is None or dec(pos['qty']) == 0:
            sells = [o for o in orders if o['payload']['side'] == 'sell']
            proceeds = sum(number(o.get('filled_qty', 0))*(o.get('filled_avg_price') or 0) for o in sells)
            c.update(status='closed', closed_at=utc(now),
                     cashflow_pnl_before_usd_fees=proceeds-q*c['entry_price'],
                     exit_reason=c.get('exit_reason', 'reconciled_zero_position'))
        else:
            c['status'] = 'dust_or_unavailable' if c.get('status') == 'dust_or_unavailable' else 'open'


def portfolio_pause(state, account, cfg, now):
    eq = number(account['equity'], True)
    day = utc(now)[:10]
    if state.get('day') != day:
        state.update(day=day, day_start_equity=eq, daily_paused=False)
    state['high_water'] = max(eq, state.get('high_water', eq))
    state['daily_paused'] = state.get('daily_paused', False) or eq <= state['day_start_equity']*(1-cfg['daily_loss_pause'])
    state['drawdown_paused'] = state.get('drawdown_paused', False) or eq <= state['high_water']*(1-cfg['drawdown_pause'])
    return state['daily_paused'] or state['drawdown_paused']


def candidates(cfg, lab, assets, market, errors):
    from cryptolab import features, signals
    found = []
    for sym in cfg['symbols']:
        if sym not in assets:
            errors.append(dict(symbol=sym, stage='unsupported_asset'))
            continue
        for label in cfg['timeframes']:
            tf = lab['timeframes'][label]
            now = time.time()
            end = int(now//tf['seconds']*tf['seconds'])
            try:
                d = market.candles(sym.replace('/', '-'), tf['seconds'],
                                   end-(lab['warmup']+5)*tf['seconds'], end)
                x = features(d)
                row = x.iloc[-1]
                completed = int(row.time+tf['seconds'])
                if not 0 <= time.time()-completed <= tf['seconds']:
                    raise SafetyError('Stale strategy candles')
                for strategy in cfg['strategies']:
                    if bool(signals(x, strategy).iloc[-1]):
                        found.append(dict(symbol=sym, timeframe=label, strategy=strategy,
                                          signal_time=completed, atr=number(row.atr, True),
                                          signal_close=number(row.close, True),
                                          hold_seconds=tf['seconds']*tf['hold']))
            except Exception as exc:
                errors.append(dict(symbol=sym, timeframe=label, stage='candles', error_type=type(exc).__name__))
    return found


def payload(sym, side, qty, cid):
    return dict(symbol=symbol(sym), side=side, qty=format(dec(qty), 'f'), type='market',
                time_in_force='gtc', client_order_id=cid)


def manage_exits(api, store, cfg, assets):
    s = store.state
    for c in s['cycles']:
        if c['status'] == 'closed':
            continue
        orders = cycle_orders(s, c)
        pending = [o for o in orders if o['status'] not in TERMINAL]
        now = time.time()
        quotes = api.latest([c['symbol']], now)
        q = quotes.get(c['symbol'])
        reason = None
        if q and c.get('entry_price'):
            reason = ('stop' if q['bid'] <= c['sl'] else 'target' if q['bid'] >= c['tp']
                      else 'time' if now-c['created_at'] >= c['hold_seconds'] else None)
        if pending:
            for o in pending:
                if o.get('broker_order_id') and (reason or now-o['created_at'] >= cfg['pending_timeout_seconds']):
                    store.save(remote=True)
                    api.call('DELETE', '/v2/orders/'+o['broker_order_id'])
                    o['cancel_requested_at'] = now
                    store.save(remote=True)
            continue
        if not reason:
            continue
        actual, _ = owned_positions(api, store)
        p = actual.get(canonical(c['symbol']))
        if not p:
            continue
        asset = assets.get(c['symbol'])
        if not asset:
            raise SafetyError('Held asset unavailable; manual broker review required')
        available = min(dec(p['qty']), dec(p.get('qty_available', p['qty'])))
        qty = round_qty(available, asset['min_trade_increment'])
        if qty < dec(asset['min_order_size']):
            c['status'] = 'dust_or_unavailable'
            continue
        sell_count = sum(o['payload']['side'] == 'sell' for o in orders)
        cid = client_id(s['account_id'], c['id']+'|exit|'+str(sell_count))
        c['exit_reason'] = reason
        submit_intent(api, store, payload(c['symbol'], 'sell', qty, cid), c['id'], now)


def execute(api, store, cfg, lab, account, market, errors):
    s = store.state
    positions, opened = api.snapshot()
    activate(api, store, positions, opened, time.time())
    reconcile_orders(api, store)
    update_fees(api, store)
    actual, _ = owned_positions(api, store)
    refresh_cycles(s, actual, time.time())
    assets = api.assets()
    manage_exits(api, store, cfg, assets)
    reconcile_orders(api, store)
    update_fees(api, store)
    actual, _ = owned_positions(api, store)
    refresh_cycles(s, actual, time.time())
    account = api.account(s['account_id'])
    paused = portfolio_pause(s, account, cfg, time.time()) or os.getenv('ALPACA_CRYPTO_PAUSE_ENTRIES', '').lower() == 'true'
    if paused:
        return []
    ideas = candidates(cfg, lab, assets, market, errors)
    for idea in ideas:
        now = time.time()
        sym = idea['symbol']
        token = sym+'|'+idea['timeframe']+'|'+idea['strategy']+'|'+str(idea['signal_time'])
        if token in s['seen']:
            continue
        s['seen'][token] = now
        if now-idea['signal_time'] > lab['timeframes'][idea['timeframe']]['seconds']:
            continue
        active = [c for c in s['cycles'] if c['status'] != 'closed']
        if any(c['symbol'] == sym for c in active) or len(active) >= cfg['max_positions']:
            continue
        if any(c['symbol'] == sym and c.get('closed_at', '')[:10] == utc(now)[:10]
               and now-stamp(c['closed_at']) < 300 for c in s['cycles']):
            continue
        q = api.latest([sym], now).get(sym)
        if not q or q['spread_bps'] > cfg['max_spread_bps']:
            continue
        if abs(q['ask']/idea['signal_close']-1) > cfg['max_signal_price_deviation']:
            continue
        distance = max(idea['atr']*lab['stop_atr'], q['ask']*lab['min_stop'])
        if distance/q['ask'] > lab['max_stop']:
            continue
        account = api.account(s['account_id'])
        actual, _ = owned_positions(api, store)
        exposure = sum(abs(number(p['market_value'])) for p in actual.values())
        reserved = sum(max(0, number(o['payload']['qty'])-number(o.get('filled_qty', 0)))*
                       next(c['reference_ask'] for c in s['cycles'] if c['id'] == o['cycle_id'])
                       for o in s['orders'].values()
                       if o['status'] not in TERMINAL and o['payload']['side'] == 'buy')
        fee = cfg['estimated_fee_bps']/10000
        cash = max(0, min(number(account['cash']), number(account.get('non_marginable_buying_power', account['cash']))))
        budget = min(cfg['max_trade_notional_usd'], cfg['max_total_notional_usd']-exposure-reserved,
                     (cash-reserved)/(1+2*fee))
        unit_risk = distance+2*q['ask']*fee
        qty = round_qty(min(max(0, budget)/q['ask'], number(account['equity'])*cfg['risk_fraction']/unit_risk),
                        assets[sym]['min_trade_increment'])
        if qty < dec(assets[sym]['min_order_size']):
            continue
        cid = client_id(s['account_id'], token)
        cycle = dict(idea, id=cid, created_at=now, status='pending', distance=distance,
                     target_r=lab['target_r'], reference_ask=q['ask'], remaining_qty=0.)
        s['cycles'].append(cycle)
        order = submit_intent(api, store, payload(sym, 'buy', qty, cid), cid, now)
        order['reference_ask'] = q['ask']
        reconcile_orders(api, store)
        update_fees(api, store)
        actual, _ = owned_positions(api, store)
        refresh_cycles(s, actual, time.time())
        store.save(remote=True)
    return ideas


def report(state, status, quotes, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out/'quotes.csv', list(quotes.values()), ['symbol', 'bid', 'ask', 'provider_time_utc'])
    rows = []
    for cid, o in state.get('orders', {}).items():
        c = next((c for c in state.get('cycles', []) if c['id'] == o['cycle_id']), {})
        rows.append(dict(o['payload'], broker_order_id=o.get('broker_order_id'), status=o['status'],
                         filled_qty=o.get('filled_qty'), filled_avg_price=o.get('filled_avg_price'),
                         filled_at=o.get('filled_at'), timeframe=c.get('timeframe'), strategy=c.get('strategy'),
                         tp=c.get('tp'), sl=c.get('sl'), created_at_utc=utc(o['created_at'])))
    write_csv(out/'orders.csv', rows, ['symbol', 'timeframe', 'strategy', 'side', 'qty', 'filled_qty',
              'filled_avg_price', 'tp', 'sl', 'status', 'client_order_id', 'broker_order_id', 'created_at_utc', 'filled_at'])
    fields = ['symbol', 'timeframe', 'strategy', 'entry_time_utc', 'entry_price', 'entry_qty',
              'entry_notional_usd', 'remaining_qty', 'tp', 'sl', 'status', 'closed_at', 'exit_reason', 'cashflow_pnl_before_usd_fees']
    opened = [c for c in state.get('cycles', []) if c['status'] != 'closed']
    closed = [c for c in state.get('cycles', []) if c['status'] == 'closed']
    write_csv(out/'open_positions.csv', opened, fields)
    write_csv(out/'closed_trades.csv', closed, fields)
    write_csv(out/'fees.csv', list(state.get('fees', {}).values()),
              ['id', 'activity_type', 'date', 'symbol', 'qty', 'price', 'net_amount', 'description'])
    (out/'status.json').write_text(json.dumps(status, indent=2)+'\n')
    lines = ['# Alpaca crypto PAPER bot', '', 'Status: '+status['status'],
             'Dedicated paper account only. Broker fills, not virtual experiment fills.',
             'TP/SL are software checks at workflow runs, NOT standing bracket orders.',
             'Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.',
             'Fees can post later. P&L below is before USD fees; no fabricated net performance.', '']
    if status.get('reason'):
        lines += ['Reason: '+status['reason'], '']
    for title, values in [('Open / pending positions', opened), ('Closed cycles', closed)]:
        lines += ['## '+title, '']
        lines += table(['Coin', 'Bar', 'Strategy', 'Entry', 'Filled qty', 'Entry dollars', 'Remaining', 'TP', 'SL', 'Status'],
                       [[c.get(k, 'n/a') for k in ('symbol', 'timeframe', 'strategy', 'entry_price',
                         'entry_qty', 'entry_notional_usd', 'remaining_qty', 'tp', 'sl', 'status')] for c in values])
    lines += ['', 'Order IDs, fill prices/times and quantities: orders.csv.',
              'Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.',
              'Dust is kept in the ledger; it is not silently written off or counted as a win.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    (out/'journal.md').write_text('\n'.join(lines)+'\n')


def run(mode, state_path, output, execution_config='alpaca_config.json', checkpoint_script=None):
    from cryptolab import config, PublicMarket
    if mode not in ('check', 'plan', 'tick'):
        raise SafetyError('Unknown mode')
    state = load(state_path)
    store = Store(state_path, state, checkpoint_script)
    status = dict(status='STARTING', paper_only=True, writes_enabled=False, mode=mode)
    quotes = {}
    try:
        enabled = os.getenv('ALPACA_CRYPTO_PAPER_ENABLED', '').lower() == 'true'
        dedicated = os.getenv('ALPACA_CRYPTO_DEDICATED_ACCOUNT', '').lower() == 'true'
        if mode == 'tick' and (not enabled or not dedicated):
            raise SafetyError('Set paper execution and dedicated-account variables true for tick')
        api = API(os.getenv('ALPACA_PAPER_KEY_ID', ''), os.getenv('ALPACA_PAPER_SECRET_KEY', ''), writes=mode == 'tick')
        expected = os.getenv('ALPACA_EXPECTED_PAPER_ACCOUNT_ID', '')
        account = api.account(expected)
        if state.get('account_id') not in (None, expected):
            raise SafetyError('Persisted account mismatch; use a separate state branch; never relabel an old ledger')
        state['account_id'] = expected
        status.update(account_verified=True, status='PAPER_ACCOUNT_VERIFIED')
        if mode in ('plan', 'tick'):
            cfg = settings(execution_config)
            api.max_quote_age = cfg['max_quote_age']
            lab = config()
            if not set(cfg['timeframes']) <= set(lab['timeframes']):
                raise SafetyError('Timeframes not present in research config')
            errors = []
            if mode == 'tick':
                status['writes_enabled'] = True
                ideas = execute(api, store, cfg, lab, account, PublicMarket(), errors)
                status.update(status='PAPER_TICK_COMPLETED', candidates=len(ideas), data_errors=errors)
            else:
                status.update(inventory(api))
                assets = api.assets()
                quotes = api.latest([s for s in cfg['symbols'] if s in assets], time.time())
                status.update(status='READ_ONLY_PLAN', fresh_quotes=len(quotes), supported_symbols=list(quotes))
    except Exception as exc:
        status.update(status='FAILED_CLOSED', error_type=type(exc).__name__,
                      reason=str(exc) if isinstance(exc, SafetyError) else 'Unexpected error; inspect tests and ledger, details withheld')
        raise SafetyError(status['reason']) from None
    finally:
        status['observed_at_utc'] = utc(time.time())
        state['observations'].append(status.copy())
        store.save()
        report(state, status, quotes, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('check', 'plan', 'tick'), default='check')
    parser.add_argument('--state', default='state/alpaca_state.json')
    parser.add_argument('--output', default='output/alpaca')
    parser.add_argument('--execution-config', default='alpaca_config.json')
    parser.add_argument('--checkpoint-script')
    args = parser.parse_args()
    run(args.mode, args.state, args.output, args.execution_config, args.checkpoint_script)
