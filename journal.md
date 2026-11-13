# Alpaca crypto PAPER bot

Status: PAPER_TICK_COMPLETED
Dedicated paper account only. Broker fills, not virtual experiment fills.
TP/SL are software checks at workflow runs, NOT standing bracket orders.
Coinbase closed candles produce signals; fresh Alpaca quotes price decisions.
Fees can post later. P&L below is before USD fees; no fabricated net performance.

## Entry diagnostics

Candidates: 1. Skipped: 0. Broker order results: 1.
Broker order results are not proof of fills; see orders.csv.

| Coin | Bar | Strategy | Outcome | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| HYPE/USD | 15m | donchian_breakout | order_result | broker_order_returned | {"broker_order_id": "386f226a-7007-46dd-a2a7-deeaecf80e4b", "broker_status": "pending_new", "client_order_id": "csl2-1862da9559a459e6150c42366dd6a3e3", "quantity": "2.713262426", "reference_ask": 73.712} |

Per-candidate decisions: entry_decisions.csv. Quotes checked for entries: quotes.csv.

## Data errors

| Coin | Bar | Stage | Error type |
| --- | --- | --- | --- |
| RENDER/USD | 5m | candles | ValueError |

## Open / pending positions

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PEPE/USD | 6h | bollinger_reversion | 4.55e-06 | 44052863.43612335 | 200.44052863436121 | 43942731.27753304 | 5.2531468577303116e-06 | 4.198426571134844e-06 | open |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | pending |
## Closed cycles

