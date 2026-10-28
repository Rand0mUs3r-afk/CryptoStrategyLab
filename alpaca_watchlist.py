"""Dynamic paper watchlist: market activity plus news, never headline-only orders."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import requests
import alpaca_crypto as engine
import alpaca_reconciled as repaired

COINBASE = 'https://api.exchange.coinbase.com'
FEEDS = (('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
         ('Cointelegraph', 'https://cointelegraph.com/rss'))
EXCLUDED_BASES = {'USDC', 'USDT', 'DAI', 'USDP', 'PYUSD', 'GUSD', 'EURC'}
DEFAULTS = dict(max_symbols=12, max_universe=40, min_estimated_volume_usd=1000000,
                max_gain_pct=40, min_relative_volume=1.5, news_max_age_hours=24)
_LOCK = threading.Lock()
_LAST_REQUEST = 0.0


def download(url):
    global _LAST_REQUEST
    allowed = url.startswith(COINBASE + '/products') or url in {item[1] for item in FEEDS}
    if not allowed:
        raise ValueError('Discovery URL not allowed')
    if url.startswith(COINBASE):
        with _LOCK:
            wait = 0.18 - (time.monotonic() - _LAST_REQUEST)
            if wait > 0:
                time.sleep(wait)
            _LAST_REQUEST = time.monotonic()
    # Separate public session: never send Alpaca credentials to news/data sites.
    with requests.get(url, headers={'User-Agent': 'CryptoStrategyLab-watchlist/1.0'},
                      timeout=(4, 10), allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise ValueError('Public source HTTP ' + str(response.status_code))
        data = bytearray()
        for block in response.iter_content(16384):
            data.extend(block)
            if len(data) > 1500000:
                raise ValueError('Public response too large')
        return bytes(data)


def options(path='watchlist_config.json'):
    cfg = dict(DEFAULTS)
    if Path(path).exists():
        cfg.update(json.loads(Path(path).read_text()))
    for key, low, high in [('max_symbols', 6, 24), ('max_universe', 6, 60), ('news_max_age_hours', 1, 48)]:
        value = cfg[key]
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ValueError('Invalid watchlist setting ' + key)
    for key, low, high in [('min_estimated_volume_usd', 100000, 1000000000),
                           ('max_gain_pct', 1, 100), ('min_relative_volume', 1, 20)]:
        if isinstance(cfg[key], bool) or not isinstance(cfg[key], (int, float)) or not math.isfinite(cfg[key]) or not low <= cfg[key] <= high:
            raise ValueError('Invalid watchlist setting ' + key)
    if cfg['max_universe'] < cfg['max_symbols']:
        raise ValueError('Watchlist universe must cover maximum symbols')
    return cfg


def news_items(data, provider, now, hours):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entity not allowed in feed')
    root = ET.fromstring(data)
    found = []
    for item in root.findall('.//item')[:100]:
        title = ' '.join((item.findtext('title') or '').split())[:400]
        link = (item.findtext('link') or '').strip()
        try:
            published = parsedate_to_datetime(item.findtext('pubDate') or '')
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age = now - published.timestamp()
        except (TypeError, ValueError, OverflowError):
            continue
        if not title or not -300 <= age <= hours * 3600 or urlparse(link).scheme != 'https':
            continue
        found.append(dict(provider=provider, title=title, url=link,
                          published_at_utc=published.isoformat()))
    return found


def mentioned(title, assets):
    # Longest names win: Bitcoin Cash must not also count as Bitcoin.
    matches = []
    for symbol, asset in assets.items():
        ticker = symbol.split('/')[0]
        names = {asset.get('name', '')}
        if ticker == 'ETH':
            names.add('Ethereum')
        for name in names:
            if len(name) > 3:
                for match in re.finditer(r'(?<![A-Za-z0-9])' + re.escape(name) + r'(?![A-Za-z0-9])', title, re.I):
                    matches.append((match.start(), match.end(), symbol))
        pattern = r'(?<![A-Za-z0-9])(?:\$' + re.escape(ticker) + r'|' + re.escape(ticker) + r'/USD)(?![A-Za-z0-9])'
        if ticker in {'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'AVAX', 'LTC'}:
            pattern += r'|(?<![A-Za-z0-9])' + re.escape(ticker) + r'(?![A-Za-z0-9])'
        for match in re.finditer(pattern, title):
            matches.append((match.start(), match.end(), symbol))
    spans, symbols = [], set()
    for start, end, symbol in sorted(matches, key=lambda x: (-(x[1] - x[0]), x[0], x[2])):
        if any(start < b and end > a for a, b in spans):
            continue
        spans.append((start, end))
        symbols.add(symbol)
    return symbols


def market_row(symbol, raw):
    values = {key: float(raw[key]) for key in ('open', 'last', 'high', 'low', 'volume')}
    if any(not math.isfinite(value) or value <= 0 for value in values.values()):
        raise ValueError('Invalid market statistics')
    if values['high'] < values['low'] or not values['low'] <= values['last'] <= values['high']:
        raise ValueError('Inconsistent market range')
    volume30 = float(raw.get('volume_30day') or 0)
    if not math.isfinite(volume30) or volume30 < values['volume']:
        raise ValueError('Invalid 30-day volume')
    return dict(symbol=symbol, change_24h_pct=(values['last'] / values['open'] - 1) * 100,
        range_24h_pct=(values['high'] / values['low'] - 1) * 100,
        estimated_volume_usd=values['volume'] * values['last'],
        relative_24h_volume=values['volume'] / (volume30 / 30) if volume30 else 0,
        news_count=0, risk_headline=False, reasons=[], headlines=[])


def discover(base_symbols, assets, held, cfg, getter=download, now=None):
    now = time.time() if now is None else now
    stamp = datetime.fromtimestamp(now, timezone.utc).isoformat(timespec='seconds')
    base = sorted(set(base_symbols) & set(assets))
    held = sorted(set(held) & set(assets))
    result = dict(observed_at_utc=stamp, status='fresh', selected=[], ranked=[], news=[], errors=[],
                  sources=['Coinbase Exchange 24h/30d statistics', 'CoinDesk RSS', 'Cointelegraph RSS'])
    try:
        products = json.loads(getter(COINBASE + '/products'))
        if not isinstance(products, list):
            raise ValueError('Invalid product response')
        supported = {p.get('id', '').replace('-', '/') for p in products if p.get('quote_currency') == 'USD'
                     and p.get('status') == 'online' and p.get('trading_disabled') is False}
    except Exception as exc:
        result.update(status='fallback_core', selected=sorted(set(base + held)))
        result['errors'].append(dict(stage='products', error_type=type(exc).__name__))
        return result
    universe = sorted(s for s in set(assets) & supported if s.split('/')[0] not in EXCLUDED_BASES or s in held)
    ordered = list(dict.fromkeys([s for s in base + held if s in universe] + universe))
    chosen = ordered[:cfg['max_universe']]
    result.update(eligible_universe=len(universe), sampled_universe=len(chosen),
                  universe_capped=len(ordered) > len(chosen))
    def read_stats(symbol):
        try:
            row = market_row(symbol, json.loads(getter(COINBASE + '/products/' + symbol.replace('/', '-') + '/stats')))
            return row, None
        except Exception as exc:
            return None, dict(stage='statistics', symbol=symbol, error_type=type(exc).__name__)
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(read_stats, chosen))
    rows = []
    for row, error in outcomes:
        if row:
            rows.append(row)
        if error:
            result['errors'].append(error)
    articles = {}
    for provider, url in FEEDS:
        try:
            for article in news_items(getter(url), provider, now, cfg['news_max_age_hours']):
                key = re.sub(r'[^a-z0-9]', '', article['title'].lower())
                articles.setdefault(key, article)
        except Exception as exc:
            result['errors'].append(dict(stage='news', source=provider, error_type=type(exc).__name__))
    by_symbol = {row['symbol']: row for row in rows}
    for article in articles.values():
        symbols = sorted(mentioned(article['title'], assets))
        if not symbols:
            continue
        risk = bool(re.search(r'\b(hack(?:ed)?|exploit(?:ed)?|delist(?:ed|ing)?|fraud|insolven\w*|rug pull)\b', article['title'], re.I))
        result['news'].append(dict(article, symbols=symbols, risk_flag=risk))
        for symbol in symbols:
            if symbol in by_symbol:
                row = by_symbol[symbol]
                row['news_count'] += 1
                row['risk_headline'] |= risk
                row['headlines'].append(article)
    eligible = [r for r in rows if r['estimated_volume_usd'] >= cfg['min_estimated_volume_usd']
                and r['change_24h_pct'] <= cfg['max_gain_pct'] and not r['risk_headline']]
    def tag_top(values, key, label, count=4):
        for row in sorted(values, key=lambda r: (-r[key], r['symbol']))[:count]:
            row['reasons'].append(label)
    tag_top([r for r in eligible if r['change_24h_pct'] > 0], 'change_24h_pct', 'top_gainer')
    tag_top(eligible, 'range_24h_pct', 'large_24h_range')
    tag_top([r for r in eligible if r['news_count'] > 0], 'news_count', 'news_attention')
    emerging = [r for r in eligible if 0 < r['change_24h_pct'] <= 15 and r['relative_24h_volume'] >= cfg['min_relative_volume']]
    tag_top(emerging, 'relative_24h_volume', 'emerging_momentum')
    for row in rows:
        row['score'] = sum({'top_gainer': 3, 'large_24h_range': 2, 'news_attention': 1, 'emerging_momentum': 4}[tag] for tag in row['reasons'])
        row['eligible_dynamic'] = row in eligible
    ranked = sorted(rows, key=lambda r: (-r['score'], -r['relative_24h_volume'], r['symbol']))
    # Existing holdings are retained even if their headline or statistics are adverse.
    selected = list(held)
    for symbol in base:
        if len(selected) >= cfg['max_symbols']:
            break
        row = by_symbol.get(symbol)
        if symbol in supported and not (row and row['risk_headline']) and symbol not in selected:
            selected.append(symbol)
    for row in ranked:
        if len(selected) >= cfg['max_symbols']:
            break
        if row['eligible_dynamic'] and row['score'] > 0 and row['symbol'] not in selected:
            selected.append(row['symbol'])
    result.update(selected=selected, ranked=ranked, status='partial' if result['errors'] else 'fresh')
    for row in ranked:
        row['selected'] = row['symbol'] in selected
        if row['risk_headline']:
            row['exclusion'] = 'risk_headline'
        elif row['estimated_volume_usd'] < cfg['min_estimated_volume_usd']:
            row['exclusion'] = 'insufficient_venue_volume'
        elif row['change_24h_pct'] > cfg['max_gain_pct']:
            row['exclusion'] = 'extreme_gain_not_chased'
    return result


def main():
    original_scanner, original_execute, original_report = engine.candidates, repaired.execute, repaired.report
    context = {}
    def dynamic_scanner(cfg, lab, assets, market, errors):
        store = context['store']
        held = [c['symbol'] for c in store.state.get('cycles', []) if c['status'] != 'closed']
        settings = options()
        watch = discover(cfg['symbols'], assets, held, settings)
        store.state['watchlist'] = watch
        store.save()
        context['diagnostics']['watchlist_status'] = watch['status']
        context['diagnostics']['watchlist_symbols'] = watch['selected']
        scoped = dict(cfg, symbols=watch['selected'])
        return original_scanner(scoped, lab, assets, market, errors)
    def execute(api, store, cfg, lab, account, market, errors, diagnostics=None, quotes=None):
        diagnostics = diagnostics if diagnostics is not None else {}
        context.update(store=store, diagnostics=diagnostics)
        try:
            return original_execute(api, store, cfg, lab, account, market, errors, diagnostics, quotes)
        finally:
            context.clear()
    def report(state, status, quotes, output):
        original_report(state, status, quotes, output)
        watch = state.get('watchlist')
        if not watch:
            return
        directory = Path(output)
        (directory / 'watchlist.json').write_text(json.dumps(watch, indent=2) + '\n')
        engine.write_csv(directory / 'watchlist.csv', [dict(r, reasons=', '.join(r['reasons'])) for r in watch['ranked']],
            ['symbol', 'selected', 'change_24h_pct', 'range_24h_pct', 'estimated_volume_usd', 'relative_24h_volume', 'news_count', 'risk_headline', 'score', 'reasons', 'exclusion'])
        lines = ['\n## Discovery watchlist', '', 'Last refresh: ' + watch['observed_at_utc'],
                 'Source status: ' + watch['status'], 'Selected: ' + ', '.join(watch['selected']),
                 'Emerging momentum is a screening label, not an undervaluation or profit claim.',
                 'News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.',
                 'USD volume is estimated from Coinbase base volume times last price, not broker liquidity.',
                 'Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.', '']
        for name in ('summary.md', 'journal.md'):
            with (directory / name).open('a') as handle:
                handle.write('\n'.join(lines))
    engine.candidates = dynamic_scanner
    repaired.execute = execute
    repaired.report = report
    repaired.main()


if __name__ == '__main__':
    main()
