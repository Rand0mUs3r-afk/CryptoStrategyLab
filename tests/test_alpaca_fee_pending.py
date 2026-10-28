"""Simulated broker tests: pending fees are not confirmed fees or P&L."""
import copy
from decimal import Decimal
import time
from unittest.mock import Mock
import pytest
import alpaca_crypto as engine
import alpaca_reconciled as repaired

CID = 'csl2-' + 'a' * 32
OID = '00000000-0000-0000-0000-000000000010'
GROSS = '1.962246379'
NET = '1.957340763'
FEE = '-0.004905616'


class Store:
    def __init__(self):
        now = time.time()
        payload = dict(symbol='SOL/USD', side='buy', qty=GROSS, type='market', time_in_force='gtc', client_order_id=CID)
        order = dict(payload=payload, cycle_id=CID, status='filled', attempted=True,
                     filled_qty=GROSS, filled_avg_price=102, created_at=now - 30,
                     filled_at=engine.utc(now - 30), broker_order_id=OID)
        self.state = dict(version=1, paper_only=True, observations=[], execution_initialized=True,
            account_id='00000000-0000-0000-0000-000000000001', activated_at=now - 60,
            orders={CID: order}, fees={}, baseline_fee_ids=[], fee_after=engine.utc(now - 60),
            cycles=[dict(id=CID, symbol='SOL/USD', status='open')])
        self.remote_saves = 0
    def save(self, remote=False):
        self.remote_saves += int(remote)


class Broker:
    def __init__(self, store, qty=NET, pages=None):
        self.store, self.qty = store, qty
        self.pages = list(pages or [[]])
        self.reads, self.writes = 0, []
        order = store.state['orders'][CID]
        self.history = [dict(order['payload'], id=OID, status='filled', filled_qty=GROSS,
                             filled_avg_price='102', filled_at=order['filled_at'], updated_at=order['filled_at'])]
        self.opened = []
        self.available = qty
    def fees(self, after):
        return self.pages.pop(0) if len(self.pages) > 1 else self.pages[0]
    def snapshot(self):
        positions = [dict(symbol='SOLUSD', qty=self.qty, qty_available=self.available)] if Decimal(self.qty) else []
        return positions, self.opened
    def call(self, method, path, **kwargs):
        assert method == 'GET' and path == '/v2/orders'
        assert kwargs['params']['status'] == 'all'
        return self.history


