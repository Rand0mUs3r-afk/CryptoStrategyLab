"""Fail-closed reconciliation repair for the existing paper executor."""
from decimal import Decimal
import json
from pathlib import Path
import time


def install(a):
    if getattr(a, '_reconciliation_repair_installed', False):
        return
    a._reconciliation_repair_installed = True
    original_execute, original_report = a.execute, a.report

    def update_fees(api, store):
        s = store.state
        ignored = set(s['baseline_fee_ids'])
        fees = {key: row for key, row in s.get('fees', {}).items() if key not in ignored}
        for row in api.fees(s['fee_after']):
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
                raise a.SafetyError('Invalid fee activity; refusing reconciliation')
            if row['id'] not in ignored:
                fees[row['id']] = row
        s['fees'] = fees

    def owned_positions(api, store, attempts=3, delay_seconds=2):
        if type(attempts) is not int or not 1 <= attempts <= 5:
            raise a.SafetyError('Invalid reconciliation attempt count')
        if not 0 <= a.number(delay_seconds) <= 10:
            raise a.SafetyError('Invalid reconciliation delay')
        s = store.state
        s['reconciliation'] = dict(status='checking', quantities=[])
        for attempt in range(1, attempts + 1):
            try:
                a.reconcile_orders(api, store)
                update_fees(api, store)
                positions, opened = api.snapshot()
                if any(row.get('client_order_id') not in s['orders'] for row in opened):
                    raise a.SafetyError('Foreign open order in dedicated account; not adopted')
                expected, fee_qty, actual = {}, {}, {}
                for order in s['orders'].values():
                    p = order['payload']
                    key = a.canonical(p['symbol'])
                    expected[key] = expected.get(key, Decimal(0)) + a.dec(order.get('filled_qty', 0)) * (1 if p['side'] == 'buy' else -1)
                for fee in s['fees'].values():
                    qty = a.dec(fee.get('qty') or '0')
                    if not qty:
                        continue
                    key = a.canonical(fee.get('symbol', ''))
                    if key not in expected:
                        matches = [pair for pair in expected if pair.endswith('USD') and pair[:-3] == key]
                        if len(matches) != 1:
                            raise a.SafetyError('Unattributable crypto fee activity')
                        key = matches[0]
                    fee_qty[key] = fee_qty.get(key, Decimal(0)) + qty
                for p in positions:
                    key = a.canonical(p['symbol'])
                    if key in actual or a.dec(p['qty']) < 0:
                        raise a.SafetyError('Duplicate or short broker position')
                    actual[key] = p
                rows, bad = [], []
                for key in sorted(set(expected) | set(actual)):
                    filled = expected.get(key, Decimal(0))
                    fees = fee_qty.get(key, Decimal(0))
                    wanted = filled + fees
                    broker = a.dec(actual[key]['qty']) if key in actual else Decimal(0)
                    delta = broker - wanted
                    row = dict(symbol=key, filled_quantity=str(filled), fee_quantity=str(fees), expected_quantity=str(wanted), broker_quantity=str(broker), difference_quantity=str(delta))
                    rows.append(row)
                    if abs(delta) > Decimal('0.00000001'):
                        bad.append(row)
                s['reconciliation'] = dict(status='mismatch' if bad else 'matched', observed_at_utc=a.utc(time.time()), attempts=attempt, max_attempts=attempts, quantities=rows)
                store.save()
                if not bad:
                    return actual, opened
                if attempt == attempts:
                    details = '; '.join(f"{r['symbol']}: expected={r['expected_quantity']}, broker={r['broker_quantity']}, difference={r['difference_quantity']}, recorded_fees={r['fee_quantity']}" for r in bad)
                    raise a.SafetyError('Position/fee reconciliation mismatch after read-only retries: ' + details + '; no fees inferred; entries and automated exits blocked')
            except Exception as exc:
                s['reconciliation'].update(observed_at_utc=a.utc(time.time()), attempts=attempt, max_attempts=attempts)
                if s['reconciliation']['status'] != 'mismatch':
                    s['reconciliation']['status'] = 'failed_closed'
                store.save()
                raise
            if delay_seconds:
                time.sleep(delay_seconds)

    def execute(api, store, cfg, lab, account, market, errors, diagnostics=None, quotes=None):
        diagnostics = diagnostics if diagnostics is not None else {}
        interval = cfg.get('entry_scan_interval_seconds', 1800)
        if type(interval) is not int or not 60 <= interval <= 86400:
            raise a.SafetyError('Invalid entry scan interval')
        scanner = a.candidates
        scan_status = {'entry_scan_interval_seconds': interval, 'entry_scan_status': 'not_reached'}
        store.state.pop('reconciliation', None)
        def scheduled_scan(*args):
            now = time.time()
            last = store.state.get('last_entry_scan_at')
            if last is not None:
                last = a.number(last)
                if last > now:
                    raise a.SafetyError('Entry scan timestamp is in the future')
                if now - last < interval:
                    scan_status.update(entry_scan_status='not_due', next_entry_scan_at_utc=a.utc(last + interval))
                    return []
            store.state['last_entry_scan_at'] = now
            scan_status.update(entry_scan_status='started', next_entry_scan_at_utc=a.utc(now + interval))
            store.save(remote=True)
            result = scanner(*args)
            scan_status['entry_scan_status'] = 'completed_with_data_errors' if errors else 'completed'
            return result
        a.candidates = scheduled_scan
        try:
            return original_execute(api, store, cfg, lab, account, market, errors, diagnostics=diagnostics, quotes=quotes)
        finally:
            a.candidates = scanner
            diagnostics.update(scan_status)
            if 'reconciliation' in store.state:
                diagnostics['reconciliation'] = store.state['reconciliation'].copy()

    def report(state, status, quotes, out):
        original_report(state, status, quotes, out)
        diagnostic = status.get('reconciliation', {})
        a.write_csv(Path(out) / 'reconciliation.csv', diagnostic.get('quantities', []), ['symbol', 'filled_quantity', 'fee_quantity', 'expected_quantity', 'broker_quantity', 'difference_quantity'])
        lines = ['\n## Reconciliation and scan schedule\n', json.dumps(diagnostic, indent=2), '\nEntry scan: ' + status.get('entry_scan_status', 'not_reached'), 'Next eligible: ' + status.get('next_entry_scan_at_utc', 'not recorded'), 'Unresolved reconciliation blocks software exits as well as entries; no fee is inferred.\n']
        for name in ('summary.md', 'journal.md'):
            with (Path(out) / name).open('a') as handle:
                handle.write('\n'.join(lines))

    a.update_fees, a.owned_positions = update_fees, owned_positions
    a.execute, a.report = execute, report
