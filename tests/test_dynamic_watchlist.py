"""Synthetic discovery fixtures test filtering, not trading performance."""
from datetime import datetime, timezone
import json
import pytest
import alpaca_watchlist as watch

NOW = 1793217600
ASSETS = {symbol: {'name': name} for symbol, name in [
    ('BTC/USD', 'Bitcoin'), ('ETH/USD', 'Ethereum'), ('SOL/USD', 'Solana'),
    ('DOGE/USD', 'Dogecoin'), ('LINK/USD', 'Chainlink'), ('LTC/USD', 'Litecoin'),
    ('AVAX/USD', 'Avalanche'), ('USDC/USD', 'USD Coin')]}


def rss(title='Dogecoin activity expands', age=0):
    published = datetime.fromtimestamp(NOW - age, timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    return f'<rss><channel><item><title>{title}</title><link>https://example.org/news</link><pubDate>{published}</pubDate></item></channel></rss>'.encode()


def getter_factory(risks=False, fail_news=False, fail_products=False, overrides=None):
    stats = dict(open='100', last='105', high='110', low='95', volume='100000', volume_30day='1000000')
    def getter(url):
        if url == watch.COINBASE + '/products':
            if fail_products:
                raise ValueError('offline')
            return json.dumps([dict(id=s.replace('/', '-'), quote_currency='USD', status='online', trading_disabled=False) for s in ASSETS] + [dict(id='UNKNOWN-USD', quote_currency='USD', status='online', trading_disabled=False)]).encode()
        if url in {feed[1] for feed in watch.FEEDS}:
            if fail_news:
                raise ValueError('offline')
            return rss('Dogecoin hack reported' if risks else 'Dogecoin activity expands')
        symbol = url.split('/products/')[1].split('/stats')[0].replace('-', '/')
        return json.dumps(dict(stats, **(overrides or {}).get(symbol, {}))).encode()
    return getter


def discover(**kwargs):
    return watch.discover(['BTC/USD'], ASSETS, kwargs.pop('held', []), dict(watch.DEFAULTS, max_symbols=6), now=NOW, **kwargs)


def test_discovers_new_broker_supported_coin():
    result = discover(getter=getter_factory())
    assert 'DOGE/USD' in result['selected']
    row = next(r for r in result['ranked'] if r['symbol'] == 'DOGE/USD')
    assert 'emerging_momentum' in row['reasons']
    assert row['news_count'] == 1
    assert 'UNKNOWN/USD' not in result['selected']
    assert 'USDC/USD' not in result['selected']


def test_news_provenance_and_deduplication():
    result = discover(getter=getter_factory())
    assert len(result['news']) == 1
    assert result['news'][0]['url'] == 'https://example.org/news'
    assert result['news'][0]['provider'] == 'CoinDesk'


def test_risk_headline_blocks_new_candidate():
    result = discover(getter=getter_factory(risks=True))
    assert 'DOGE/USD' not in result['selected']
    row = next(r for r in result['ranked'] if r['symbol'] == 'DOGE/USD')
    assert row['exclusion'] == 'risk_headline'


def test_held_coin_retained_despite_news_risk():
    result = discover(getter=getter_factory(risks=True), held=['DOGE/USD'])
    assert 'DOGE/USD' in result['selected']


def test_feed_failure_does_not_stop_market_discovery():
    result = discover(getter=getter_factory(fail_news=True))
    assert result['selected']
    assert result['status'] == 'partial'
    assert len([e for e in result['errors'] if e['stage'] == 'news']) == 2


def test_product_failure_falls_back_without_expanding():
    result = discover(getter=getter_factory(fail_products=True), held=['SOL/USD'])
    assert result['status'] == 'fallback_core'
    assert result['selected'] == ['BTC/USD', 'SOL/USD']


def test_low_volume_new_coin_excluded():
    result = discover(getter=getter_factory(overrides={'DOGE/USD': dict(volume='1', volume_30day='30')}))
    assert 'DOGE/USD' not in result['selected']


def test_extreme_gain_is_not_chased():
    result = discover(getter=getter_factory(overrides={'DOGE/USD': dict(last='160', high='170')}))
    assert 'DOGE/USD' not in result['selected']
    assert next(r for r in result['ranked'] if r['symbol'] == 'DOGE/USD')['exclusion'] == 'extreme_gain_not_chased'


def test_missing_or_old_news_not_used():
    assert watch.news_items(rss(age=90000), 'test', NOW, 24) == []
    assert watch.news_items(b'<rss><item><title>Bitcoin</title></item></rss>', 'test', NOW, 24) == []


def test_dtd_entities_rejected():
    with pytest.raises(ValueError):
        watch.news_items(b'<!DOCTYPE rss><rss/>', 'test', NOW, 24)


def test_name_overlap_does_not_double_count():
    assert watch.mentioned('Bitcoin Cash gains', {'BTC/USD': {'name': 'Bitcoin'}, 'BCH/USD': {'name': 'Bitcoin Cash'}}) == {'BCH/USD'}


def test_common_words_do_not_match_ticker():
    assert 'LINK/USD' not in watch.mentioned('Click this link for market news', ASSETS)
    assert watch.mentioned('$LINK gains attention', ASSETS) == {'LINK/USD'}


@pytest.mark.parametrize('change', [dict(last='nan'), dict(volume='-1'), dict(high='90'), dict(volume_30day='1')])
def test_invalid_statistics_rejected(change):
    raw = dict(open='100', last='105', high='110', low='95', volume='100000', volume_30day='1000000')
    raw.update(change)
    with pytest.raises(ValueError):
        watch.market_row('DOGE/USD', raw)


def test_selection_bounded_and_deterministic():
    first = discover(getter=getter_factory())
    second = discover(getter=getter_factory())
    assert first == second
    assert len(first['selected']) <= 6


def test_options_reject_invalid_limits(tmp_path):
    path = tmp_path / 'watch.json'
    path.write_text(json.dumps(dict(max_symbols=1000)))
    with pytest.raises(ValueError):
        watch.options(path)


def test_disallowed_public_url_never_requested():
    with pytest.raises(ValueError):
        watch.download('https://example.org/credentials')
