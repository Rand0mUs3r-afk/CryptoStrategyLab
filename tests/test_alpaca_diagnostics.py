"""Offline regression fixtures for quote receipt timing and entry diagnostics."""
import copy
import csv
import json
from unittest.mock import Mock

import pytest
import alpaca_crypto as a
from test_alpaca_execution import ACCOUNT, account, env, idea


@pytest.mark.parametrize('provider_time,accepted', [
    (100.5, True), (101., True), (71., True), (70.999, False), (102., False),
])
def test_quote_age_is_measured_after_response(monkeypatch, provider_time, accepted):
    api = a.API('fixture', 'fixture')
    clock = {'now': 100.}
    monkeypatch.setattr(a.time, 'time', lambda: clock['now'])

    def response(*args, **kwargs):
        clock['now'] = 101.
        return {'quotes': {'BTC/USD': {'bp': 99.9, 'ap': 100.,
                                     't': a.datetime.fromtimestamp(provider_time, a.timezone.utc).isoformat()}}}

    api.call = Mock(side_effect=response)
    quotes = api.latest(['BTC/USD'], clock['now'])
    assert bool(quotes) is accepted
    if accepted:
        assert quotes['BTC/USD']['age_seconds'] == pytest.approx(101.-provider_time)
    api.call.assert_called_once()


@pytest.mark.parametrize('case,reason', [
    ('missing', 'no_fresh_quote'), ('spread', 'spread_too_wide'),
    ('deviation', 'signal_price_deviation'), ('stop', 'stop_distance_too_large'),
    ('quantity', 'quantity_below_minimum'), ('stale', 'stale_signal'),
    ('active', 'symbol_already_active'), ('positions', 'max_positions'),
    ('cooldown', 'symbol_cooldown'), ('seen', 'already_seen'),
])
def test_each_entry_skip_has_a_reason(env, monkeypatch, case, reason):
    api, store, cfg, lab = env
    monkeypatch.delenv('ALPACA_CRYPTO_PAUSE_ENTRIES', raising=False)
    candidate = idea()
    token = '|'.join([candidate['symbol'], candidate['timeframe'], candidate['strategy'],
                      str(candidate['signal_time'])])
    a.activate(api, store, [], [], a.time.time())
    if case == 'missing':
        api.latest = lambda *args: {}
    elif case == 'spread':
        api.bid = 90.
    elif case == 'deviation':
        candidate['signal_close'] = 90.
    elif case == 'stop':
        candidate['atr'] = 100.
    elif case == 'quantity':
        cfg['max_total_notional_usd'] = .000001
    elif case == 'stale':
        candidate['signal_time'] -= 1800
    elif case in ('active', 'positions'):
        store.state['cycles'] = [dict(id='fixture', symbol='BTC/USD' if case == 'active' else 'ETH/USD',
                                      status='open')]
        monkeypatch.setattr(a, 'manage_exits', lambda *args: None)
        cfg['max_positions'] = 1
    elif case == 'cooldown':
        store.state['cycles'] = [dict(id='fixture', symbol='BTC/USD', status='closed',
                                      closed_at=a.utc(a.time.time()))]
    elif case == 'seen':
        store.state['seen'][token] = a.time.time()
    monkeypatch.setattr(a, 'candidates', lambda *args: [candidate])
    diagnostics, quotes = {}, {}
    result = a.execute(api, store, cfg, lab, account(), None, [], diagnostics, quotes)
    assert result == [candidate] and diagnostics['candidates'] == 1
    assert diagnostics['entry_decisions'][0]['reason'] == reason
    assert diagnostics['entry_decisions'][0]['outcome'] == 'skipped'
    assert api.posts == [] and store.state['orders'] == {}
    if case in ('spread', 'deviation', 'stop', 'quantity'):
        assert quotes['BTC/USD']['ask'] == 100.


def test_seen_skip_is_reported_and_never_replayed(env, monkeypatch):
    api, store, cfg, lab = env
    candidate = idea()
    monkeypatch.setattr(a, 'candidates', lambda *args: [candidate])
    api.latest = Mock(return_value={})
    diagnostics = {}
    a.execute(api, store, cfg, lab, account(), None, [], diagnostics)
    seen = copy.deepcopy(store.state['seen'])
    assert diagnostics['entry_decisions'][0]['reason'] == 'no_fresh_quote'
    a.execute(api, store, cfg, lab, account(), None, [], diagnostics)
    assert diagnostics['entry_decisions'][0]['reason'] == 'already_seen'
    assert store.state['seen'] == seen and api.posts == []
    api.latest.assert_called_once()


