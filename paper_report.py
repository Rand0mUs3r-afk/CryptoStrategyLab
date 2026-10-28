"""Human-readable reporting over the existing simulation ledger; never changes state."""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

OPEN_FIELDS = ['product', 'timeframe', 'strategy', 'entry_time_utc', 'entry', 'qty',
               'entry_notional_usd', 'entry_fee_usd', 'total_entry_cost_usd', 'tp', 'sl',
               'mark_bid', 'quote_time_utc', 'quote_status', 'estimated_exit_fee_usd',
               'estimated_open_net_pnl_usd', 'cash_usd', 'marked_equity_usd',
               'estimated_liquidation_equity_usd', 'planned_risk_usd', 'book']
CLOSED_FIELDS = ['product', 'timeframe', 'strategy', 'entry_time_utc', 'exit_time_utc',
                 'entry', 'exit', 'qty', 'entry_notional_usd', 'total_entry_cost_usd',
                 'tp', 'sl', 'entry_fee', 'exit_fee', 'net_pnl', 'net_r', 'reason', 'book']


def utc(value):
    if value is None or value == '':
        return ''
    return datetime.fromtimestamp(float(value), timezone.utc).isoformat(timespec='seconds')


def identity(book):
    product, timeframe, strategy = book.split('|')
    return dict(product=product, timeframe=timeframe, strategy=strategy, book=book)


def write_csv(path, rows, fields):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def cell(value):
    return str(value).replace('|', '&#124;').replace('\n', ' ')


def money(value):
    return 'n/a' if value is None else f'{value:,.2f}'


def table(headers, rows):
    return ['| ' + ' | '.join(map(cell, headers)) + ' |',
            '| ' + ' | '.join('---' for _ in headers) + ' |'] + [
                '| ' + ' | '.join(map(cell, row)) + ' |' for row in rows]


