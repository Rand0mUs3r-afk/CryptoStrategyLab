"""Deterministic broker/market fixtures test mechanics, never trading performance."""
import copy
import json
import time
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock
import pytest
import requests
import alpaca_crypto as a
from cryptolab import config

ACCOUNT = '00000000-0000-0000-0000-000000000001'
ORDER_ID = '00000000-0000-0000-0000-000000000010'


def account():
    return dict(id=ACCOUNT, status='ACTIVE', crypto_status='ACTIVE', currency='USD',
                trading_blocked=False, account_blocked=False, trade_suspended_by_user=False,
                equity='10000', cash='10000', non_marginable_buying_power='10000')


def asset():
    return dict(symbol='BTC/USD', min_trade_increment='0.000001', min_order_size='0.000001')


def raw_order(p, status='filled', qty=None, price=100):
    return dict(p, id=ORDER_ID, status=status, filled_qty=str(qty if qty is not None else p['qty']),
                filled_avg_price=str(price), filled_at=a.utc(time.time()), updated_at=a.utc(time.time()))


class FakeBroker:
    def __init__(self):
        self.orders = {}
        self.qty = Decimal(0)
        self.bid = 99.9
        self.ask = 100.
        self.posts = []
        self.fee_rows = []
        self.events = []

    def account(self, expected):
        assert expected == ACCOUNT
        return account()

    def lookup(self, cid):
        return copy.deepcopy(self.orders.get(cid))

    def snapshot(self):
        positions = [dict(symbol='BTCUSD', asset_class='crypto', qty=str(self.qty),
                          qty_available=str(self.qty), market_value=str(self.qty*Decimal(str(self.bid))))] if self.qty else []
        opened = [o for o in self.orders.values() if o['status'] not in a.TERMINAL]
        return positions, opened

    def assets(self):
        return {'BTC/USD': asset()}

    def fees(self, after):
        return self.fee_rows

    def latest(self, symbols, now):
        return {'BTC/USD': dict(symbol='BTC/USD', bid=self.bid, ask=self.ask,
                               provider_time_utc=a.utc(now), spread_bps=(self.ask-self.bid)/self.ask*10000)}

    def call(self, method, path, **kwargs):
        self.events.append(method)
        if method == 'DELETE':
            for o in self.orders.values():
                if o['id'] == path.split('/')[-1]:
                    o['status'] = 'canceled'
            return
        assert method == 'POST' and path == '/v2/orders'
        p = kwargs['payload']
        assert p['client_order_id'] not in self.orders
        price = self.ask if p['side'] == 'buy' else self.bid
        self.qty += Decimal(p['qty'])*(1 if p['side'] == 'buy' else -1)
        assert self.qty >= 0
        r = raw_order(p, price=price)
        self.orders[p['client_order_id']] = r
        self.posts.append(p)
        return copy.deepcopy(r)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    s = dict(version=1, paper_only=True, observations=[], account_id=ACCOUNT)
    store = a.Store(tmp_path/'ledger.json', s)
    cfg = a.settings()
    cfg['symbols'] = ['BTC/USD']
    return FakeBroker(), store, cfg, config()


