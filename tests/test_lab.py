"""Mechanical fixtures only; not simulated market performance claims."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
import cryptolab as lab

@pytest.fixture
def c(): return lab.config()

@pytest.fixture
def bars():
    price = 100+np.arange(300)*.1
    return pd.DataFrame(dict(time=1699999800+np.arange(300)*300, open=price,
                             high=price+1, low=price-1, close=price+.2, volume=100.))

@pytest.mark.parametrize('name', lab.STRATEGIES)
def test_no_future_leakage(name, bars):
    original = lab.signals(lab.features(bars), name)
    changed = bars.copy()
    changed.loc[250:, ['open','high','low','close']] *= 5
    pd.testing.assert_series_equal(original.iloc[:250], lab.signals(lab.features(changed), name).iloc[:250])

def test_channels_exclude_current(bars):
    assert lab.features(bars).iloc[240].high20 == bars.iloc[220:240].high.max()

def test_closed_candles_only():
    rows = [[0,99,101,100,100,1],[300,99,101,100,100,1]]
    assert lab.normalize(rows,300,0,450).time.tolist() == [0]

def test_conflicting_duplicates():
    with pytest.raises(ValueError, match='Conflicting'):
        lab.normalize([[0,99,101,100,100,1],[0,99,101,100,100,2]],300,0,300)

def test_identical_duplicates():
    row = [0,99,101,100,100,1]
    assert len(lab.normalize([row,row],300,0,300)) == 1

def test_missing_candles():
    with pytest.raises(ValueError, match='Missing'):
        lab.normalize([[0,99,101,100,100,1],[600,99,101,100,100,1]],300,0,900)

def test_bad_ohlc():
    with pytest.raises(ValueError, match='Inconsistent'):
        lab.normalize([[0,99,98,100,100,1]],300,0,300)

def test_nonfinite():
    with pytest.raises(ValueError, match='Nonfinite'):
        lab.normalize([[0,99,101,100,float('nan'),1]],300,0,300)

def test_public_endpoints_only():
    with pytest.raises(ValueError): lab.PublicMarket().get('/orders')

def test_identity_fail_closed(monkeypatch):
    m = lab.PublicMarket()
    monkeypatch.setattr(m,'get',lambda path: dict(id='BTC-USDT',base_currency='BTC',quote_currency='USDT'))
    with pytest.raises(ValueError,match='identity'): m.product('BTC-USD')

def test_stale_quote(monkeypatch):
    m = lab.PublicMarket()
    monkeypatch.setattr(m,'get',lambda path: dict(bid='100',ask='101',time='2020-01-01T00:00:00Z'))
    with pytest.raises(ValueError,match='Stale'): m.quote('BTC-USD',120)

def test_ambiguous_bar_stop_first():
    assert lab.bar_exit(dict(stop=95,target=110,bars=1),SimpleNamespace(open=100,low=90,high=115,close=105),10) == (95,'stop')

def test_gap_stop():
    assert lab.bar_exit(dict(stop=95,target=110,bars=1),SimpleNamespace(open=80,low=75,high=100,close=90),10) == (80.,'gap_stop')

def test_gap_target_not_improved():
    assert lab.bar_exit(dict(stop=95,target=110,bars=1),SimpleNamespace(open=120,low=119,high=125,close=122),10) == (110,'target')

def test_fees_and_cash(c):
    b = lab.new_book(c)
    assert lab.enter(b,100,2,0,300,'up',c)
    assert b['position']['qty']*b['position']['entry'] <= 2000
    assert b['cash'] >= 0
    t = lab.exit_trade(b,100,600,'test',c)
    assert t['net_pnl'] < 0
    assert b['cash'] == pytest.approx(10000+t['net_pnl'])

def test_only_one_position(c):
    b=lab.new_book(c)
    assert lab.enter(b,100,2,0,300,'up',c)
    assert not lab.enter(b,100,2,0,300,'up',c)

def test_next_bar_fill(c,bars):
    sig=pd.Series(False,index=bars.index)
    sig.iloc[220]=True
    t,_=lab.backtest(lab.features(bars),sig,210,240,dict(seconds=300,hold=4),c)
    assert t[0]['entry_time']==bars.iloc[221].time
    assert t[0]['signal_time']==t[0]['entry_time']

def test_stress_drag(c):
    rr=[]
    for multiple in [1,2]:
        b=lab.new_book(c)
        lab.enter(b,100,2,0,300,'up',c,multiple)
        rr.append(lab.exit_trade(b,100,600,'test',c,multiple)['net_r'])
    assert rr[1]<rr[0]

def test_drawdown_latches(c):
    b=lab.new_book(c)
    b['cash']=8000
    lab.risk(b,100,1800000000,c)
    assert b['drawdown_paused']
    b['cash']=10000
    lab.risk(b,100,1800100000,c)
    assert b['drawdown_paused']

def test_daily_pause_resets(c):
    b=lab.new_book(c)
    lab.risk(b,100,1800000000,c)
    b['cash']=9750
    lab.risk(b,100,1800000001,c)
    assert b['daily_paused']
    lab.risk(b,100,1800100000,c)
    assert not b['daily_paused']

def test_empty_metrics(c):
    m=lab.metrics([],lab.new_book(c)['curve'],c)
    assert m['win_rate'] is None and m['win_rate_low95'] is None
    assert m['review']=='INSUFFICIENT_SAMPLE'

def test_purged_segments():
    s=lab.splits(3000,210,73)
    assert s[0][2]+73==s[1][1]
    assert s[1][2]+73==s[2][1]

def test_short_history_refused():
    with pytest.raises(ValueError): lab.splits(300,210,73)

def test_corrupt_state_refused(tmp_path,c):
    p=tmp_path/'state.json'
    p.write_text('invalid')
    with pytest.raises(json.JSONDecodeError): lab.load_state(p,c)

def test_changed_config_refused(tmp_path,c):
    p=tmp_path/'state.json'
    lab.atomic_json(p,lab.load_state(p,c))
    other=copy.deepcopy(c)
    other['target_r']=3
    with pytest.raises(ValueError,match='changed'): lab.load_state(p,other)

def test_ledger_tamper(tmp_path,c):
    p=tmp_path/'state.json'
    s=lab.load_state(p,c)
    lab.event(s,dict(kind='test',time=1))
    lab.atomic_json(p,s)
    assert lab.load_state(p,c)['events'][0]['time']==1
    s['events'][0]['time']=2
    lab.atomic_json(p,s)
    with pytest.raises(ValueError,match='integrity'): lab.load_state(p,c)

class FakeMarket:
    def __init__(self,bars): self.bars=bars
    def product(self,p): return dict(id=p)
    def candles(self,p,seconds,start,end):
        d=self.bars.copy()
        d['time']=np.arange(len(d))*seconds+end-len(d)*seconds
        return d
    def quote(self,p,max_age):
        return dict(bid=130.,ask=130.1,observed_at=lab.time.time(),provider_time=lab.time.time(),spread_bps=8.)

def test_forward_durable_independent_books(tmp_path,c,bars):
    c=copy.deepcopy(c)
    c['products']=['BTC-USD']
    c['timeframes']={'5m':c['timeframes']['5m']}
    p=tmp_path/'state.json'
    lab.paper(c,p,tmp_path/'out',True,FakeMarket(bars))
    s=lab.load_state(p,c)
    assert len(s['books'])==8 and s['runs']==1
    lab.paper(c,p,tmp_path/'out',True,FakeMarket(bars))
    assert lab.load_state(p,c)['runs']==2

def test_pause_does_not_block_quote_exits(tmp_path,c,bars):
    c=copy.deepcopy(c)
    c['products']=['BTC-USD']
    c['timeframes']={'5m':c['timeframes']['5m']}
    p=tmp_path/'state.json'
    lab.paper(c,p,tmp_path/'out',True,FakeMarket(bars))
    s=lab.load_state(p,c)
    key='BTC-USD|5m|ema_cross'
    assert lab.enter(s['books'][key],200,2,0,lab.time.time(),'up',c,quoted=True)
    lab.atomic_json(p,s)
    lab.paper(c,p,tmp_path/'out',True,FakeMarket(bars))
    s=lab.load_state(p,c)
    assert s['books'][key]['position'] is None
    assert s['trades'][0]['reason']=='observed_quote_stop'
    assert s['trades'][0]['exit']<130

def test_all_quotes_fail_no_fake_trades(tmp_path,c):
    class Broken:
        def product(self,p): raise ValueError('offline')
    p=tmp_path/'state.json'
    with pytest.raises(RuntimeError,match='No fresh quotes'): lab.paper(c,p,tmp_path/'out',True,Broken())
    s=lab.load_state(p,c)
    assert s['trades']==[] and s['runs']==1

def test_no_private_order_adapter():
    text=Path(lab.__file__).read_text()
    assert '.post(' not in text and 'api.alpaca.markets' not in text
