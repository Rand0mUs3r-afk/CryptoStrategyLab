"""Persisted quantity replay with synthetic ownership/history; no broker requests."""
import copy
from decimal import Decimal as D, ROUND_HALF_UP
from types import SimpleNamespace as NS
import pytest
import alpaca_crypto as engine
import alpaca_reconciled as repaired

BUYS={
    'AAVEUSD':'1.487541837 1.444147591 1.454545454 1.498228344 1.475905837 1.560062402',
    'BTCUSD':'0.002465863 0.002491328 0.002574304 0.002572120 0.002567047 0.002556900 0.002548899 0.002586804',
    'ETHUSD':'0.085015940 0.084922083 0.086782579 0.088206756 0.088187309 0.088386070 0.087416790 0.088233218',
    'TRUMPUSD':'117.164616285 118.063754427 124.937531234',
}
# Net fills, confirmed signed fee quantity, and broker position from the incident.
VALUES={
    'AAVEUSD':('0.022301081','-0.018400924','0'),
    'BTCUSD':('0.002631256','-0.000044452','0.002580336'),
    'ETHUSD':('0.089755515','-0.001522297','0.088012634'),
    'TRUMPUSD':('0.900414757','-0.588070928','0'),
}
NOW=1804309200

@pytest.fixture(autouse=True)
def policy(monkeypatch):
    for key,value in {'allow_fee_pending_exits':True,'allow_fee_pending_entries':True,'pending_fee_rate_bps':25,'pending_fee_max_age_seconds':172800}.items():
        monkeypatch.setitem(repaired._POLICY,key,value)
    monkeypatch.setattr(repaired.time,'time',lambda:NOW)

def incident():
    orders={};cycles=[];fees={};positions=[]
    def add(pair,side,qty,age,cycle_id):
        cid='csl2-'+format(len(orders)+1,'032x')
        payload=dict(symbol=pair,side=side,qty=str(qty),type='market',time_in_force='gtc',client_order_id=cid)
        orders[cid]=dict(payload=payload,cycle_id=cycle_id,status='filled',filled_qty=str(qty),filled_avg_price=1,filled_at=engine.utc(NOW-age))
    for key,text in BUYS.items():
        pair=key[:-3]+'/USD';quantities=text.split();filled,fee,broker=map(D,VALUES[key])
        for i,qty in enumerate(quantities):
            cycle_id=key+'-'+str(i)
            active=i==len(quantities)-1 and broker>0
            cycles.append(dict(id=cycle_id,symbol=pair,status='open' if active else 'closed'))
            add(pair,'buy',qty,30 if i==len(quantities)-1 else 345600,cycle_id)
        add(pair,'sell',sum(map(D,quantities))-filled,20,key+'-0')
        fees[key]=dict(id=key,symbol=key,qty=str(fee),activity_type='CFEE')
        if broker: positions.append(dict(symbol=key,qty=str(broker),qty_available=str(broker)))
    state=dict(orders=orders,cycles=cycles,fees=fees,activated_at=NOW-604800)
    history=[dict(order['payload'],id=str(i),status='filled',filled_qty=order['filled_qty'],filled_avg_price='1',filled_at=order['filled_at'],updated_at=order['filled_at']) for i,order in enumerate(orders.values())]
    class Broker:
        def __init__(self): self.history=history;self.positions=positions;self.calls=[]
        def snapshot(self): return self.positions,[]
        def call(self,method,path,**kwargs):
            self.calls.append((method,path));assert method=='GET' and path=='/v2/orders'
            return self.history
    api=Broker();store=NS(state=state)
    return api,store

def mismatch(api,store):
    with pytest.raises(repaired.PositionMismatch) as caught: repaired.position_snapshot(api,store)
    return caught.value

def test_old_nearest_rounding_reproduces_rejection(monkeypatch):
    api,store=incident();error=mismatch(api,store)
    monkeypatch.setattr(repaired,'ROUND_CEILING',ROUND_HALF_UP)
    assert repaired.allow_pending(api,store,error) is False
    assert api.calls==[]

def test_upper_bound_rounding_recovers_only_provisional_state():
    api,store=incident();error=mismatch(api,store)
    fees=copy.deepcopy(store.state['fees']);orders=copy.deepcopy(store.state['orders']);positions=copy.deepcopy(api.positions)
    assert repaired.allow_pending(api,store,error) is True
    result=store.state['reconciliation']
    assert result['status']=='fee_pending' and result['accounting_final'] is False
    assert result['exit_checks_allowed'] is True and result['entries_blocked'] is False
    assert store.state['fees']==fees and store.state['orders']==orders and api.positions==positions
    assert repaired.TOLERANCE==D('0.00000001')
    assert api.calls==[('GET','/v2/orders')]

@pytest.mark.parametrize('broker_qty',['0.0025','0.003'])
def test_unexplained_shortfall_or_excess_still_blocks(broker_qty):
    api,store=incident();next(p for p in api.positions if p['symbol']=='BTCUSD')['qty']=broker_qty
    assert repaired.allow_pending(api,store,mismatch(api,store)) is False

def test_stale_missing_fees_still_block():
    api,store=incident()
    for order in store.state['orders'].values(): order['filled_at']=engine.utc(NOW-345600)
    assert repaired.allow_pending(api,store,mismatch(api,store)) is False

@pytest.mark.parametrize('problem',['foreign','missing','truncated'])
def test_ownership_guards_still_block(problem):
    api,store=incident();error=mismatch(api,store)
    if problem=='foreign': api.history.append(dict(api.history[0],client_order_id='foreign'))
    elif problem=='missing': api.history=[]
    else: api.history=(api.history*500)[:500]
    with pytest.raises(engine.SafetyError): repaired.allow_pending(api,store,error)

def test_explicit_disabled_pending_policy_still_blocks(monkeypatch):
    api,store=incident();error=mismatch(api,store)
    monkeypatch.setitem(repaired._POLICY,'allow_fee_pending_exits',False)
    assert repaired.allow_pending(api,store,error) is False

def test_entries_can_remain_paused_while_exit_checks_are_allowed(monkeypatch):
    api,store=incident();error=mismatch(api,store)
    monkeypatch.setitem(repaired._POLICY,'allow_fee_pending_entries',False)
    assert repaired.allow_pending(api,store,error) is True
    assert store.state['reconciliation']['entries_blocked'] is True
