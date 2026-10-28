"""Synthetic broker fixtures test reconciliation mechanics, not performance."""
from decimal import Decimal
import pytest
import alpaca_crypto as engine
import alpaca_reconciled as repaired


class Store:
    def __init__(self):
        self.state = dict(orders={'buy': dict(payload=dict(symbol='SOL/USD', side='buy'), filled_qty='2')}, fees={}, baseline_fee_ids=[], fee_after='2026-10-28')
    def save(self):
        pass


class Broker:
    def __init__(self, pages, qty='2', opened=None):
        self.pages = iter(pages)
        self.qty = qty
        self.opened = opened or []
        self.reads = 0
    def fees(self, after):
        return next(self.pages)
    def snapshot(self):
        return [dict(symbol='SOLUSD', qty=self.qty)], self.opened


@pytest.fixture(autouse=True)
def read_only_refresh(monkeypatch):
    def refresh(api, store):
        api.reads += 1
    monkeypatch.setattr(engine, 'reconcile_orders', refresh)


def fee(**changes):
    return dict(dict(id='f1', symbol='SOLUSD', qty='-0.005'), **changes)


def test_delayed_fee_recovers():
    store = Store()
    api = Broker([[], [fee()]], '1.995')
    repaired.owned_positions(api, store, delay_seconds=0)
    assert store.state['reconciliation']['attempts'] == 2
    assert store.state['reconciliation']['status'] == 'matched'


def test_persistent_difference_is_not_adopted():
    store = Store()
    api = Broker([[], []], '1.995')
    with pytest.raises(repaired.PositionMismatch, match='expected=2, broker=1.995'):
        repaired.owned_positions(api, store, attempts=2, delay_seconds=0)
    assert store.state['fees'] == {}
    assert store.state['reconciliation']['retry_exhausted'] is True
    assert Decimal(store.state['reconciliation']['quantities'][0]['difference_quantity']) == Decimal('-0.005')


def test_observed_fee_is_retained():
    store = Store()
    api = Broker([[fee()], []], '1.995')
    repaired.update_fees(api, store)
    repaired.update_fees(api, store)
    assert store.state['fees'] == {'f1': fee()}


def test_base_asset_fee_maps_only_to_existing_pair():
    store = Store()
    repaired.owned_positions(Broker([[fee(symbol='SOL')]], '1.995'), store, delay_seconds=0)
    assert store.state['reconciliation']['status'] == 'matched'


def test_foreign_open_order_blocks_without_retry():
    api = Broker([[]], opened=[dict(client_order_id='foreign')])
    with pytest.raises(engine.SafetyError, match='Foreign'):
        repaired.owned_positions(api, Store(), delay_seconds=0)
    assert api.reads == 1


def test_foreign_fee_is_not_adopted():
    with pytest.raises(engine.SafetyError, match='Unattributable'):
        repaired.owned_positions(Broker([[fee(symbol='ETH')]], '1.995'), Store(), delay_seconds=0)


def test_baseline_fee_excluded():
    store = Store()
    store.state['baseline_fee_ids'] = ['f1']
    repaired.update_fees(Broker([[fee()]]), store)
    assert store.state['fees'] == {}


def test_duplicate_fee_id_counted_once():
    store = Store()
    repaired.owned_positions(Broker([[fee(), fee()]], '1.995'), store, delay_seconds=0)
    assert len(store.state['fees']) == 1
