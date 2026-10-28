"""Paper execution adapter: explicit pending fees, guarded exits and timed entries."""
import argparse
import copy
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import time
import alpaca_crypto as engine

TOLERANCE = Decimal('0.00000001')
_POLICY = dict(allow_fee_pending_exits=False, pending_fee_rate_bps=25,
               pending_fee_max_age_seconds=172800, entry_scan_interval_seconds=1800)
_ORIGINAL_SETTINGS = engine.settings
_ORIGINAL_EXECUTE = engine.execute
_ORIGINAL_SUBMIT = engine.submit_intent
_ORIGINAL_REPORT = engine.report
_ACTIVE_STATE_PATH = None


class PositionMismatch(engine.SafetyError):
    def __init__(self, message, actual, opened):
        super().__init__(message)
        self.actual, self.opened = actual, opened


def settings(path='alpaca_config.json'):
    cfg = _ORIGINAL_SETTINGS(path)
    for key, default in _POLICY.items():
        cfg.setdefault(key, default)
    if not isinstance(cfg['allow_fee_pending_exits'], bool):
        raise engine.SafetyError('allow_fee_pending_exits must be boolean')
    for key, low, high in [('entry_scan_interval_seconds', 60, 86400),
                           ('pending_fee_max_age_seconds', 60, 172800)]:
        value = cfg[key]
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise engine.SafetyError('Invalid ' + key)
    rate = engine.number(cfg['pending_fee_rate_bps'])
    if not 0 < rate <= 25:
        raise engine.SafetyError('Pending fee rate must be positive and at most 25 bps')
    _POLICY.update({key: cfg[key] for key in _POLICY})
    return cfg


def update_fees(api, store):
    state = store.state
    ignored = set(state['baseline_fee_ids'])
    rows = api.fees(state['fee_after'])
    if not isinstance(rows, list):
        raise engine.SafetyError('Invalid fee response')
    fees = {key: copy.deepcopy(row) for key, row in state.get('fees', {}).items() if key not in ignored}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            raise engine.SafetyError('Invalid broker fee activity ID')
        if row['id'] not in ignored:
            fees[row['id']] = copy.deepcopy(row)
    state['fees'] = fees


def position_snapshot(api, store):
    state = store.state
    positions, opened = api.snapshot()
    if any(order.get('client_order_id') not in state['orders'] for order in opened):
        raise engine.SafetyError('Foreign open order in dedicated account; not adopted')
    fills, fees, actual = {}, {}, {}
    for order in state['orders'].values():
        payload = order['payload']
        key = engine.canonical(payload['symbol'])
        qty = engine.dec(order.get('filled_qty', '0'))
        if payload['side'] not in ('buy', 'sell') or qty < 0:
            raise engine.SafetyError('Invalid ledger order quantity or side')
        fills[key] = fills.get(key, Decimal(0)) + qty * (1 if payload['side'] == 'buy' else -1)
    for fee in state.get('fees', {}).values():
        qty = engine.dec(fee.get('qty') or '0')
        if not qty:
            continue
        key = engine.canonical(fee.get('symbol', ''))
        if key not in fills:
            matches = [pair for pair in fills if pair.endswith('USD') and pair[:-3] == key]
            if len(matches) != 1:
                raise engine.SafetyError('Unattributable crypto fee activity')
            key = matches[0]
        fees[key] = fees.get(key, Decimal(0)) + qty
    for position in positions:
        key = engine.canonical(position['symbol'])
        if key in actual or engine.dec(position['qty']) < 0:
            raise engine.SafetyError('Duplicate or short broker position')
        actual[key] = position
    quantities, mismatches = [], []
    for key in sorted(set(fills) | set(actual)):
        filled, fee_qty = fills.get(key, Decimal(0)), fees.get(key, Decimal(0))
        expected = filled + fee_qty
        broker = engine.dec(actual[key]['qty']) if key in actual else Decimal(0)
        difference = broker - expected
        row = dict(symbol=key, filled_quantity=str(filled), fee_quantity=str(fee_qty),
                   expected_quantity=str(expected), broker_quantity=str(broker),
                   difference_quantity=str(difference), tolerance_quantity=str(TOLERANCE),
                   unconfirmed_shortfall='0')
        quantities.append(row)
        if abs(difference) > TOLERANCE:
            mismatches.append(row)
    state['reconciliation'] = dict(status='mismatch' if mismatches else 'matched',
        observed_at_utc=engine.utc(time.time()), quantities=quantities,
        entries_blocked=bool(mismatches), exit_checks_allowed=not mismatches,
        accounting_final=not mismatches)
    if mismatches:
        text = '; '.join(f"{r['symbol']}: expected={r['expected_quantity']}, broker={r['broker_quantity']}, difference={r['difference_quantity']}, recorded_fee_quantity={r['fee_quantity']}" for r in mismatches)
        raise PositionMismatch('Position/fee reconciliation mismatch for ' + text, actual, opened)
    return actual, opened


