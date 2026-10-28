"""Offline regressions for the workflow reconciliation compatibility layer."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from alpaca_reconciliation import install


class SafetyError(RuntimeError):
    pass


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.a = SimpleNamespace(SafetyError=SafetyError, number=float, dec=lambda v: Decimal(str(v)), canonical=lambda s: s.replace('/', '').replace('-', ''), utc=lambda t: str(t), report=Mock(), write_csv=Mock())
        self.a.reconcile_orders = Mock()
        self.a.candidates = Mock(return_value=[])
        def execute(api, store, cfg, lab, account, market, errors, diagnostics=None, quotes=None):
            self.a.owned_positions(api, store, delay_seconds=0)
            api.exits_checked += 1
            return self.a.candidates(cfg, lab, {}, market, errors)
        self.a.execute = execute
        install(self.a)
        order = {'payload': {'symbol': 'SOL/USD', 'side': 'buy'}, 'filled_qty': '2'}
        self.store = SimpleNamespace(state={'orders': {'own': order}, 'baseline_fee_ids': [], 'fee_after': '2026-10-28', 'fees': {}}, save=Mock())
        self.api = SimpleNamespace(snapshot=Mock(return_value=([{'symbol': 'SOLUSD', 'qty': '2'}], [])), fees=Mock(return_value=[]), exits_checked=0)

    def fee(self, symbol='SOLUSD'):
        return {'id': 'fee1', 'symbol': symbol, 'qty': '-0.005'}

    def test_matching_inventory(self):
        actual, opened = self.a.owned_positions(self.api, self.store, delay_seconds=0)
        self.assertEqual(actual['SOLUSD']['qty'], '2')
        self.assertEqual(self.store.state['reconciliation']['status'], 'matched')

    def test_delayed_fee_resolves_on_second_read(self):
        self.api.snapshot.return_value = ([{'symbol': 'SOLUSD', 'qty': '1.995'}], [])
        self.api.fees.side_effect = [[], [self.fee()]]
        self.a.owned_positions(self.api, self.store, delay_seconds=0)
        self.assertEqual(self.store.state['reconciliation']['attempts'], 2)
        self.assertEqual(self.a.reconcile_orders.call_count, 2)

    def test_unresolved_mismatch_records_exact_delta_and_stops(self):
        self.api.snapshot.return_value = ([{'symbol': 'SOLUSD', 'qty': '1.995'}], [])
        with self.assertRaisesRegex(SafetyError, 'expected=2, broker=1.995, difference=-0.005'):
            self.a.owned_positions(self.api, self.store, delay_seconds=0)
        self.assertEqual(self.api.snapshot.call_count, 3)
        self.assertEqual(self.store.state['fees'], {})

    def test_observed_fee_is_not_dropped(self):
        self.api.fees.side_effect = [[self.fee()], []]
        self.a.update_fees(self.api, self.store)
        self.a.update_fees(self.api, self.store)
        self.assertEqual(self.store.state['fees']['fee1'], self.fee())

    def test_base_symbol_fee_is_unambiguous(self):
        self.api.fees.return_value = [self.fee('SOL')]
        self.api.snapshot.return_value = ([{'symbol': 'SOLUSD', 'qty': '1.995'}], [])
        self.a.owned_positions(self.api, self.store, delay_seconds=0)
        self.assertEqual(self.store.state['reconciliation']['status'], 'matched')

    def test_foreign_order_is_not_retried_or_adopted(self):
        self.api.snapshot.return_value = ([], [{'client_order_id': 'foreign'}])
        with self.assertRaisesRegex(SafetyError, 'Foreign'):
            self.a.owned_positions(self.api, self.store, delay_seconds=0)
        self.assertEqual(self.api.snapshot.call_count, 1)

    def test_unattributable_fee_is_blocked(self):
        self.api.fees.return_value = [self.fee('ETHUSD')]
        with self.assertRaisesRegex(SafetyError, 'Unattributable'):
            self.a.owned_positions(self.api, self.store, delay_seconds=0)

    def test_thirty_minute_timer_does_not_skip_exit_handling(self):
        first, second = {}, {}
        args = (self.api, self.store, {}, {}, {}, None, [])
        self.a.execute(*args, diagnostics=first)
        self.a.execute(*args, diagnostics=second)
        self.assertEqual(self.a.candidates.call_count, 1)
        self.assertEqual(self.api.exits_checked, 2)
        self.assertEqual(second['entry_scan_status'], 'not_due')
        self.store.state['last_entry_scan_at'] -= 1801
        self.a.execute(*args, diagnostics={})
        self.assertEqual(self.a.candidates.call_count, 2)

    def test_failed_checkpoint_prevents_scanning(self):
        def save(remote=False):
            if remote:
                raise SafetyError('checkpoint failed')
        self.store.save = save
        with self.assertRaisesRegex(SafetyError, 'checkpoint failed'):
            self.a.execute(self.api, self.store, {}, {}, {}, None, [], diagnostics={})
        self.assertEqual(self.a.candidates.call_count, 0)

    def test_future_scan_timestamp_is_blocked(self):
        self.store.state['last_entry_scan_at'] = 999999999999
        with self.assertRaisesRegex(SafetyError, 'future'):
            self.a.execute(self.api, self.store, {}, {}, {}, None, [], diagnostics={})


if __name__ == '__main__':
    unittest.main()