@pytest.fixture(autouse=True)
def policy(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_exits', True)
    monkeypatch.setitem(repaired._POLICY, 'pending_fee_rate_bps', 25)
    monkeypatch.setitem(repaired._POLICY, 'pending_fee_max_age_seconds', 172800)
    def refresh(api, store):
        api.reads += 1
    monkeypatch.setattr(engine, 'reconcile_orders', refresh)


def confirmed_fee():
    return dict(id='sol-fee', symbol='SOLUSD', qty=FEE, activity_type='CFEE')


def reconcile(api, store):
    return repaired.owned_positions(api, store, attempts=1, delay_seconds=0)


def test_exact_reported_sol_case_is_pending_not_invented_fee():
    store = Store()
    api = Broker(store)
    actual, _ = reconcile(api, store)
    assert actual['SOLUSD']['qty'] == NET
    assert store.state['fees'] == {}
    status = store.state['reconciliation']
    assert status['status'] == 'fee_pending'
    assert status['entries_blocked'] and status['exit_checks_allowed']
    assert status['accounting_final'] is False
    assert status['quantities'][0]['unconfirmed_shortfall'] == '0.004905616'


def test_late_activity_clears_pending_without_double_counting():
    store = Store()
    api = Broker(store)
    reconcile(api, store)
    api.pages = [[confirmed_fee(), confirmed_fee()]]
    reconcile(api, store)
    assert store.state['reconciliation']['status'] == 'matched'
    assert not store.state['reconciliation']['entries_blocked']
    assert len(store.state['fees']) == 1


def test_posted_fee_survives_temporary_api_omission():
    store = Store()
    api = Broker(store, pages=[[confirmed_fee()], []])
    reconcile(api, store)
    reconcile(api, store)
    assert store.state['reconciliation']['status'] == 'matched'
    assert store.state['fees']['sol-fee'] == confirmed_fee()


@pytest.mark.parametrize('qty', ['1.95', '1.962', '2', '-1'])
def test_unexplained_difference_or_short_is_blocked(qty):
    store = Store()
    with pytest.raises(engine.SafetyError):
        reconcile(Broker(store, qty=qty), store)


def test_pending_requires_recent_fill():
    store = Store()
    store.state['orders'][CID]['filled_at'] = engine.utc(time.time() - 172900)
    with pytest.raises(engine.SafetyError):
        reconcile(Broker(store), store)


def test_pending_requires_explicit_policy(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_exits', False)
    store = Store()
    with pytest.raises(engine.SafetyError):
        reconcile(Broker(store), store)


def test_foreign_closed_order_is_not_adopted():
    store = Store()
    api = Broker(store)
    api.history.append(dict(api.history[0], client_order_id='foreign'))
    with pytest.raises(engine.SafetyError, match='Foreign order history'):
        reconcile(api, store)


def test_missing_history_blocks_pending():
    store = Store()
    api = Broker(store)
    api.history = []
    with pytest.raises(engine.SafetyError, match='missing from order history'):
        reconcile(api, store)


def test_truncated_history_blocks_pending():
    store = Store()
    api = Broker(store)
    api.history *= 500
    with pytest.raises(engine.SafetyError, match='history incomplete'):
        reconcile(api, store)


def test_foreign_open_order_is_not_adopted():
    store = Store()
    api = Broker(store)
    api.opened = [dict(client_order_id='foreign', symbol='SOLUSD')]
    with pytest.raises(engine.SafetyError, match='Foreign open order'):
        reconcile(api, store)


def test_multiple_active_cycles_block_pending():
    store = Store()
    store.state['cycles'].append(dict(id='other', symbol='SOL/USD', status='open'))
    with pytest.raises(engine.SafetyError):
        reconcile(Broker(store), store)


def test_confirmed_fee_base_asset_label():
    store = Store()
    api = Broker(store, pages=[[dict(confirmed_fee(), symbol='SOL')]])
    reconcile(api, store)
    assert store.state['reconciliation']['status'] == 'matched'


def test_fee_pending_buy_guard_blocks_post(monkeypatch):
    store = Store()
    api = Broker(store)
    original = Mock()
    monkeypatch.setattr(repaired, '_ORIGINAL_SUBMIT', original)
    monkeypatch.setattr(repaired.time, 'sleep', lambda _: None)
    payload = dict(store.state['orders'][CID]['payload'], client_order_id='csl2-' + 'b' * 32)
    with pytest.raises(engine.SafetyError, match='New buy blocked'):
        repaired.submit_intent(api, store, payload, payload['client_order_id'], time.time())
    original.assert_not_called()


def test_guarded_exit_can_sell_only_broker_net_quantity(monkeypatch):
    store = Store()
    api = Broker(store)
    original = Mock(return_value={'status': 'filled'})
    monkeypatch.setattr(repaired, '_ORIGINAL_SUBMIT', original)
    monkeypatch.setattr(repaired.time, 'sleep', lambda _: None)
    payload = dict(store.state['orders'][CID]['payload'], side='sell', qty=NET, client_order_id='csl2-' + 'b' * 32)
    repaired.submit_intent(api, store, payload, CID, time.time())
    original.assert_called_once()
    assert original.call_args.args[2]['qty'] == NET


def test_guarded_exit_rejects_gross_quantity(monkeypatch):
    store = Store()
    api = Broker(store)
    original = Mock()
    monkeypatch.setattr(repaired, '_ORIGINAL_SUBMIT', original)
    monkeypatch.setattr(repaired.time, 'sleep', lambda _: None)
    payload = dict(store.state['orders'][CID]['payload'], side='sell', client_order_id='csl2-' + 'b' * 32)
    with pytest.raises(engine.SafetyError, match='available quantity'):
        repaired.submit_intent(api, store, payload, CID, time.time())
    original.assert_not_called()


def test_pending_shortfall_remains_explicit_after_net_exit():
    store = Store()
    buy = store.state['orders'][CID]
    sell_payload = dict(buy['payload'], side='sell', qty=NET, client_order_id='csl2-' + 'b' * 32)
    store.state['orders'][sell_payload['client_order_id']] = dict(buy, payload=sell_payload, filled_qty=NET)
    api = Broker(store, qty='0')
    api.history.append(dict(api.history[0], **sell_payload, filled_qty=NET))
    reconcile(api, store)
    assert store.state['reconciliation']['status'] == 'fee_pending'
    assert not store.state['fees']


def test_delayed_fee_read_recovers_without_pending_mode(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_exits', False)
    store = Store()
    api = Broker(store, pages=[[], [confirmed_fee()]])
    repaired.owned_positions(api, store, attempts=3, delay_seconds=0)
    assert store.state['reconciliation']['status'] == 'matched'
    assert store.state['reconciliation']['attempts'] == 2


def fake_execution(api, store, cfg, lab, account, market, errors, diagnostics, quotes):
    diagnostics.update(entry_pause_reasons=[], entry_decisions=[])
    api.exit_checks += 1
    return engine.candidates(cfg, lab, {}, market, errors)


def test_scan_timer_keeps_exit_callback_running(monkeypatch):
    store = Store()
    store.state['reconciliation'] = dict(entries_blocked=False)
    api = Mock(exit_checks=0)
    scanner = Mock(return_value=[])
    monkeypatch.setattr(engine, 'candidates', scanner)
    monkeypatch.setattr(repaired, '_ORIGINAL_EXECUTE', fake_execution)
    cfg = dict(entry_scan_interval_seconds=1800)
    for _ in range(2):
        diagnostic = {}
        repaired.execute(api, store, cfg, {}, {}, None, [], diagnostic)
    assert api.exit_checks == 2
    assert scanner.call_count == 1
    assert diagnostic['entry_scan_status'] == 'not_due'
    store.state['last_entry_scan_at'] -= 1801
    repaired.execute(api, store, cfg, {}, {}, None, [], {})
    assert scanner.call_count == 2


def test_pending_blocks_scanner_but_not_exit_callback(monkeypatch):
    store = Store()
    store.state['reconciliation'] = dict(entries_blocked=True)
    api = Mock(exit_checks=0)
    scanner = Mock()
    monkeypatch.setattr(engine, 'candidates', scanner)
    monkeypatch.setattr(repaired, '_ORIGINAL_EXECUTE', fake_execution)
    diagnostic = {}
    repaired.execute(api, store, dict(entry_scan_interval_seconds=1800), {}, {}, None, [], diagnostic)
    assert api.exit_checks == 1
    scanner.assert_not_called()
    assert diagnostic['entry_scan_status'] == 'fee_pending'
