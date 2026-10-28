"""Read-only Alpaca PAPER readiness. No order submission, cancellation or live host."""
import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import re
import time
import requests
from paper_report import table, write_csv

PAPER = 'https://paper-api.alpaca.markets'
DATA = 'https://data.alpaca.markets'
SHARED_ACCOUNT_COMPATIBLE = False
POLICY = 'CHATGPTTRADER_OWNERSHIP_CONFLICT'


class SafetyError(RuntimeError):
    pass


def number(value, positive=False):
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise SafetyError('Invalid numeric broker value')
    return result


def symbol(value):
    if not re.fullmatch(r'[A-Z0-9]{2,12}/USD', value):
        raise SafetyError('Only explicit crypto USD pairs allowed')
    return value


def canonical(value):
    return value.replace('/', '').replace('-', '')


def load(path):
    if not Path(path).exists():
        return dict(version=1, paper_only=True, observations=[])
    state = json.loads(Path(path).read_text())
    if (state.get('version') != 1 or state.get('paper_only') is not True
            or not isinstance(state.get('observations'), list)):
        raise SafetyError('Broker state invalid; never reset automatically')
    return state


class API:
    def __init__(self, key, secret):
        if not key or not secret:
            raise SafetyError('Missing paper credentials')
        self.session = requests.Session()
        self.session.headers.update({'APCA-API-KEY-ID': key, 'APCA-API-SECRET-KEY': secret})
        self.verified = False

    def call(self, method, path, params=None, data=False):
        allowed = {'/v2/account', '/v2/assets', '/v2/orders', '/v2/positions',
                   '/v1beta3/crypto/us/latest/quotes'}
        if method != 'GET' or path not in allowed or data != path.startswith('/v1beta3/'):
            raise SafetyError('Read-only endpoints only; no order writes, cancellation or liquidation')
        try:
            response = self.session.request('GET', (DATA if data else PAPER)+path,
                params=params, timeout=(5, 25), allow_redirects=False)
        except requests.RequestException:
            raise SafetyError('Broker transport error; details withheld') from None
        if response.status_code != 200:
            raise SafetyError(f'Broker HTTP {response.status_code}; response body withheld')
        try:
            return response.json()
        except ValueError:
            raise SafetyError('Unexpected broker JSON') from None

    def account(self, expected):
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
            stamp = datetime.fromisoformat(q['t'].replace('Z', '+00:00')).timestamp()
            if ask >= bid and 0 <= now-stamp <= 30 and (ask-bid)/((ask+bid)/2) <= .005:
                result[s] = dict(symbol=s, bid=bid, ask=ask, provider_time_utc=q['t'])
        return result


def inventory(api):
    """Read a snapshot; never adopt, cancel, close, or claim ownership of positions."""
    positions = api.call('GET', '/v2/positions')
    orders = api.call('GET', '/v2/orders', params={'status': 'open', 'limit': 500, 'nested': 'false'})
    if len(orders) >= 500:
        raise SafetyError('Open order snapshot may be truncated; manual review required')
    crypto = lambda row: row.get('asset_class') == 'crypto' or '/' in row.get('symbol', '')
    return dict(total_positions=len(positions), total_open_orders=len(orders),
                crypto_positions=sum(map(crypto, positions)), crypto_open_orders=sum(map(crypto, orders)))


def execute(*args, **kwargs):
    raise SafetyError(POLICY+': existing stock bot rejects crypto orders/positions; no writes')


def report(state, status, quotes, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out/'quotes.csv', list(quotes.values()), ['symbol', 'bid', 'ask', 'provider_time_utc'])
    fields = ['symbol', 'side', 'entry_price', 'qty', 'tp', 'sl', 'broker_order_id', 'status']
    write_csv(out/'orders.csv', [], fields)
    (out/'status.json').write_text(json.dumps(status, indent=2)+'\n')
    lines = ['# Alpaca crypto PAPER readiness', '', 'Status: '+status['status'],
             'Read-only: zero orders submitted by this integration.',
             'Shared account trading is BLOCKED: the unchanged stock coordinator rejects foreign orders/positions.',
             'Changing a repository variable cannot enable writes in this revision.',
             'Use paper-state/journal.md for virtual trade entry, quantity, TP, SL and profit.',
             'Broker readiness is NOT a broker trade journal or proof of profitability.', '',
             '## Latest verified quotes', '']
    lines += table(['Coin', 'Bid', 'Ask', 'Provider UTC'],
                   [[q['symbol'], q['bid'], q['ask'], q['provider_time_utc']] for q in quotes.values()])
    if status.get('reason'):
        lines += ['', 'Reason: '+status['reason']]
    (out/'summary.md').write_text('\n'.join(lines)+'\n')


def run(mode, state_path, output):
    from cryptolab import atomic_json, config
    if mode not in ('check', 'plan'):
        execute()
    state = load(state_path)
    status = dict(status='STARTING', paper_only=True, writes_enabled=False,
                  shared_account_compatible=SHARED_ACCOUNT_COMPATIBLE, submitted_orders=0)
    quotes = {}
    try:
        api = API(os.getenv('ALPACA_PAPER_KEY_ID', ''), os.getenv('ALPACA_PAPER_SECRET_KEY', ''))
        expected = os.getenv('ALPACA_EXPECTED_PAPER_ACCOUNT_ID', '')
        api.account(expected)
        if state.get('account_id') not in (None, expected):
            raise SafetyError('Persisted account mismatch; refusing adoption')
        state['account_id'] = expected
        status['account_verified'] = True
        status['status'] = 'READ_ONLY_ACCOUNT_VERIFIED_SHARED_EXECUTION_BLOCKED'
        if mode == 'plan':
            status.update(inventory(api))
            assets = api.assets()
            wanted = [p.replace('-', '/') for p in config()['products'] if p.replace('-', '/') in assets]
            quotes = api.latest(wanted, time.time())
            status.update(status=POLICY, supported_symbols=wanted, fresh_quotes=len(quotes))
    except Exception as exc:
        status.update(status='FAILED_CLOSED', error_type=type(exc).__name__,
                      reason=str(exc) if isinstance(exc, SafetyError) else 'Unexpected error; details withheld')
        raise SafetyError(status['reason']) from None
    finally:
        state['observations'].append(dict(time=time.time(), **status))
        atomic_json(state_path, state)
        report(state, status, quotes, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('check', 'plan'), default='check')
    parser.add_argument('--state', default='state/alpaca_state.json')
    parser.add_argument('--output', default='output/alpaca')
    args = parser.parse_args()
    run(args.mode, args.state, args.output)