@pytest.mark.parametrize('pause,reason', [
    ('variable', 'entries_paused_by_variable'), ('daily', 'daily_loss_pause'),
    ('drawdown', 'drawdown_pause'),
])
def test_pause_reasons_are_distinct_from_no_signals(env, monkeypatch, pause, reason):
    api, store, cfg, lab = env
    monkeypatch.delenv('ALPACA_CRYPTO_PAUSE_ENTRIES', raising=False)
    if pause == 'variable':
        monkeypatch.setenv('ALPACA_CRYPTO_PAUSE_ENTRIES', 'true')
    elif pause == 'daily':
        store.state.update(day=a.utc(a.time.time())[:10], day_start_equity=20000.)
    else:
        store.state['high_water'] = 20000.
    scan = Mock()
    monkeypatch.setattr(a, 'candidates', scan)
    diagnostics = {}
    assert a.execute(api, store, cfg, lab, account(), None, [], diagnostics) == []
    assert reason in diagnostics['entry_pause_reasons']
    assert diagnostics['entry_decisions'] == [] and diagnostics['candidates'] == 0
    scan.assert_not_called()
    assert api.posts == []


def test_report_persists_skips_quotes_and_data_errors(env, monkeypatch, tmp_path):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    api.bid = 90.
    status = dict(status='PAPER_TICK_COMPLETED', mode='tick')
    quotes = {}
    a.execute(api, store, cfg, lab, account(), None, [], status, quotes)
    status['data_errors'] = [dict(symbol='ETH/USD', timeframe='5m', stage='candles', error_type='SafetyError')]
    before = copy.deepcopy(store.state)
    a.report(store.state, status, quotes, tmp_path)
    assert store.state == before
    saved = json.loads((tmp_path/'status.json').read_text())
    assert saved['entry_decisions'][0]['reason'] == 'spread_too_wide'
    with (tmp_path/'entry_decisions.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]['reason'] == 'spread_too_wide'
    assert json.loads(rows[0]['details'])['max_spread_bps'] == cfg['max_spread_bps']
    with (tmp_path/'quotes.csv').open() as stream:
        assert list(csv.DictReader(stream))[0]['bid'] == '90.0'
    text = (tmp_path/'summary.md').read_text()
    assert 'Candidates: 1. Skipped: 1. Broker order results: 0.' in text
    assert 'spread_too_wide' in text and 'Data errors' in text and 'ETH/USD' in text
    assert text == (tmp_path/'journal.md').read_text()


def test_order_result_does_not_claim_fill_and_failure_keeps_intent(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    diagnostics = {}
    api.call = Mock(side_effect=a.SafetyError('fixture transport'))
    with pytest.raises(a.SafetyError, match='fixture transport'):
        a.execute(api, store, cfg, lab, account(), None, [], diagnostics)
    decision = diagnostics['entry_decisions'][0]
    assert decision['outcome'] == 'order_intent'
    assert decision['reason'] == 'entry_checks_passed'
    assert list(store.state['orders'].values())[0]['attempted'] is True
    assert api.posts == []


def test_successful_order_reports_broker_status(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    diagnostics, quotes = {}, {}
    a.execute(api, store, cfg, lab, account(), None, [], diagnostics, quotes)
    decision = diagnostics['entry_decisions'][0]
    assert decision['outcome'] == 'order_result'
    assert decision['details']['broker_status'] == 'filled'
    assert len(api.posts) == 1 and 'BTC/USD' in quotes


@pytest.mark.parametrize('fail', [False, True])
def test_run_preserves_diagnostics_and_quotes_in_observations(env, monkeypatch, tmp_path, fail):
    api, store, cfg, lab = env
    for name in ('ALPACA_CRYPTO_PAPER_ENABLED', 'ALPACA_CRYPTO_DEDICATED_ACCOUNT'):
        monkeypatch.setenv(name, 'true')
    monkeypatch.setenv('ALPACA_EXPECTED_PAPER_ACCOUNT_ID', ACCOUNT)
    monkeypatch.setenv('ALPACA_PAPER_KEY_ID', 'fixture')
    monkeypatch.setenv('ALPACA_PAPER_SECRET_KEY', 'fixture')
    monkeypatch.delenv('ALPACA_CRYPTO_PAUSE_ENTRIES', raising=False)
    for name in ('account', 'snapshot', 'fees', 'assets', 'lookup', 'latest'):
        method = getattr(api, name)
        monkeypatch.setattr(a.API, name, lambda self, *args, _method=method, **kwargs: _method(*args, **kwargs))
    monkeypatch.setattr(a, 'settings', lambda *args: cfg)
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    if fail:
        monkeypatch.setattr(a.API, 'call', lambda *args, **kwargs: (_ for _ in ()).throw(a.SafetyError('fixture transport')))
    else:
        api.bid = 90.
    path, out = tmp_path/'run-state.json', tmp_path/'run-report'
    if fail:
        with pytest.raises(a.SafetyError, match='fixture transport'):
            a.run('tick', path, out)
    else:
        a.run('tick', path, out)
    saved = json.loads((out/'status.json').read_text())
    ledger = json.loads(path.read_text())
    assert saved == ledger['observations'][-1]
    assert saved['candidates'] == 1 and saved['data_errors'] == []
    assert saved['entry_decisions'][0]['outcome'] == ('order_intent' if fail else 'skipped')
    assert saved['status'] == ('FAILED_CLOSED' if fail else 'PAPER_TICK_COMPLETED')
    with (out/'quotes.csv').open() as stream:
        assert len(list(csv.DictReader(stream))) == 1