def render(state, quotes, c, status, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    marks = {}
    for q in quotes:
        try:
            bid = float(q['bid'])
            observed = float(q['observed_at'])
            provider = float(q['provider_time'])
            current = float(status['observed_at'])
            if (math.isfinite(bid) and bid > 0 and observed >= current
                    and -30 <= observed-provider <= c['max_quote_age']):
                marks[q['product']] = dict(q, bid=bid)
        except (KeyError, ValueError, TypeError):
            continue
    opened, closed, books = [], [], []
    for trade in state['trades']:
        meta = identity(trade['book'])
        closed.append(dict(trade, **{k: v for k, v in meta.items() if k != 'book'},
                           entry_time_utc=utc(trade['entry_time']), exit_time_utc=utc(trade['exit_time']),
                           entry_notional_usd=trade['qty']*trade['entry'],
                           total_entry_cost_usd=trade['qty']*trade['entry']+trade['entry_fee'],
                           tp=trade['target'], sl=trade['stop']))
    for key, b in sorted(state['books'].items()):
        meta = identity(key)
        p = b.get('position')
        q = marks.get(meta['product'])
        bid = float(q['bid']) if q else None
        marked = b['cash'] + p['qty']*bid if p and bid is not None else (b['cash'] if not p else None)
        liquid = marked
        open_pnl = None
        if p:
            total = p['qty']*p['entry']+p['entry_fee']
            exit_value = p['qty']*bid*(1-c['slippage_bps']/10000) if bid is not None else None
            fee = exit_value*c['fee_bps']/10000 if exit_value is not None else None
            open_pnl = exit_value-fee-total if fee is not None else None
            liquid = b['cash']+exit_value-fee if fee is not None else None
            opened.append(dict(meta, entry_time_utc=utc(p['entry_time']), entry=p['entry'], qty=p['qty'],
                               entry_notional_usd=p['qty']*p['entry'], entry_fee_usd=p['entry_fee'],
                               total_entry_cost_usd=total, tp=p['target'], sl=p['stop'], mark_bid=bid,
                               quote_time_utc=utc(q['provider_time']) if q else '',
                               quote_status='FRESH_THIS_RUN' if q else 'MISSING_OR_STALE_UNEVALUATED',
                               estimated_exit_fee_usd=fee, estimated_open_net_pnl_usd=open_pnl,
                               cash_usd=b['cash'], marked_equity_usd=marked,
                               estimated_liquidation_equity_usd=liquid, planned_risk_usd=p['risk_usd']))
        done = [t for t in closed if t['book'] == key]
        wins = sum(t['net_pnl'] > 0 for t in done)
        books.append(dict(meta, position=p is not None, closed_trades=len(done),
                          win_rate=wins/len(done) if done else None,
                          realized_net_pnl=sum(t['net_pnl'] for t in done),
                          estimated_open_net_pnl=open_pnl, marked_equity=marked,
                          estimated_liquidation_equity=liquid))
    write_csv(out/'open_positions.csv', opened, OPEN_FIELDS)
    write_csv(out/'closed_trades.csv', closed, CLOSED_FIELDS)
    write_csv(out/'account_books.csv', books, ['product', 'timeframe', 'strategy', 'position', 'closed_trades',
              'win_rate', 'realized_net_pnl', 'estimated_open_net_pnl', 'marked_equity',
              'estimated_liquidation_equity', 'book'])
    preface = ['# Forward paper observation', '', 'Independent simulated books; no broker orders.',
               f"Fresh products: {status.get('fresh_products', 0)}. Errors: {len(status.get('errors', []))}. "
               f"Entries paused: {status.get('entries_paused', 'unknown')}.",
               f"Open positions: {len(opened)}. Completed trades: {len(closed)}.", '',
               'Each book has its own simulated capital: do not add these balances together.',
               'Net realized P&L includes completed trades only. Open net P&L estimates buying AND selling costs.',
               'Marked equity uses bid before future exit costs; liquidation equity deducts modeled selling costs.',
               'Missing/current-run quote unavailable = n/a, never a fabricated live mark.', '',
               '## Open position journal', '']
    open_table = table(['Coin', 'Bar', 'Strategy', 'Entry UTC', 'Entry price', 'Qty', 'Spent incl fee',
                        'TP', 'SL', 'Current bid', 'Est open net P&L'],
                       [[r['product'], r['timeframe'], r['strategy'], r['entry_time_utc'],
                         money(r['entry']), f"{r['qty']:.9f}", money(r['total_entry_cost_usd']),
                         money(r['tp']), money(r['sl']), money(r['mark_bid']),
                         money(r['estimated_open_net_pnl_usd'])] for r in opened])
    lines = preface + open_table + ['', '## Completed trade journal', ''] + table(
        ['Coin', 'Bar', 'Strategy', 'Entry', 'Exit', 'TP', 'SL', 'Net P&L', 'Reason', 'Exit UTC'],
        [[r['product'], r['timeframe'], r['strategy'], money(r['entry']), money(r['exit']),
          money(r['tp']), money(r['sl']), money(r['net_pnl']), r['reason'], r['exit_time_utc']] for r in closed])
    lines += ['', '## All independent books', ''] + table(
        ['Coin', 'Bar', 'Strategy', 'Open', 'Closed trades', 'Win rate', 'Realized net P&L',
         'Est open net P&L', 'Marked equity', 'Est liquidation equity'],
        [[r['product'], r['timeframe'], r['strategy'], r['position'], r['closed_trades'],
          'n/a' if r['win_rate'] is None else f"{r['win_rate']:.1%}", money(r['realized_net_pnl']),
          money(r['estimated_open_net_pnl']), money(r['marked_equity']),
          money(r['estimated_liquidation_equity'])] for r in books])
    lines += ['', 'Software TP/SL is evaluated only when an observation runs; it is NOT a standing exchange order.',
              'Historical candle touches do not imply executable forward fills. No proven win rate.',
              'Download open_positions.csv / closed_trades.csv for full precision and timestamps.']
    for name in ('summary.md', 'journal.md'):
        (out/name).write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (out/'open_positions.md').write_text('\n'.join(preface+open_table)+'\n', encoding='utf-8')
    return opened, closed, books


def refresh(c, state_path, output):
    from cryptolab import load_state
    out = Path(output)
    status = json.loads((out/'status.json').read_text())
    with (out/'quotes.csv').open() as stream:
        quotes = list(csv.DictReader(stream))
    return render(load_state(state_path, c), quotes, c, status, out)


def main():
    from cryptolab import config, paper
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--state', default='state/state.json')
    parser.add_argument('--output', default='output/paper')
    parser.add_argument('--pause-entries', action='store_true')
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    import os
    c = config(args.config)
    if args.report_only:
        refresh(c, args.state, args.output)
    else:
        try:
            paper(c, args.state, args.output,
                  args.pause_entries or os.getenv('CRYPTO_PAUSE_ENTRIES', '').lower() == 'true')
        finally:
            status_path = Path(args.output)/'status.json'
            if status_path.exists() and Path(args.state).exists():
                refresh(c, args.state, args.output)


if __name__ == '__main__':
    main()
