"""Mechanical regression fixtures; not market-performance evidence."""
import copy
import csv
import json
from unittest.mock import Mock

import pytest
import alpaca_crypto as a
import paper_report as p


@pytest.fixture
def sample():
    pos = dict(qty=2., entry=100., entry_fee=1., target=110., stop=95.,
               entry_time=100., risk_usd=12.)
    state = dict(books={'BTC-USD|15m|trend_pullback': dict(cash=799., position=pos)}, trades=[])
    quotes = [dict(product='BTC-USD', bid=103., observed_at=200., provider_time=199.)]
    config = dict(slippage_bps=5, fee_bps=40, max_quote_age=120)
    status = dict(observed_at=200., fresh_products=1, errors=[], entries_paused=False)
    return state, quotes, config, status


def test_reporting_does_not_modify_state(sample, tmp_path):
    state, quotes, config, status = sample
    before = copy.deepcopy(state)
    opened, closed, books = p.render(state, quotes, config, status, tmp_path)
    assert state == before
    assert len(opened) == 1 and closed == []
    assert books[0]['closed_trades'] == 0 and books[0]['win_rate'] is None
    assert opened[0]['total_entry_cost_usd'] == 201.
    assert opened[0]['tp'] == 110. and opened[0]['sl'] == 95.
    exit_value = 2*103*(1-.0005)
    assert opened[0]['estimated_open_net_pnl_usd'] == pytest.approx(exit_value*.996-201.)
    assert opened[0]['marked_equity_usd'] == 1005.
    assert opened[0]['estimated_liquidation_equity_usd'] < 1005.
    assert '1970-01-01T00:01:40+00:00' == opened[0]['entry_time_utc']


def test_tables_have_consistent_columns(sample, tmp_path):
    p.render(*sample, tmp_path)
    text = (tmp_path/'summary.md').read_text()
    widths = []
    for line in text.splitlines():
        if line.startswith('|'):
            widths.append(line.count('|'))
        elif widths:
            assert len(set(widths)) == 1
            widths = []
    if widths:
        assert len(set(widths)) == 1
    assert 'BTC-USD|15m|' not in text
    assert (tmp_path/'journal.md').read_text() == text


@pytest.mark.parametrize('quotes', [[], [dict(product='BTC-USD', bid=103., observed_at=199., provider_time=199.)],
    [dict(product='BTC-USD', bid=103., observed_at=200., provider_time=0.)],
    [dict(product='BTC-USD', bid='nan', observed_at=200., provider_time=199.)]])
def test_missing_or_stale_quote_not_marked(sample, tmp_path, quotes):
    state, _, config, status = sample
    opened, _, _ = p.render(state, quotes, config, status, tmp_path)
    assert opened[0]['mark_bid'] is None
    assert opened[0]['estimated_open_net_pnl_usd'] is None
    assert opened[0]['marked_equity_usd'] is None
    assert opened[0]['estimated_liquidation_equity_usd'] is None
    assert 'n/a' in (tmp_path/'summary.md').read_text()


def test_closed_journal_and_no_position(sample, tmp_path):
    state, quotes, config, status = sample
    position = state['books']['BTC-USD|15m|trend_pullback']['position']
    state['trades'] = [dict(position, book='BTC-USD|15m|trend_pullback', exit=110.,
        exit_time=200., exit_fee=.88, net_pnl=18.12, net_r=1.51, reason='target')]
    state['books']['BTC-USD|15m|trend_pullback'].update(position=None, cash=1018.12)
    opened, closed, books = p.render(state, quotes, config, status, tmp_path)
    assert opened == [] and closed[0]['tp'] == 110.
    assert books[0]['win_rate'] == 1 and books[0]['realized_net_pnl'] == 18.12
    with (tmp_path/'open_positions.csv').open() as f:
        assert list(csv.DictReader(f)) == []
    with (tmp_path/'closed_trades.csv').open() as f:
        assert len(list(csv.DictReader(f))) == 1


def account():
    return dict(id='00000000-0000-0000-0000-000000000001', status='ACTIVE', crypto_status='ACTIVE',
                currency='USD', trading_blocked=False, account_blocked=False,
                trade_suspended_by_user=False, equity='10000', cash='5000')