def allow_pending(api, store, mismatch):
    if not _POLICY['allow_fee_pending_exits']:
        return False
    state, now = store.state, time.time()
    rate = engine.dec(_POLICY['pending_fee_rate_bps']) / Decimal(10000)
    proposed = []
    for row in state['reconciliation']['quantities']:
        difference = engine.dec(row['difference_quantity'])
        if abs(difference) <= TOLERANCE:
            continue
        if difference >= 0 or engine.dec(row['fee_quantity']) > 0:
            return False
        key = row['symbol']
        buys = [o for o in state['orders'].values() if o['payload']['side'] == 'buy'
                and engine.canonical(o['payload']['symbol']) == key
                and engine.dec(o.get('filled_qty', '0')) > 0]
        if not buys or any(o.get('status') != 'filled' or not o.get('filled_at') for o in buys):
            return False
        if any(o.get('status') not in engine.TERMINAL and engine.canonical(o['payload']['symbol']) == key for o in state['orders'].values()):
            return False
        active = [c for c in state.get('cycles', []) if engine.canonical(c['symbol']) == key and c['status'] != 'closed']
        if engine.dec(row['broker_quantity']) > 0 and len(active) != 1:
            return False
        cycles = {c['id']: c for c in state.get('cycles', [])}
        if any(o['cycle_id'] not in cycles or engine.canonical(cycles[o['cycle_id']]['symbol']) != key for o in buys):
            return False
        def fee_bound(order):
            return (engine.dec(order['filled_qty']) * rate).quantize(Decimal('0.000000001'), rounding=ROUND_HALF_UP)
        gross_bound = sum((fee_bound(o) for o in buys), Decimal(0))
        recent_bound = sum((fee_bound(o) for o in buys if 0 <= now - engine.stamp(o['filled_at']) <= _POLICY['pending_fee_max_age_seconds']), Decimal(0))
        pending = gross_bound + engine.dec(row['fee_quantity'])
        if not (0 < pending <= recent_bound + TOLERANCE and abs(-difference - pending) <= TOLERANCE):
            return False
        proposed.append((row, str(-difference)))
    if not proposed or not state.get('activated_at'):
        return False
    # A matching percentage is not ownership proof. Reject unknown closed orders too.
    history = api.call('GET', '/v2/orders', params=dict(status='all', after=engine.utc(state['activated_at']), direction='asc', limit=500, nested='false'))
    if not isinstance(history, list) or len(history) >= 500:
        raise engine.SafetyError('Order ownership history incomplete; pending-fee exits blocked')
    observed = set()
    for raw in history:
        cid = raw.get('client_order_id')
        local = state['orders'].get(cid)
        if local is None:
            raise engine.SafetyError('Foreign order history; pending-fee exits blocked')
        checked = copy.deepcopy(local)
        engine.apply_order(checked, raw)
        observed.add(cid)
    relevant = {cid for cid, o in state['orders'].items() if engine.dec(o.get('filled_qty', '0')) > 0}
    if not relevant <= observed:
        raise engine.SafetyError('Owned fill missing from order history; pending-fee exits blocked')
    for row, shortfall in proposed:
        row['unconfirmed_shortfall'] = shortfall
    state['reconciliation'].update(status='fee_pending', entries_blocked=True,
        exit_checks_allowed=True, accounting_final=False,
        warning='Fee-sized shortfall is unconfirmed, not a posted fee. Only validated exits allowed.')
    return True