def idea(strategy='trend_pullback'):
    return dict(symbol='BTC/USD', timeframe='15m', strategy=strategy,
                signal_time=int(time.time()//900*900), atr=1., signal_close=100., hold_seconds=21600)


def test_entry_and_target_exit_complete_roundtrip(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    a.execute(api, store, cfg, lab, account(), None, [])
    assert len(api.posts) == 1 and api.posts[0]['side'] == 'buy'
    c = store.state['cycles'][0]
    assert c['status'] == 'open' and c['tp'] == 103. and c['sl'] == 98.5
    api.bid, api.ask = 104., 104.1
    monkeypatch.setattr(a, 'candidates', lambda *args: [])
    a.execute(api, store, cfg, lab, account(), None, [])
    assert len(api.posts) == 2 and api.posts[-1]['side'] == 'sell'
    assert api.qty == 0 and c['status'] == 'closed' and c['exit_reason'] == 'target'
    assert c['cashflow_pnl_before_usd_fees'] > 0


@pytest.mark.parametrize('reason', ['stop', 'time'])
def test_stop_and_time_exit(env, monkeypatch, reason):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    a.execute(api, store, cfg, lab, account(), None, [])
    c = store.state['cycles'][0]
    if reason == 'stop':
        api.bid, api.ask = 97., 97.1
    else:
        c['created_at'] -= c['hold_seconds']+1
    monkeypatch.setattr(a, 'candidates', lambda *args: [])
    a.execute(api, store, cfg, lab, account(), None, [])
    assert c['status'] == 'closed' and c['exit_reason'] == reason


def test_repeated_signal_and_multiple_strategies_cannot_duplicate(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea(), idea('ema_cross')])
    for _ in range(3):
        a.execute(api, store, cfg, lab, account(), None, [])
    assert len(api.posts) == 1


def test_entries_paused_still_manage_exits(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    a.execute(api, store, cfg, lab, account(), None, [])
    monkeypatch.setenv('ALPACA_CRYPTO_PAUSE_ENTRIES', 'true')
    api.bid, api.ask = 97., 97.1
    a.execute(api, store, cfg, lab, account(), None, [])
    assert api.posts[-1]['side'] == 'sell'


def test_empty_dedicated_account_required(env):
    api, store, cfg, lab = env
    api.qty = Decimal(1)
    with pytest.raises(a.SafetyError, match='empty dedicated'):
        a.execute(api, store, cfg, lab, account(), None, [])
    assert not api.posts


def test_unexplained_position_change_not_adopted(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    a.execute(api, store, cfg, lab, account(), None, [])
    api.qty += Decimal(1)
    with pytest.raises(a.SafetyError, match='reconciliation mismatch'):
        a.execute(api, store, cfg, lab, account(), None, [])
    assert len(api.posts) == 1


def test_fee_reductions_require_broker_activity(env, monkeypatch):
    api, store, cfg, lab = env
    monkeypatch.setattr(a, 'candidates', lambda *args: [idea()])
    a.execute(api, store, cfg, lab, account(), None, [])
    api.qty -= Decimal('.00001')
    with pytest.raises(a.SafetyError, match='fee reconciliation'):
        a.execute(api, store, cfg, lab, account(), None, [])
    api.fee_rows = [dict(id='fee1', symbol='BTCUSD', qty='-.00001', activity_type='CFEE', net_amount='0')]
    a.execute(api, store, cfg, lab, account(), None, [])
    assert store.state['cycles'][0]['remaining_qty'] == float(api.qty)


def test_remote_checkpoint_precedes_order_and_failure_prevents_post(env, monkeypatch):
    api, store, cfg, lab = env
    a.activate(api, store, [], [], time.time())
    store.script = 'checkpoint-fixture.sh'
    def fail(*args, **kwargs):
        api.events.append('checkpoint')
        return Mock(returncode=1)
    monkeypatch.setattr(a.subprocess, 'run', fail)
    cid = a.client_id(ACCOUNT, 'checkpoint')
    with pytest.raises(a.SafetyError, match='checkpoint failed'):
        a.submit_intent(api, store, a.payload('BTC/USD','buy',1,cid),cid,time.time())
    assert api.events == ['checkpoint'] and api.posts == []


def test_github_requires_checkpoint_script(env, monkeypatch):
    _, store, _, _ = env
    monkeypatch.setenv('GITHUB_ACTIONS','true')
    with pytest.raises(a.SafetyError, match='checkpoint script'):
        store.save(remote=True)


def test_successful_checkpoint_then_post(env, monkeypatch):
    api, store, _, _ = env
    store.state.update(orders={})
    store.script='fixture.sh'
    def checkpoint(*args, **kwargs):
        api.events.append('checkpoint')
        return Mock(returncode=0)
    monkeypatch.setattr(a.subprocess,'run',checkpoint)
    cid=a.client_id(ACCOUNT,'once')
    p=a.payload('BTC/USD','buy',1,cid)
    a.submit_intent(api,store,p,cid,time.time())
    a.submit_intent(api,store,p,cid,time.time())
    assert api.events == ['checkpoint','POST','checkpoint']
    assert len(api.posts)==1


def test_unknown_transport_never_blindly_retried(env):
    api, store, _, _ = env
    store.state.update(orders={})
    cid=a.client_id(ACCOUNT,'lost')
    p=a.payload('BTC/USD','buy',1,cid)
    api.call=Mock(side_effect=a.SafetyError('transport'))
    with pytest.raises(a.SafetyError):
        a.submit_intent(api,store,p,cid,time.time())
    api.call.reset_mock()
    with pytest.raises(a.SafetyError,match='Ambiguous'):
        a.reconcile_orders(api,store)
    api.call.assert_not_called()


def test_post_fill_crash_recovers_by_client_id(env):
    api,store,_,_=env
    cid=a.client_id(ACCOUNT,'recover')
    p=a.payload('BTC/USD','buy',1,cid)
    store.state['orders']={cid:dict(payload=p,cycle_id=cid,status='queued',created_at=time.time(),attempted=True,filled_qty='0')}
    api.orders[cid]=raw_order(p)
    a.reconcile_orders(api,store)
    assert store.state['orders'][cid]['status']=='filled'
    assert not api.posts


def test_abandoned_unsubmitted_queue_is_canceled_not_bought(env):
    api,store,_,_=env
    cid=a.client_id(ACCOUNT,'abandoned')
    p=a.payload('BTC/USD','buy',1,cid)
    store.state['orders']={cid:dict(payload=p,cycle_id=cid,status='queued',created_at=0,attempted=False,filled_qty='0')}
    a.reconcile_orders(api,store)
    assert store.state['orders'][cid]['status']=='canceled' and not api.posts


@pytest.mark.parametrize('change', [dict(symbol='SPY'),dict(type='limit'),dict(time_in_force='day'),
                                   dict(qty='nan'),dict(qty='0'),dict(side='short'),dict(client_order_id='foreign')])
def test_invalid_order_payload_rejected(change):
    p=a.payload('BTC/USD','buy',1,a.client_id(ACCOUNT,'valid'))
    p.update(change)
    with pytest.raises(a.SafetyError):
        a.API.validate_order(p)


def test_api_post_requires_verified_enabled_paper_session():
    api=a.API('fixture','fixture',writes=True)
    api.session.request=Mock()
    p=a.payload('BTC/USD','buy',1,a.client_id(ACCOUNT,'valid'))
    with pytest.raises(a.SafetyError):
        api.call('POST','/v2/orders',payload=p)
    api.session.request.assert_not_called()
    api.verified=True
    api.session.request.return_value=Mock(status_code=200,json=lambda:raw_order(p))
    api.call('POST','/v2/orders',payload=p)
    args=api.session.request.call_args
    assert args.args==('POST',a.PAPER+'/v2/orders') and args.kwargs['allow_redirects'] is False


@pytest.mark.parametrize('path', ['/v2/orders','/v2/positions','https://api.alpaca.markets/v2/orders'])
def test_no_bulk_delete_or_live_host(path):
    api=a.API('fixture','fixture',writes=True)
    api.verified=True
    api.session.request=Mock()
    with pytest.raises(a.SafetyError):
        api.call('DELETE',path)
    api.session.request.assert_not_called()


def test_partial_fill_monotonicity():
    cid=a.client_id(ACCOUNT,'partial')
    p=a.payload('BTC/USD','buy',2,cid)
    local=dict(payload=p,filled_qty='0')
    a.apply_order(local,raw_order(p,status='partially_filled',qty=1))
    assert local['filled_qty']=='1'
    with pytest.raises(a.SafetyError,match='Non-monotonic'):
        a.apply_order(local,raw_order(p,status='partially_filled',qty=.5))
    a.apply_order(local,raw_order(p,qty=2))
    assert local['status']=='filled'


def test_foreign_broker_identity_rejected():
    cid=a.client_id(ACCOUNT,'identity')
    p=a.payload('BTC/USD','buy',1,cid)
    raw=raw_order(p)
    raw['side']='sell'
    with pytest.raises(a.SafetyError,match='identity'):
        a.apply_order(dict(payload=p),raw)


def test_no_quote_no_entry(env,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    api.latest=lambda *args:{}
    a.execute(api,store,cfg,lab,account(),None,[])
    assert not api.posts


def test_total_cap_and_broker_quantity_precision(env,monkeypatch):
    api,store,cfg,lab=env
    cfg['max_total_notional_usd']=10.123456789
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    a.execute(api,store,cfg,lab,account(),None,[])
    qty=Decimal(api.posts[0]['qty'])
    assert qty*Decimal('100')<=Decimal(str(cfg['max_total_notional_usd']))
    assert qty % Decimal(asset()['min_trade_increment'])==0


def test_report_tracks_actual_fills_not_requested_quantities(env,tmp_path,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    a.execute(api,store,cfg,lab,account(),None,[])
    a.report(store.state,dict(status='PAPER_TICK_COMPLETED'),{},tmp_path)
    assert 'trend_pullback' in (tmp_path/'journal.md').read_text()
    assert 'filled_avg_price' in (tmp_path/'orders.csv').read_text()
    assert 'net_pnl' not in (tmp_path/'closed_trades.csv').read_text()
    assert 'USD fees' in (tmp_path/'summary.md').read_text()


def test_foreign_open_order_never_canceled(env):
    api,store,_,_=env
    a.activate(api,store,[],[],time.time())
    p=a.payload('BTC/USD','buy',1,a.client_id(ACCOUNT,'not-in-ledger'))
    api.orders[p['client_order_id']]=raw_order(p,status='new',qty=0)
    with pytest.raises(a.SafetyError,match='Foreign'):
        a.owned_positions(api,store)
    assert not api.events


def test_fees_pagination():
    api=a.API('fixture','fixture')
    first=[dict(id=str(i)) for i in range(100)]
    api.call=Mock(side_effect=[first,[dict(id='last')]])
    rows=api.fees('2026-01-01')
    assert len(rows)==101
    assert api.call.call_args.kwargs['params']['page_token']=='99'


def test_dust_reported_without_fabricated_close(env,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    a.execute(api,store,cfg,lab,account(),None,[])
    c=store.state['cycles'][0]
    api.qty=Decimal('.00000001')
    api.fee_rows=[dict(id='fee1',symbol='BTCUSD',qty=str(api.qty-Decimal(str(c['entry_qty']))),net_amount='0')]
    api.bid,api.ask=97.,97.1
    a.execute(api,store,cfg,lab,account(),None,[])
    assert c['status'] in ('open','dust_or_unavailable') and 'closed_at' not in c
    assert len(api.posts)==1


def test_workflow_uses_no_force_push_and_checkpoint_before_trading():
    text=Path('.github/workflows/alpaca-crypto-paper.yml').read_text()
    assert 'options: [check, plan, tick]' in text and 'cron:' in text
    assert '--checkpoint-script' in text and '--force' not in text
    assert 'ALPACA_CRYPTO_DEDICATED_ACCOUNT' in text


def test_partial_entry_canceled_then_only_filled_quantity_exits(env,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    a.execute(api,store,cfg,lab,account(),None,[])
    c=store.state['cycles'][0]
    cid=api.posts[0]['client_order_id']
    buy=store.state['orders'][cid]
    # Fixture represents a broker entry that was only partially filled from the outset.
    buy.update(status='partially_filled',filled_qty='1',created_at=time.time()-120)
    api.orders[cid].update(status='partially_filled',filled_qty='1')
    api.qty=Decimal('1')
    api.bid,api.ask=97.,97.1
    monkeypatch.setattr(a,'candidates',lambda *args:[])
    a.execute(api,store,cfg,lab,account(),None,[])
    assert 'DELETE' in api.events and buy['status']=='canceled'
    a.execute(api,store,cfg,lab,account(),None,[])
    assert api.posts[-1]['side']=='sell' and Decimal(api.posts[-1]['qty'])==Decimal('1')
    assert api.qty==0 and c['status']=='closed'


def test_wide_spread_blocks_entry_not_exit(env,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    api.bid=90.
    a.execute(api,store,cfg,lab,account(),None,[])
    assert not api.posts
    store.state['seen']={}
    api.bid=99.9
    a.execute(api,store,cfg,lab,account(),None,[])
    api.bid=90.
    a.execute(api,store,cfg,lab,account(),None,[])
    assert api.posts[-1]['side']=='sell'


def test_identity_change_cannot_relabel_saved_state(tmp_path,monkeypatch):
    p=tmp_path/'state.json'
    p.write_text(json.dumps(dict(version=1,paper_only=True,observations=[],account_id='different')))
    monkeypatch.setenv('ALPACA_EXPECTED_PAPER_ACCOUNT_ID',ACCOUNT)
    monkeypatch.setenv('ALPACA_PAPER_KEY_ID','fixture')
    monkeypatch.setenv('ALPACA_PAPER_SECRET_KEY','fixture')
    monkeypatch.setattr(a.API,'account',lambda self,expected:account())
    with pytest.raises(a.SafetyError,match='Persisted account mismatch'):
        a.run('check',p,tmp_path/'reports')
    assert json.loads(p.read_text())['account_id']=='different'


def test_failed_identity_reverification_revokes_writes():
    api=a.API('fixture','fixture',writes=True)
    api.verified=True
    api.call=Mock(return_value=dict(account(),id='wrong'))
    with pytest.raises(a.SafetyError):
        api.account(ACCOUNT)
    assert api.verified is False


def test_broker_lookup_only_404_means_not_found():
    api=a.API('fixture','fixture')
    api.call=Mock(side_effect=a.BrokerHTTPError(404))
    assert api.lookup('fixture') is None
    api.call=Mock(side_effect=a.BrokerHTTPError(500))
    with pytest.raises(a.BrokerHTTPError):
        api.lookup('fixture')


def test_fee_history_existing_before_activation_not_counted(env):
    api,store,_,_=env
    api.fee_rows=[dict(id='old',symbol='BTCUSD',qty='-1')]
    a.activate(api,store,[],[],time.time())
    a.update_fees(api,store)
    assert store.state['fees']=={}
    actual,_=a.owned_positions(api,store)
    assert actual=={}


def test_account_read_only_check_does_not_request_trades(tmp_path,monkeypatch):
    monkeypatch.setenv('ALPACA_EXPECTED_PAPER_ACCOUNT_ID',ACCOUNT)
    monkeypatch.setenv('ALPACA_PAPER_KEY_ID','fixture')
    monkeypatch.setenv('ALPACA_PAPER_SECRET_KEY','fixture')
    calls=[]
    def call(self,method,path,**kwargs):
        calls.append((method,path))
        return account()
    monkeypatch.setattr(a.API,'call',call)
    a.run('check',tmp_path/'ledger.json',tmp_path/'report')
    assert calls==[('GET','/v2/account')]


def test_stop_failure_report_does_not_claim_zero_orders(env,tmp_path,monkeypatch):
    api,store,cfg,lab=env
    monkeypatch.setattr(a,'candidates',lambda *args:[idea()])
    a.execute(api,store,cfg,lab,account(),None,[])
    a.report(store.state,dict(status='FAILED_CLOSED',reason='fixture transport'),{},tmp_path)
    assert 'FAILED_CLOSED' in (tmp_path/'summary.md').read_text()
    assert 'buy' in (tmp_path/'orders.csv').read_text()