| Coin | Bar | Strategy | Entry | Filled qty | Entry dollars | Remaining | TP | SL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ETH/USD | 15m | trend_pullback | 2352.83 | 0.08501594 | 200.0280541102 | 0.0 | 2368.832612413611 | 2344.8286937931944 | closed |
| SOL/USD | 5m | trend_pullback | 102.0 | 1.962246379 | 200.149130658 | 0.0 | 102.407696 | 101.796152 | closed |
| BTC/USD | 1h | trend_pullback | 81141.525053225 | 0.002465863 | 200.08388439232058 | 0.0 | 82340.13793842054 | 80542.21861062724 | closed |
| ETH/USD | 1h | trend_pullback | 2355.8 | 0.084922083 | 200.0594431314 | 0.0 | 2403.3986052917962 | 2332.000697354102 | closed |
| SOL/USD | 1h | trend_pullback | 102.297 | 1.955034213 | 199.994134887261 | 0.0 | 104.62114764381133 | 101.13492617809433 | closed |
| LINK/USD | 1h | macd_momentum | 11.85 | 16.87763713 | 199.9999999905 | 0.0 | 12.243345161382472 | 11.653327419308763 | closed |
| ARB/USD | 1h | donchian_breakout | 0.176896 | 1129.969038848 | 199.88700309605582 | 0.0 | 0.1847036898550324 | 0.17299215507248378 | closed |
| PEPE/USD | 5m | trend_pullback | 5.04e-06 | 39682539.68253968 | 199.99999999999997 | 0.0 | 5.161466000949713e-06 | 4.979266999525144e-06 | closed |
| UNI/USD | 5m | trend_pullback | 7.248 | 27.601435274 | 200.055202865952 | 0.0 | 7.315980677349064 | 7.214009661325468 | closed |
| PEPE/USD | 5m | trend_pullback | 5.04e-06 | 39761431.411530815 | 200.39761431411532 | 0.0 | 5.137478146438155e-06 | 4.991260926780923e-06 | closed |
| PEPE/USD | 5m | bollinger_reversion | 4.88e-06 | 40899795.501022495 | 199.59100204498978 | 0.0 | 5.0278268626405795e-06 | 4.80608656867971e-06 | closed |
| ARB/USD | 15m | bollinger_reversion | 0.16432 | 1217.433649866 | 200.0486973459811 | 0.0 | 0.16884034877884005 | 0.16205982561057997 | closed |
| ETH/USD | 1h | bollinger_reversion | 2305.2 | 0.086782579 | 200.05120111079998 | 0.0 | 2359.320736026376 | 2278.1396319868118 | closed |
| DOT/USD | 15m | rsi_rebound | 0.9702 | 206.185779572 | 200.0414433407544 | 0.0 | 0.9933076118532437 | 0.958646194073378 | closed |
| SOL/USD | 15m | rsi_rebound | 100.121 | 1.997443272 | 199.98601783591198 | 0.0 | 101.35444207935545 | 99.50427896032227 | closed |
| BTC/USD | 1h | bollinger_reversion | 80283.540728391 | 0.002491328 | 200.0126329557809 | 0.0 | 81609.51263608344 | 79620.55477454478 | closed |
| PEPE/USD | 15m | trend_pullback | 5.09e-06 | 38241304.50980393 | 194.648239954902 | 0.0 | 5.32158489621366e-06 | 4.9742075518931705e-06 | closed |
| AVAX/USD | 5m | donchian_breakout | 8.818 | 22.639365101 | 199.63392146061798 | 0.0 | 8.890288014191333 | 8.781855992904333 | closed |
| HYPE/USD | 15m | ema_cross | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| ARB/USD | 15m | ema_cross | 0.17032 | 1174.398120963 | 200.0234879624182 | 0.0 | 0.1737328821130826 | 0.1686135589434587 | closed |
| FIL/USD | 15m | donchian_breakout | 0.9095 | 219.884121068 | 199.984608111346 | 0.0 | 0.9260077902125277 | 0.9012461048937361 | closed |
| HYPE/USD | 1h | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| PEPE/USD | 5m | bollinger_reversion | 4.86e-06 | 41237113.40206186 | 200.41237113402062 | 0.0 | 4.947608994219858e-06 | 4.816195502890071e-06 | closed |
| SOL/USD | 5m | donchian_breakout | 101.96 | 1.961938395 | 200.0392387542 | 0.0 | 102.8022141789213 | 101.53889291053935 | closed |
| PEPE/USD | 1h | trend_pullback | 5.03e-06 | 38668482.10735587 | 194.50246500000003 | 0.0 | 5.424840282494075e-06 | 4.832579858752963e-06 | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| HYPE/USD | 5m | bollinger_reversion | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| SOL/USD | 5m | rsi_rebound | 100.3 | 1.994415636 | 200.0398882908 | 0.0 | 101.01718373799453 | 99.94140813100273 | closed |
| AAVE/USD | 15m | trend_pullback | 134.489 | 1.487541837 | 200.058014116293 | 0.0 | 136.09900983532222 | 133.6839950823389 | closed |
| AVAX/USD | 15m | bollinger_reversion | 8.528 | 23.415639305 | 199.68857199304 | 0.0 | 8.594000202002652 | 8.494999898998675 | closed |
| LINK/USD | 5m | bollinger_reversion | 11.5471 | 17.328019407 | 200.0883728945697 | 0.0 | 11.613289919548077 | 11.514005040225962 | closed |
| ETH/USD | 5m | macd_momentum | 2267.56 | 0.088206756 | 200.01411163536 | 0.0 | 2276.6295999999998 | 2263.0252 | closed |
| AAVE/USD | 15m | donchian_breakout | 138.6 | 1.444147591 | 200.15885611259998 | 0.0 | 140.91959811562253 | 137.44020094218874 | closed |
| BTC/USD | 15m | trend_pullback | 77738.296008397 | 0.002574304 | 200.12200636760042 | 0.0 | 78049.059568397 | 77582.914228397 | closed |
| AVAX/USD | 15m | donchian_breakout | 8.872 | 22.519479349 | 199.792820784328 | 0.0 | 9.01437007758712 | 8.80081496120644 | closed |
| UNI/USD | 15m | trend_pullback | 7.181 | 27.90492457 | 200.38526333717 | 0.0 | 7.300773753751183 | 7.121113123124409 | closed |
| ETH/USD | 15m | trend_pullback | 2268.6 | 0.088187309 | 200.0617291974 | 0.0 | 2279.9521028114164 | 2262.9239485942917 | closed |
| HYPE/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| LINK/USD | 5m | trend_pullback | 11.7339 | 17.05029838 | 200.06649616108203 | 0.0 | 11.805452540737084 | 11.698123729631458 | closed |
| AAVE/USD | 15m | trend_pullback | 137.614 | 1.454545454 | 200.165818106756 | 0.0 | 139.66480060462044 | 136.58859969768977 | closed |
| BTC/USD | 5m | bollinger_reversion | 77777.084288058 | 0.00257212 | 200.05199403899974 | 0.0 | 78088.111700058 | 77621.570582058 | closed |
| UNI/USD | 5m | bollinger_reversion | 7.205 | 27.773534598 | 200.10831677859002 | 0.0 | 7.270419269591361 | 7.1722903652043195 | closed |
| ETH/USD | 15m | trend_pullback | 2264.065049526 | 0.08838607 | 200.11181195195852 | 0.0 | 2276.8293182366338 | 2257.6829151706834 | closed |
| BTC/USD | 15m | macd_momentum | 77940.6 | 0.002567047 | 200.0771834082 | 0.0 | 78276.92160587902 | 77772.43919706049 | closed |
| UNI/USD | 1h | donchian_breakout | 7.3045 | 27.404768429 | 200.17813098963052 | 0.0 | 7.549550005739403 | 7.181974997130299 | closed |
| SOL/USD | 1h | bollinger_reversion | 94.885 | 2.107477118 | 199.96796634142999 | 0.0 | 96.44891526039979 | 94.10304236980012 | closed |
| TRUMP/USD | 1h | donchian_breakout | 1.70826 | 117.164616285 | 200.14762741501409 | 0.0 | 1.7793160226095484 | 1.6727319886952257 | closed |
| TRUMP/USD | 1h | rolling_vwap_reclaim | 1.6931 | 118.063754427 | 199.89374262035372 | 0.0 | 1.7820998552547356 | 1.6486000723726324 | closed |
| AAVE/USD | 15m | bollinger_reversion | 133.552 | 1.498228344 | 200.09139179788798 | 0.0 | 135.68555812265961 | 132.48522093867018 | closed |
| LINK/USD | 1h | bollinger_reversion | 11.351 | 17.630465444 | 200.123413254844 | 0.0 | 11.639403080819955 | 11.206798459590024 | closed |
| SOL/USD | 1h | bollinger_reversion | 94.3207 | 2.121115706 | 200.0651181709142 | 0.0 | 95.86473168713084 | 93.54868415643458 | closed |
| UNI/USD | 1h | trend_pullback | 7.1791 | 27.882336539 | 200.1700822471349 | 0.0 | 7.42161978344981 | 7.057840108275095 | closed |
| SOL/USD | 15m | bollinger_reversion | 93.89 | 2.130606157 | 200.04261208072998 | 0.0 | 94.82614521801622 | 93.42192739099188 | closed |
| BTC/USD | 15m | ema_cross | 78236.044797716 | 0.0025569 | 200.04174294328 | 0.0 | 78682.87850149203 | 78012.62794582798 | closed |
| ETH/USD | 15m | donchian_breakout | 2288.24 | 0.08741679 | 200.03059554959998 | 0.0 | 2311.5322058677275 | 2276.593897066136 | closed |
| AAVE/USD | 1h | trend_pullback | 135.566 | 1.475905837 | 200.08265069874201 | 0.0 | 139.92848587099192 | 133.38475706450404 | closed |
| BTC/USD | 5m | trend_pullback | 78478.03458866 | 0.002548899 | 200.03258388500086 | 0.0 | 78791.89551265999 | 78321.10412666 | closed |
| AAVE/USD | 5m | donchian_breakout | 128.26 | 1.560062402 | 200.09360368051998 | 0.0 | 129.28408688045377 | 127.7479565597731 | closed |
| ETH/USD | 15m | donchian_breakout | 2268.428166476 | 0.088233218 | 200.1507169300172 | 0.0 | 2287.218323230117 | 2259.0330880989413 | closed |
| TRUMP/USD | 5m | donchian_breakout | 1.601 | 124.937531234 | 200.02498750563402 | 0.0 | 1.6111050978694956 | 1.5959474510652523 | closed |
| BTC/USD | 5m | donchian_breakout | 77384.18 | 0.002586804 | 200.17770636071998 | 0.0 | 77693.44767373563 | 77229.54616313218 | closed |
| HYPE/USD | 5m | trend_pullback | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| PEPE/USD | 1h | macd_momentum | 5.01e-06 | 39920159.68063872 | 200.00000000000003 | 0.0 | 5.263353097673113e-06 | 4.8833234511634434e-06 | closed |
| UNI/USD | 1h | trend_pullback | 7.379 | 27.118644067 | 200.108474570393 | 0.0 | 7.736090787573656 | 7.200454606213172 | closed |
| ETH/USD | 1h | macd_momentum | 2301.9 | 0.086900074 | 200.0352803406 | 0.0 | 2357.8940243716884 | 2273.902987814156 | closed |
| LINK/USD | 15m | ema_cross | 11.13 | 17.977528089 | 200.08988763057002 | 0.0 | 11.341471359945134 | 11.024264320027434 | closed |
| HYPE/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| POL/USD | 15m | donchian_breakout | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| SOL/USD | 15m | donchian_breakout | 93.8938 | 2.130814994 | 200.07031688363722 | 0.0 | 95.06239491305311 | 93.30950254347344 | closed |
| BTC/USD | 5m | bollinger_reversion | 78071.2 | 0.002561208 | 199.9565820096 | 0.0 | 78432.69577880135 | 77890.45211059932 | closed |
| BTC/USD | 5m | trend_pullback | 78544.311 | 0.002546619 | 200.022434734509 | 0.0 | 78942.66623833876 | 78345.13338083062 | closed |
| LINK/USD | 15m | donchian_breakout | 11.69 | 17.137960582 | 200.34275920358002 | 0.0 | 11.971892183110988 | 11.549053908444504 | closed |
| SOL/USD | 15m | donchian_breakout | 96.523 | 2.067758374 | 199.58624153360196 | 0.0 | 98.75804789759727 | 95.40547605120136 | closed |
| BTC/USD | 1h | donchian_breakout | 80600.909 | 0.00248268 | 200.10626475612 | 0.0 | 82524.74630170345 | 79638.99034914827 | closed |
| ETH/USD | 1h | donchian_breakout | 2441.927 | 0.077328403 | 188.83031515258102 | 0.0 | 2517.287691655622 | 2404.246654172189 | closed |
| SOL/USD | 15m | trend_pullback | 95.17 | 2.102607232 | 200.10513026944 | 0.0 | 97.03783371062269 | 94.23608314468865 | closed |
| ONDO/USD | 15m | trend_pullback | 0.410972 | 486.570650058 | 199.96691319563638 | 0.0 | 0.42140262376781346 | 0.4057566881160933 | closed |
| LINK/USD | 15m | trend_pullback | 11.59 | 17.256255392 | 199.99999999328 | 0.0 | 11.807369977836238 | 11.48131501108188 | closed |
| LINK/USD | 15m | trend_pullback | 11.477331943 | 17.404925593 | 199.7621084740771 | 0.0 | 11.667372015496435 | 11.38231190675178 | closed |
| RENDER/USD | 15m | trend_pullback | 1.62653 | 122.827488791 | 199.7825953432252 | 0.0 | 1.6700577053551326 | 1.6047661473224337 | closed |
| SOL/USD | 15m | donchian_breakout | 96.6316 | 2.068971224 | 199.92799972907844 | 0.0 | 97.98171627061451 | 95.95654186469275 | closed |
| RENDER/USD | 15m | trend_pullback | 1.6069 | 124.428407005 | 199.94400721633448 | 0.0 | 1.6389355580017448 | 1.5908822209991276 | closed |
| ARB/USD | 15m | trend_pullback | 0.16392 | 1221.001221001 | 200.14652014648394 | 0.0 | 0.16669779274923682 | 0.1625311036253816 | closed |
| TRUMP/USD | 5m | bollinger_reversion | 1.23045 | 162.350840165 | 199.76459128102425 | 0.0 | 1.2518833942425258 | 1.2197333028787372 | closed |
| BTC/USD | 15m | bollinger_reversion | 79059.09 | 0.002528717 | 199.91806488753 | 0.0 | 79687.8388062688 | 78744.71559686559 | closed |
| UNI/USD | 15m | rsi_rebound | 7.22543 | 27.693159789 | 200.09498753423426 | 0.0 | 7.370993364755867 | 7.1526483176220665 | closed |
| SOL/USD | 5m | bollinger_reversion | 91.1844 | 2.194040984 | 200.06231070144958 | 0.0 | 93.16621511791254 | 90.19349244104373 | closed |
| BTC/USD | 1h | bollinger_reversion | 75995.880171653 | 0.002632171 | 200.03415190730004 | 0.0 | 78167.06678227903 | 74910.28686633999 | closed |
| ETH/USD | 1h | bollinger_reversion | 2246.47 | 0.08904323 | 200.0329448981 | 0.0 | 2326.647858081802 | 2206.3810709590985 | closed |
| SOL/USD | 15m | rsi_rebound | 90.05 | 2.222222222 | 200.1111110911 | 0.0 | 92.24357750062816 | 88.9532112496859 | closed |
| LINK/USD | 1h | rsi_rebound | 10.82 | 18.501387604 | 200.18501387528002 | 0.0 | 11.344656284249725 | 10.557671857875139 | closed |
| TRUMP/USD | 5m | trend_pullback | 1.2087 | 165.498522925 | 200.0380646594475 | 0.0 | 1.2504055615895013 | 1.1878472192052494 | closed |
| ONDO/USD | 5m | rsi_rebound | 0.366236 | 545.348450392 | 199.72623507776453 | 0.0 | 0.37229023919876864 | 0.36320888040061566 | closed |
| ARB/USD | 1h | ema_cross | 0.165593 | 1207.802403526 | 200.0036234070809 | 0.0 | 0.17492801982768363 | 0.16092549008615817 | closed |
| PEPE/USD | 6h | trend_pullback | 4.93e-06 | 40567951.318458416 | 200.0 | 0.0 | 5.6313488264385755e-06 | 4.579325586780713e-06 | closed |
| XRP/USD | 5m | bollinger_reversion | 1.18303 | 168.918918918 | 199.83614864756154 | 0.0 | 1.1944162928606987 | 1.1773368535696507 | closed |
| SOL/USD | 5m | trend_pullback | 90.22 | 2.184292716 | 197.06688883752 | 0.0 | 90.71425254043615 | 89.97287372978192 | closed |
| RENDER/USD | 15m | trend_pullback | 1.6053 | 122.046589311 | 195.9213898209483 | 0.0 | 1.6539345533305592 | 1.5809827233347205 | closed |
| SOL/USD | 5m | ema_cross | 90.1754 | 2.175210665 | 196.15049180064096 | 0.0 | 90.68566924307164 | 89.92026537846418 | closed |
| RENDER/USD | 15m | trend_pullback | 1.58061 | 125.296740202 | 198.04528053068321 | 0.0 | 1.6112540981052377 | 1.5652879509473814 | closed |
| SOL/USD | 15m | bollinger_reversion | 89.9579 | 2.223425342 | 200.0146745731018 | 0.0 | 90.7451881079653 | 89.56425594601734 | closed |
| HYPE/USD | 15m | bollinger_reversion | n/a | n/a | n/a | 0.0 | n/a | n/a | closed |
| AAVE/USD | 15m | trend_pullback | 131.9 | 1.516622179 | 200.04246541010002 | 0.0 | 133.52356834455492 | 131.08821582772254 | closed |
| SOL/USD | 1h | bollinger_reversion | 89.75232266 | 2.229405863 | 200.0943543560718 | 0.0 | 91.2379270674575 | 89.00952045627125 | closed |
| LTC/USD | 5m | bollinger_reversion | 51.796 | 3.852080123 | 199.52234205090798 | 0.0 | 52.059835133387054 | 51.66408243330647 | closed |
| SOL/USD | 1h | bollinger_reversion | 89.09 | 2.244920866 | 199.99999995194003 | 0.0 | 90.60555763529119 | 88.33222118235442 | closed |
| UNI/USD | 5m | bollinger_reversion | 6.977 | 28.684486425 | 200.131661787225 | 0.0 | 7.026001862545989 | 6.952499068727006 | closed |
| ETH/USD | 15m | bollinger_reversion | 2133.87 | 0.093763331 | 200.07875912097 | 0.0 | 2178.221243509793 | 2111.6943782451035 | closed |
| LINK/USD | 15m | rsi_rebound | 10.4317 | 19.193857965 | 200.2245681334905 | 0.0 | 10.648976580034741 | 10.323061709982628 | closed |
| SOL/USD | 15m | bollinger_reversion | 86.759 | 2.306326252 | 200.09455929726798 | 0.0 | 88.57139041511181 | 85.8528047924441 | closed |
| UNI/USD | 1h | rsi_rebound | 6.843 | 29.273147741 | 200.316149991663 | 0.0 | 7.098091022852047 | 6.715454488573976 | closed |
| BTC/USD | 5m | bollinger_reversion | 74263.9 | 0.002693468 | 200.02743820519999 | 0.0 | 74676.63158143718 | 74057.53420928141 | closed |
| RENDER/USD | 1h | ema_cross | 1.56799 | 127.551020408 | 199.9987244895399 | 0.0 | 1.6433661585431856 | 1.5303019207284072 | closed |
| ETH/USD | 5m | bollinger_reversion | 2109.164 | 0.094863699 | 200.08309883763602 | 0.0 | 2124.763868701307 | 2101.3640656493467 | closed |
| LINK/USD | 15m | rsi_rebound | 10.292 | 19.421624036 | 199.887354578512 | 0.0 | 10.498727159495576 | 10.188636420252212 | closed |
| BTC/USD | 1h | rsi_rebound | 74527.82 | 0.002685839 | 200.16972554098004 | 0.0 | 76094.09818437824 | 73744.68090781089 | closed |
| SOL/USD | 1h | rsi_rebound | 86.99 | 2.298927205 | 199.98367756295 | 0.0 | 89.91706099103635 | 85.52646950448182 | closed |
| RENDER/USD | 15m | ema_cross | 1.5941 | 125.944584382 | 200.76826196334622 | 0.0 | 1.6429052297457325 | 1.5696973851271339 | closed |
| ARB/USD | 15m | donchian_breakout | 0.176522 | 1068.802648556 | 188.66718112840223 | 0.0 | 0.18130899093296346 | 0.17412850453351827 | closed |
| XRP/USD | 15m | bollinger_reversion | 1.086 | 183.994332974 | 199.81784560976402 | 0.0 | 1.1079497452195028 | 1.0750251273902487 | closed |
| ETH/USD | 5m | rsi_rebound | 2102.24 | 0.095162871 | 200.05519393103998 | 0.0 | 2118.548584047813 | 2094.085707976093 | closed |
| SOL/USD | 5m | bollinger_reversion | 85.3689 | 2.344127257 | 200.11556539010726 | 0.0 | 86.03372526272248 | 85.03648736863875 | closed |
| LINK/USD | 1h | bollinger_reversion | 10.447 | 19.13875598 | 199.94258372305998 | 0.0 | 10.733994360492106 | 10.303502819753945 | closed |
| AAVE/USD | 1h | rsi_rebound | 125.01 | 1.6 | 200.01600000000002 | 0.0 | 129.788577246973 | 122.62071137651351 | closed |
| ARB/USD | 1h | bollinger_reversion | 0.16403 | 1221.001221001 | 200.28083028079405 | 0.0 | 0.1722575080426776 | 0.15991624597866122 | closed |
| SOL/USD | 5m | bollinger_reversion | 83.557 | 2.392974227 | 199.949747485439 | 0.0 | 84.55478691688593 | 83.05810654155704 | closed |
| UNI/USD | 1h | trend_pullback | 7.078 | 24.784504868 | 175.424725455704 | 0.0 | 7.40037484123546 | 6.91681257938227 | closed |
| SOL/USD | 15m | bollinger_reversion | 82.15 | 2.435163764 | 200.0487032126 | 0.0 | 84.32456114821323 | 81.06271942589339 | closed |
| BTC/USD | 1h | bollinger_reversion | 73174.0 | 0.002733599 | 200.028373226 | 0.0 | 75066.4026904474 | 72227.7986547763 | closed |
| ARB/USD | 1h | rsi_rebound | 0.160405 | 1246.882793017 | 200.0062344138919 | 0.0 | 0.17037393093457043 | 0.1554205345327148 | closed |
| TRUMP/USD | 15m | trend_pullback | 1.13441 | 176.511601224 | 200.23652554451783 | 0.0 | 1.1648626556677402 | 1.11918367216613 | closed |
| RENDER/USD | 15m | ema_cross | 1.599 | 116.713172607 | 186.624362998593 | 0.0 | 1.6383296124059326 | 1.5793351937970337 | closed |
| LINK/USD | 5m | macd_momentum | 10.4069 | 19.23076923 | 200.132692299687 | 0.0 | 10.493761997901364 | 10.36346900104932 | closed |
| FIL/USD | 15m | trend_pullback | 0.76375 | 254.411535039 | 194.30680988603626 | 0.0 | 0.7762799061305282 | 0.757485046934736 | closed |
| ETH/USD | 5m | trend_pullback | 2063.814 | 0.096934917 | 200.05563879343796 | 0.0 | 2075.456612573262 | 2057.9926937133687 | closed |
| SOL/USD | 5m | bollinger_reversion | 83.086 | 2.302557244 | 191.310271174984 | 0.0 | 83.64042499115591 | 82.80878750442204 | closed |
| LINK/USD | 5m | trend_pullback | 10.3838 | 18.338224587 | 190.4204564664906 | 0.0 | 10.454821394271297 | 10.348289302864353 | closed |
| UNI/USD | 15m | bollinger_reversion | 6.4357 | 31.110924445 | 200.22057645068648 | 0.0 | 6.621025015838152 | 6.343037492080924 | closed |
| SOL/USD | 5m | donchian_breakout | 83.7 | 2.389851733 | 200.0305900521 | 0.0 | 84.34990754624235 | 83.37504622687884 | closed |
| RENDER/USD | 1h | trend_pullback | 1.611 | 122.607095771 | 197.520031287081 | 0.0 | 1.6850784662255254 | 1.5739607668872373 | closed |
| DOT/USD | 15m | donchian_breakout | 0.86092 | 232.349025412 | 200.03392295769905 | 0.0 | 0.874996369143577 | 0.8538818154282115 | closed |
| SOL/USD | 5m | trend_pullback | 83.82 | 2.383790226 | 199.80929674331998 | 0.0 | 84.73291538334783 | 83.36354230832607 | closed |
| ETH/USD | 15m | donchian_breakout | 2095.29 | 0.094640123 | 198.29850332067002 | 0.0 | 2127.650414780107 | 2079.1097926099465 | closed |
| LINK/USD | 5m | trend_pullback | 10.4569 | 19.123932645 | 199.9770512755005 | 0.0 | 10.548678477460657 | 10.41101076126967 | closed |
| ETH/USD | 5m | bollinger_reversion | 2056.78 | 0.097214796 | 199.94944811688003 | 0.0 | 2070.459176056234 | 2049.9404119718833 | closed |
| LINK/USD | 15m | bollinger_reversion | 10.152 | 19.732817649 | 200.327564772648 | 0.0 | 10.396733497568604 | 10.029633251215696 | closed |
| SOL/USD | 15m | rsi_rebound | 82.8979 | 2.414138158 | 200.12698360806823 | 0.0 | 84.384954133019 | 82.15437293349052 | closed |
| RENDER/USD | 15m | bollinger_reversion | 1.55194 | 128.865979381 | 199.99226804054913 | 0.0 | 1.5872792964138849 | 1.5342703517930576 | closed |
| UNI/USD | 5m | bollinger_reversion | 6.179 | 32.388663967 | 200.129554652093 | 0.0 | 6.298095073060007 | 6.1194524634699965 | closed |
| ONDO/USD | 1h | bollinger_reversion | 0.35887 | 557.103064066 | 199.92757660136544 | 0.0 | 0.3755464471402786 | 0.3505317764298607 | closed |
| SOL/USD | 5m | bollinger_reversion | 82.826 | 2.414292612 | 199.96619988151198 | 0.0 | 83.34684653266098 | 82.5655767336695 | closed |
| DOT/USD | 15m | bollinger_reversion | 0.843608 | 237.23751152 | 200.13546261836416 | 0.0 | 0.8544830406625321 | 0.8381704796687339 | closed |
| UNI/USD | 5m | bollinger_reversion | 6.156 | 32.509752925 | 200.1300390063 | 0.0 | 6.21351471476696 | 6.127242642616519 | closed |
| SOL/USD | 5m | bollinger_reversion | 82.6727 | 2.419353863 | 200.0145161096401 | 0.0 | 83.02951044662264 | 82.49429477668869 | closed |
| ETH/USD | 15m | bollinger_reversion | 2023.88 | 0.09878353 | 199.9260106964 | 0.0 | 2045.066647183046 | 2013.2866764084772 | closed |
| LINK/USD | 15m | bollinger_reversion | 9.9915 | 20.02002002 | 200.03003002983002 | 0.0 | 10.114091687273127 | 9.930204156363438 | closed |
| SOL/USD | 15m | bollinger_reversion | 82.454 | 2.425418384 | 199.98544743433598 | 0.0 | 83.38064112649941 | 81.99067943675028 | closed |
| LINK/USD | 5m | bollinger_reversion | 9.84942 | 20.290149132 | 199.84620066370346 | 0.0 | 9.976557600444568 | 9.785851199777717 | closed |
| SOL/USD | 5m | bollinger_reversion | 80.83 | 2.472768635 | 199.87388876705 | 0.0 | 81.79343943357583 | 80.34828028321208 | closed |
| BTC/USD | 15m | rsi_rebound | 71789.62 | 0.002786979 | 200.07616335798 | 0.0 | 72867.39960341778 | 71250.7301982911 | closed |
| LINK/USD | 5m | macd_momentum | 10.02 | 19.96007984 | 199.99999999679997 | 0.0 | 10.122913115319868 | 9.968543442340065 | closed |
| PEPE/USD | 5m | trend_pullback | 4.56e-06 | 43859649.12280701 | 200.0 | 0.0 | 4.619714154376828e-06 | 4.530142922811586e-06 | closed |
| BTC/USD | 15m | bollinger_reversion | 71448.21 | 0.002800078 | 200.06056096038003 | 0.0 | 72105.5651435224 | 71119.5324282388 | closed |
| ADA/USD | 15m | donchian_breakout | 0.17523 | 1140.901312036 | 199.9201369080683 | 0.0 | 0.1778250673834666 | 0.1739324663082667 | closed |
| LINK/USD | 5m | trend_pullback | 10.08 | 19.845207382 | 200.03969041056 | 0.0 | 10.159292191908689 | 10.040353904045656 | closed |
| BTC/USD | 5m | bollinger_reversion | 69218.71 | 0.002891323 | 200.13364825333002 | 0.0 | 70032.80697925707 | 68811.66151037147 | closed |
| LINK/USD | 5m | bollinger_reversion | 9.802 | 20.406705643 | 200.02652871268597 | 0.0 | 9.958411708972267 | 9.723794145513866 | closed |
| ETH/USD | 15m | bollinger_reversion | 1934.349 | 0.103519668 | 200.24316627613197 | 0.0 | 1977.8675798250274 | 1912.589710087486 | closed |
| SOL/USD | 15m | bollinger_reversion | 78.537 | 2.545986888 | 199.95417222285602 | 0.0 | 80.28689104970933 | 77.66205447514534 | closed |
| UNI/USD | 5m | bollinger_reversion | 5.72526 | 35.013760407 | 200.4628819077808 | 0.0 | 5.838829354206556 | 5.668475322896721 | closed |
| LINK/USD | 5m | trend_pullback | 9.945 | 20.128399057 | 200.176928621865 | 0.0 | 10.034608889034732 | 9.900195555482634 | closed |

