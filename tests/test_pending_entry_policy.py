"""Explicit paper-entry exception never erases broker quantities or records."""
import time
from unittest.mock import Mock
import pytest
import alpaca_crypto as engine
import alpaca_reconciled as repaired
from test_alpaca_fee_pending import Store, Broker, CID, policy, reconcile, confirmed_fee


def test_explicit_policy_unblocks_validated_pending_entries(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_entries', True)
    store = Store()
    reconcile(Broker(store), store)
    diagnostic = store.state['reconciliation']
    assert diagnostic['status'] == 'fee_pending'
    assert diagnostic['entries_blocked'] is False
    assert diagnostic['accounting_final'] is False
    assert store.state['fees'] == {}


def test_buy_passes_pending_guard_only_when_explicitly_enabled(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_entries', True)
    monkeypatch.setattr(repaired.time, 'sleep', lambda _: None)
    original = Mock(return_value={'status': 'new'})
    monkeypatch.setattr(repaired, '_ORIGINAL_SUBMIT', original)
    store = Store()
    payload = dict(store.state['orders'][CID]['payload'], client_order_id='csl2-' + 'b' * 32)
    repaired.submit_intent(Broker(store), store, payload, payload['client_order_id'], time.time())
    original.assert_called_once()


def test_unknown_difference_still_blocks_with_entry_exception(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_entries', True)
    store = Store()
    with pytest.raises(engine.SafetyError):
        reconcile(Broker(store, qty='1.9'), store)
    assert store.state['reconciliation']['entries_blocked'] is True


def test_real_fee_record_is_preserved_with_entry_exception(monkeypatch):
    monkeypatch.setitem(repaired._POLICY, 'allow_fee_pending_entries', True)
    store = Store()
    reconcile(Broker(store, pages=[[confirmed_fee()]]), store)
    assert store.state['fees']['sol-fee'] == confirmed_fee()
    assert store.state['reconciliation']['status'] == 'matched'