def owned_positions(api, store, attempts=3, delay_seconds=2):
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 5:
        raise engine.SafetyError('Invalid reconciliation attempt count')
    delay = engine.number(delay_seconds)
    if not 0 <= delay <= 10:
        raise engine.SafetyError('Invalid reconciliation retry delay')
    store.state['reconciliation'] = dict(status='checking', quantities=[], entries_blocked=True, exit_checks_allowed=False, accounting_final=False)
    for attempt in range(1, attempts + 1):
        try:
            engine.reconcile_orders(api, store)
            update_fees(api, store)
            actual, opened = position_snapshot(api, store)
        except PositionMismatch as exc:
            store.state['reconciliation'].update(attempts=attempt, retry_exhausted=attempt == attempts)
            if attempt == attempts:
                try:
                    permitted = allow_pending(api, store, exc)
                except Exception:
                    store.save()
                    raise
                store.save()
                if permitted:
                    return exc.actual, exc.opened
                raise PositionMismatch(str(exc) + '; unresolved after read-only retries; entries and exits blocked', exc.actual, exc.opened) from None
            store.save()
            time.sleep(delay)
        except Exception:
            store.state['reconciliation'].update(status='failed_closed', attempts=attempt,
                entries_blocked=True, exit_checks_allowed=False, accounting_final=False)
            store.save()
            raise
        else:
            store.state['reconciliation'].update(attempts=attempt, retry_exhausted=False)
            store.save()
            return actual, opened


def submit_intent(api, store, payload, cycle_id, now):
    engine.API.validate_order(payload)
    existing = store.state['orders'].get(payload['client_order_id'])
    if existing and (existing.get('attempted') or existing.get('status') in engine.TERMINAL):
        return _ORIGINAL_SUBMIT(api, store, payload, cycle_id, now)
    actual, opened = owned_positions(api, store)
    if payload['side'] == 'buy':
        if store.state['reconciliation']['entries_blocked']:
            raise engine.SafetyError('New buy blocked while fee reconciliation is pending')
    else:
        cycles = [c for c in store.state['cycles'] if c['id'] == cycle_id and c['symbol'] == payload['symbol'] and c['status'] != 'closed']
        position = actual.get(engine.canonical(payload['symbol']))
        if len(cycles) != 1 or position is None:
            raise engine.SafetyError('Exit lacks a single owned active cycle and broker holding')
        if any(engine.canonical(o['symbol']) == engine.canonical(payload['symbol']) for o in opened):
            raise engine.SafetyError('Exit blocked by existing open order for symbol')
        available = min(engine.dec(position['qty']), engine.dec(position.get('qty_available', position['qty'])))
        if engine.dec(payload['qty']) > available:
            raise engine.SafetyError('Exit exceeds broker available quantity')
    return _ORIGINAL_SUBMIT(api, store, payload, cycle_id, now)


def execute(api, store, cfg, lab, account, market, errors, diagnostics=None, quotes=None):
    diagnostics = diagnostics if diagnostics is not None else {}
    scanner = engine.candidates
    interval = cfg.get('entry_scan_interval_seconds', 1800)
    def gated_scanner(*args):
        diagnostic = store.state.get('reconciliation', {})
        diagnostics.update(entry_scan_interval_seconds=interval)
        if diagnostic.get('entries_blocked', True):
            diagnostics['entry_scan_status'] = 'fee_pending'
            diagnostics['entry_pause_reasons'].append('fee_pending')
            return []
        now, last = time.time(), store.state.get('last_entry_scan_at')
        if last is not None:
            elapsed = now - engine.number(last)
            if elapsed < 0:
                raise engine.SafetyError('Entry scan timestamp is in the future')
            if elapsed < interval:
                diagnostics.update(entry_scan_status='not_due', next_entry_scan_at_utc=engine.utc(last + interval))
                diagnostics['entry_pause_reasons'].append('entry_scan_interval_not_elapsed')
                return []
        store.state['last_entry_scan_at'] = now
        store.save(remote=True)
        diagnostics.update(entry_scan_status='started', next_entry_scan_at_utc=engine.utc(now + interval))
        ideas = scanner(*args)
        diagnostics['entry_scan_status'] = 'completed_with_data_errors' if errors else 'completed'
        return ideas
    engine.candidates = gated_scanner
    try:
        return _ORIGINAL_EXECUTE(api, store, cfg, lab, account, market, errors, diagnostics, quotes)
    finally:
        engine.candidates = scanner