Order IDs, fill prices/times and quantities: orders.csv.
Closed trade cashflows: closed_trades.csv. Broker-reported fees: fees.csv.
Dust is kept in the ledger; it is not silently written off or counted as a win.

## Reconciliation

Status: fee_pending
New entries blocked: False
Exit checks allowed: True
Accounting final: False

| Coin | Expected | Broker | Difference | Unconfirmed |
| --- | --- | --- | --- | --- |
| AAVEUSD | 0E-9 | 0 | 0E-9 | 0 |
| ADAUSD | 0E-9 | 0 | 0E-9 | 0 |
| ARBUSD | 0E-9 | 0 | 0E-9 | 0 |
| AVAXUSD | 0E-9 | 0 | 0E-9 | 0 |
| BTCUSD | 0E-9 | 0 | 0E-9 | 0 |
| DOTUSD | 0E-9 | 0 | 0E-9 | 0 |
| ETHUSD | 0E-9 | 0 | 0E-9 | 0 |
| FILUSD | 0E-9 | 0 | 0E-9 | 0 |
| HYPEUSD | 0 | 0 | 0 | 0 |
| LINKUSD | 0.050320998 | 0 | -0.050320998 | 0.050320998 |
| LTCUSD | 0E-9 | 0 | 0E-9 | 0 |
| ONDOUSD | 0E-9 | 0 | 0E-9 | 0 |
| PEPEUSD | 43942731.277533041 | 43942731.277533041 | 0E-9 | 0 |
| POLUSD | 0 | 0 | 0 | 0 |
| RENDERUSD | 0E-9 | 0 | 0E-9 | 0 |
| SOLUSD | 0E-9 | 0 | 0E-9 | 0 |
| TRUMPUSD | 0E-9 | 0 | 0E-9 | 0 |
| UNIUSD | 0E-9 | 0 | 0E-9 | 0 |
| XRPUSD | 0E-9 | 0 | 0E-9 | 0 |

PENDING, NOT CONFIRMED: fee-sized shortfall. No fee record invented.
New buys permitted by explicit paper policy; all entry checks still apply.
Guarded software exits remain active. Trade accounting is provisional until broker records reconcile.

Entry scan status: completed_with_data_errors
Next entry scan eligible: 2026-11-13T11:55:43+00:00
Entry scans: at most once every 30 minutes. Software exits: every successful workflow tick, not standing orders.
Full diagnostics: reconciliation.csv and reconciliation.json.

## Discovery watchlist

Last refresh: 2026-11-13T11:25:44+00:00
Source status: partial
Selected: PEPE/USD, AVAX/USD, BTC/USD, ETH/USD, LINK/USD, LTC/USD, SOL/USD, ADA/USD, HYPE/USD, RENDER/USD, ONDO/USD, UNI/USD
Emerging momentum is a screening label, not an undervaluation or profit claim.
News is attention/risk context, not a buy signal. Existing strategy, quote and risk checks still apply.
USD volume is estimated from Coinbase base volume times last price, not broker liquidity.
Details, exclusions, source errors and headline links: watchlist.json and watchlist.csv.