def test_account_check_read_only():
    api = a.API('test-key', 'test-secret')
    api.call = Mock(return_value=account())
    api.account(account()['id'])
    assert api.verified
    api.call.assert_called_once_with('GET', '/v2/account')


@pytest.mark.parametrize('field,value', [('id', 'different'), ('status', 'INACTIVE'),
    ('crypto_status', 'INACTIVE'), ('trading_blocked', True), ('account_blocked', True),
    ('trade_suspended_by_user', True), ('equity', 'nan'), ('cash', 'inf'), ('currency', 'CAD')])
def test_invalid_accounts_rejected(field, value):
    api = a.API('key', 'secret')
    row = account()
    row[field] = value
    api.call = Mock(return_value=row)
    with pytest.raises((a.SafetyError, ValueError)):
        api.account(account()['id'])
    assert not api.verified


def test_credentials_and_expected_account_required():
    with pytest.raises(a.SafetyError):
        a.API('', '')
    api = a.API('key', 'secret')
    with pytest.raises(a.SafetyError):
        api.account('')


@pytest.mark.parametrize('method,path', [('DELETE', '/v2/orders'), ('DELETE', '/v2/positions'),
    ('POST', '/v2/orders'), ('GET', 'https://api.alpaca.markets/v2/account'),
    ('GET', '/v2/../account')])
def test_unapproved_api_write_or_path_never_sent(method, path):
    api = a.API('key', 'secret')
    api.session.request = Mock()
    with pytest.raises(a.SafetyError):
        api.call(method, path)
    api.session.request.assert_not_called()


def test_paper_tick_requires_explicit_execution_and_dedicated_account(tmp_path, monkeypatch):
    monkeypatch.delenv('ALPACA_CRYPTO_PAPER_ENABLED', raising=False)
    monkeypatch.delenv('ALPACA_CRYPTO_DEDICATED_ACCOUNT', raising=False)
    with pytest.raises(a.SafetyError, match='dedicated-account'):
        a.run('tick', tmp_path/'state.json', tmp_path/'report')


def test_crypto_inventory_read_only():
    api = Mock()
    api.call.side_effect = [[dict(symbol='SPY', asset_class='us_equity'),
                            dict(symbol='BTCUSD', asset_class='crypto')],
                           [dict(symbol='SPY', asset_class='us_equity')]]
    snapshot = a.inventory(api)
    assert snapshot['total_positions'] == 2 and snapshot['crypto_positions'] == 1
    assert snapshot['crypto_open_orders'] == 0
    assert all(call.args[0] == 'GET' for call in api.call.call_args_list)


def test_truncated_inventory_refused():
    api = Mock()
    api.call.side_effect = [[], [{}]*500]
    with pytest.raises(a.SafetyError, match='truncated'):
        a.inventory(api)


def test_broker_ledger_corruption_refused(tmp_path):
    path = tmp_path/'state.json'
    path.write_text(json.dumps(dict(version=2, paper_only=True, observations=[])))
    with pytest.raises(a.SafetyError):
        a.load(path)
    path.write_text('invalid')
    with pytest.raises(json.JSONDecodeError):
        a.load(path)


def test_quotes_age_spread_and_symbol(monkeypatch):
    api = a.API('key', 'secret')
    api.call = Mock(return_value=dict(quotes={'BTC/USD': dict(bp=100., ap=100.1, t='1970-01-01T00:01:40Z')}))
    monkeypatch.setattr(a.time, 'time', lambda: 101.)
    assert 'BTC/USD' in api.latest(['BTC/USD'], 101.)
    monkeypatch.setattr(a.time, 'time', lambda: 200.)
    assert api.latest(['BTC/USD'], 200.) == {}
    with pytest.raises(a.SafetyError):
        api.latest(['SPY'], 101.)


def test_broker_report_no_fabricated_trades(tmp_path):
    a.report(dict(observations=[]), dict(status='BLOCKED'), {}, tmp_path)
    assert 'BLOCKED' in (tmp_path/'summary.md').read_text()
    with (tmp_path/'orders.csv').open() as f:
        assert list(csv.DictReader(f)) == []
