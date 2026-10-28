"""Paper execution entrypoint with read-only reconciliation retries.

The existing execution engine retains account verification, order idempotency,
checkpoints, signals, risk limits and exit logic. Only reconciliation/reporting
are supplied here until the engine is refactored into separate modules.
"""
import argparse
import copy
from decimal import Decimal
import json
from pathlib import Path
import time
import alpaca_crypto as engine


class PositionMismatch(engine.SafetyError):
    pass


def update_fees(api, store):
    state = store.state
    ignored = set(state['baseline_fee_ids'])
    rows = api.fees(state['fee_after'])
    if not isinstance(rows, list):
        raise engine.SafetyError('Invalid fee response')
    fees = {key: value for key, value in state.get('fees', {}).items() if key not in ignored}
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
        raise engine.SafetyError('Foreign open order in dedicated account; not canceled or adopted')
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
        qty = engine.dec(position['qty'])
        if key in actual or qty < 0:
            raise engine.SafetyError('Duplicate or short broker position')
        actual[key] = position
    quantities, mismatches = [], []
    tolerance = Decimal('0.00000001')
    for key in sorted(set(fills) | set(actual)):
        filled = fills.get(key, Decimal(0))
        fee_qty = fees.get(key, Decimal(0))
        expected = filled + fee_qty
        broker = engine.dec(actual[key]['qty']) if key in actual else Decimal(0)
        difference = broker - expected
        row = dict(symbol=key, filled_quantity=str(filled), fee_quantity=str(fee_qty),
                   expected_quantity=str(expected), broker_quantity=str(broker),
                   difference_quantity=str(difference), tolerance_quantity=str(tolerance))
        quantities.append(row)
        if abs(difference) > tolerance:
            mismatches.append(row)
    state['reconciliation'] = dict(status='mismatch' if mismatches else 'matched',
        observed_at_utc=engine.utc(time.time()), broker_fee_records=len(state.get('fees', {})),
        quantities=quantities)
    if mismatches:
        details = '; '.join(f"{r['symbol']}: expected={r['expected_quantity']}, broker={r['broker_quantity']}, difference={r['difference_quantity']}, recorded_fee_quantity={r['fee_quantity']}" for r in mismatches)
        raise PositionMismatch('Position/fee reconciliation mismatch for ' + details)
    return actual, opened


def owned_positions(api, store, attempts=3, delay_seconds=2):
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 5:
        raise engine.SafetyError('Invalid reconciliation attempt count')
    delay = engine.number(delay_seconds)
    if not 0 <= delay <= 10:
        raise engine.SafetyError('Invalid reconciliation retry delay')
    store.state['reconciliation'] = dict(status='checking', quantities=[])
    for attempt in range(1, attempts + 1):
        try:
            engine.reconcile_orders(api, store)
            update_fees(api, store)
            actual, opened = position_snapshot(api, store)
        except PositionMismatch as exc:
            store.state['reconciliation'].update(attempts=attempt, retry_exhausted=attempt == attempts)
            store.save()
            if attempt == attempts:
                raise PositionMismatch(str(exc) + f'; unresolved after {attempts} read-only attempts. No fee inferred or position adopted; entries and automated exits blocked. Review reconciliation.csv and the paper holding.') from None
            time.sleep(delay)
        except Exception:
            store.state['reconciliation'].update(status='failed_closed', attempts=attempt,
                observed_at_utc=engine.utc(time.time()))
            store.save()
            raise
        else:
            store.state['reconciliation'].update(attempts=attempt, retry_exhausted=False)
            store.save()
            return actual, opened


_ORIGINAL_REPORT = engine.report


def report(state, status, quotes, output):
    diagnostic = copy.deepcopy(state.get('reconciliation', {}))
    # Never attribute a previous tick's reconciliation to a read-only check.
    if status.get('mode') == 'tick' and diagnostic:
        status['reconciliation'] = diagnostic
        if state.get('observations'):
            state['observations'][-1]['reconciliation'] = diagnostic
        from cryptolab import atomic_json
        if _ACTIVE_STATE_PATH is not None:
            atomic_json(_ACTIVE_STATE_PATH, state)
    _ORIGINAL_REPORT(state, status, quotes, output)
    if status.get('mode') != 'tick' or not diagnostic:
        return
    directory = Path(output)
    fields = ['symbol', 'filled_quantity', 'fee_quantity', 'expected_quantity',
              'broker_quantity', 'difference_quantity', 'tolerance_quantity']
    engine.write_csv(directory / 'reconciliation.csv', diagnostic.get('quantities', []), fields)
    (directory / 'reconciliation.json').write_text(json.dumps(diagnostic, indent=2) + '\n')
    lines = ['\n## Reconciliation', '', 'Status: ' + diagnostic.get('status', 'unknown'),
             'Read-only attempts: ' + str(diagnostic.get('attempts', 0)), '']
    lines += engine.table(['Coin', 'Expected', 'Broker', 'Difference'], [
        [row[key] for key in ('symbol', 'expected_quantity', 'broker_quantity', 'difference_quantity')]
        for row in diagnostic.get('quantities', [])])
    if diagnostic.get('status') != 'matched':
        lines += ['', 'UNRESOLVED: new entries and automated exits are blocked. Review the paper holding. No missing fee has been invented.']
    lines += ['', 'Full diagnostics: reconciliation.csv and reconciliation.json.', '']
    for name in ('summary.md', 'journal.md'):
        with (directory / name).open('a') as handle:
            handle.write('\n'.join(lines))


_ACTIVE_STATE_PATH = None


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
    engine.owned_positions = owned_positions
    engine.update_fees = update_fees
    engine.report = report
    # Clear only diagnostics, never orders, positions, cycles or deduplication.
    original_load = engine.load
    def load_for_run(path):
        state = original_load(path)
        if args.mode == 'tick':
            state['reconciliation'] = dict(status='not_started', quantities=[])
        return state
    engine.load = load_for_run
    engine.run(args.mode, args.state, args.output, args.execution_config, args.checkpoint_script)


if __name__ == '__main__':
    main()