def report(state, status, quotes, output):
    diagnostic = copy.deepcopy(state.get('reconciliation', {}))
    if status.get('mode') == 'tick' and diagnostic:
        status['reconciliation'] = diagnostic
        if state.get('observations'):
            state['observations'][-1]['reconciliation'] = diagnostic
        if _ACTIVE_STATE_PATH is not None:
            from cryptolab import atomic_json
            atomic_json(_ACTIVE_STATE_PATH, state)
    _ORIGINAL_REPORT(state, status, quotes, output)
    if status.get('mode') != 'tick' or not diagnostic:
        return
    directory = Path(output)
    fields = ['symbol', 'filled_quantity', 'fee_quantity', 'expected_quantity', 'broker_quantity', 'difference_quantity', 'tolerance_quantity', 'unconfirmed_shortfall']
    engine.write_csv(directory / 'reconciliation.csv', diagnostic.get('quantities', []), fields)
    (directory / 'reconciliation.json').write_text(json.dumps(diagnostic, indent=2) + '\n')
    lines = ['\n## Reconciliation', '', 'Status: ' + diagnostic.get('status', 'unknown'),
             'New entries blocked: ' + str(diagnostic.get('entries_blocked', True)),
             'Exit checks allowed: ' + str(diagnostic.get('exit_checks_allowed', False)),
             'Accounting final: ' + str(diagnostic.get('accounting_final', False)), '']
    lines += engine.table(['Coin', 'Expected', 'Broker', 'Difference', 'Unconfirmed'], [
        [row[key] for key in ('symbol', 'expected_quantity', 'broker_quantity', 'difference_quantity', 'unconfirmed_shortfall')]
        for row in diagnostic.get('quantities', [])])
    if diagnostic.get('status') == 'fee_pending':
        lines += ['', 'PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented. New buys blocked; guarded software exits remain active. Trade accounting is provisional until broker fees arrive.']
    elif diagnostic.get('status') != 'matched':
        lines += ['', 'UNRESOLVED: entries and automated exits blocked. Review the paper holding.']
    lines += ['', 'Entry scan status: ' + status.get('entry_scan_status', 'not_reached'),
              'Next entry scan eligible: ' + status.get('next_entry_scan_at_utc', 'not_scheduled'),
              'Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.',
              'Full diagnostics: reconciliation.csv and reconciliation.json.', '']
    for name in ('summary.md', 'journal.md'):
        with (directory / name).open('a') as handle:
            handle.write('\n'.join(lines))


def main():
    global _ACTIVE_STATE_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('check', 'plan', 'tick'), default='check')
    parser.add_argument('--state', default='state/alpaca_state.json')
    parser.add_argument('--output', default='output/alpaca')
    parser.add_argument('--execution-config', default='alpaca_config.json')
    parser.add_argument('--checkpoint-script')
    args = parser.parse_args()
    _ACTIVE_STATE_PATH = args.state
    original_load = engine.load
    def load_for_run(path):
        state = original_load(path)
        if args.mode == 'tick':
            state['reconciliation'] = dict(status='not_started', quantities=[], entries_blocked=True, exit_checks_allowed=False, accounting_final=False)
        return state
    engine.load = load_for_run
    engine.settings = settings
    engine.owned_positions = owned_positions
    engine.update_fees = update_fees
    engine.submit_intent = submit_intent
    engine.execute = execute
    engine.report = report
    engine.run(args.mode, args.state, args.output, args.execution_config, args.checkpoint_script)


if __name__ == '__main__':
    main()
