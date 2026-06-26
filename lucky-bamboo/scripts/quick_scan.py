#!/usr/bin/env python3
"""lucky-bamboo quick scan v2.8: 四灯 + 筹码峰 + MACD八形态 + 股东户数 + 换手率(市值分档) + PEG + 量价背离

Usage: python quick_scan.py <secid>  (e.g. 1.688008 for 澜起科技)
       secid = market(1=SH, 0=SZ) + '.' + code

v2.8 新增：MACD八形态自动检测
  零轴下二次金叉(小鸭出水/海底捞月) · 零轴上回踩不破(空中缆车/漫步青云)
  佛手向上 · 天鹅展翅 · 空中缆绳 · 海底电缆
  与四灯互补——四灯找买入时机，形态判断趋势结构。
"""

import json, math, os, re, ssl, sys, urllib.request
from datetime import datetime, date, timedelta


# ── DFCF 模块路径 (只设一次) ──────────────────────────────────
_dfcf_path_added = False

def _ensure_dfcf_path():
    global _dfcf_path_added
    if not _dfcf_path_added:
        # repo-relative: ../../fugui-finance-package/dfcf_finance from scripts/
        _repo_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, os.path.join(
            _repo_root, 'fugui-finance-package', 'dfcf_finance'))
        _dfcf_path_added = True


# ── 妙想 API 底层 ─────────────────────────────────────────────

def _dfcf_data(query: str) -> list:
    """统一查询入口 · 防御 data:null 崩溃"""
    _ensure_dfcf_path()
    from dfcf_finance import DFCFFinance
    tool = DFCFFinance()
    r = tool.data(query)
    inner = (r.get('data') or {}).get('data') or {}
    inner = (inner.get('data') or {})
    return (inner.get('searchDataResultDTO') or {}).get('dataTableDTOList', [])


# ── 数据拉取 (妙想主力 → push2his 降级) ──────────────────────

def _try_fetch_miaoxiang(secid: str) -> tuple | None:
    """妙想五合一套餐 + 流通市值 → (name, data)

    返回格式与 fetch_kline_push2his 一致:
      [{date, open, high, low, close, turnover, cap}, ...]
    失败返回 None, 调用方自动降级 push2his.
    """
    code = secid.split('.')[-1]

    # 日期范围: 往前推 90 天 (覆盖 BOLL+MACD+KDJ 热身)
    end = date.today()
    start = end - timedelta(days=90)

    try:
        # ── 调用1: 五合一套餐 (OHLC + 换手率) ──
        tables = _dfcf_data(
            f'{code} 收盘价 最高价 最低价 开盘价 换手率 '
            f'{start.strftime("%Y-%m-%d")}至{end.strftime("%Y-%m-%d")}'
        )
        if not tables:
            return None
        tbl = tables[0].get('table', {})
        head = tbl.get('headName', [])
        if not head or len(head) < 25:
            return None

        # 字段码 → 列名
        FIELD_MAP = {'326269': 'open', '325898': 'close',
                     '326339': 'high', '326386': 'low',
                     '326699': 'turnover'}

        # 防御: 次新股/边缘票可能返回 f-code 快照而非 3xxxxx 时间序列
        actual_keys = set(k for k in tbl if k != 'headName')
        if not (actual_keys & set(FIELD_MAP.keys())):
            # 五合一套餐格式不符 → 分拆单独查询 (v2.7 fallback)
            return _try_fetch_miaoxiang_split(secid, start, end)

        # 清洗: 去后缀 → float/str, 翻转为时间升序
        records = []
        for i in range(len(head)):
            d = head[i].replace('(日)', '') if isinstance(head[i], str) else str(head[i])
            row = {'date': d}
            for fk, col in FIELD_MAP.items():
                raw = tbl.get(fk, [])
                if isinstance(raw, list) and i < len(raw):
                    val_str = str(raw[i])
                    val = float(val_str.replace('元', '').replace('%', '').replace(',', ''))
                    row[col] = val
                else:
                    row[col] = None
            records.append(row)

        if not records or not records[0].get('close'):
            return None

        records.reverse()  # 妙想返回最新在前 → 翻转为时间顺序

        # ── 调用2: 流通市值 ──
        cap = None
        try:
            tables2 = _dfcf_data(f'{code} 流通市值')
            if tables2:
                tbl2 = tables2[0].get('table', {})
                for k, v in tbl2.items():
                    if k == 'headName':
                        continue
                    if isinstance(v, list) and len(v) > 0 and '亿' in str(v[0]):
                        cap = float(str(v[0]).replace('亿元', '').replace('亿', '').replace(',', ''))
                        break
        except Exception:
            pass

        # 注入 cap (只有最后一根有值, 前面的为 None)
        for r in records:
            r['cap'] = None
        if cap is not None:
            records[-1]['cap'] = cap

        # 从 secid 推断名字 (妙想没有直接返回)
        name = code

        return name, records

    except Exception as e:
        print(f"  ⚠️ 妙想五合一套餐失败, 降级 push2his: {e}", file=sys.stderr)
        return None


def _try_fetch_miaoxiang_split(secid: str, start: date, end: date) -> tuple | None:
    """五合一套餐格式不符时的分拆降级 (v2.7)

    边缘票 (次新股/冷门股) 的五合一返回 f-code 快照而非标准 3xxxxx 时间序列.
    分拆为单独查询: 收盘+换手可拉时间序列, 最高/最低/开盘仅单点快照不可用.
    → 用 close±2% 估算高/低价 (KDJ 精度降级), open=close.

    返回格式与主函数一致, 失败返回 None → push2his 最终降级.
    """
    code = secid.split('.')[-1]
    date_range = f'{start.strftime("%Y-%m-%d")}至{end.strftime("%Y-%m-%d")}'

    try:
        # ── 收盘价 (已验证可返回标准 325898 时间序列) ──
        tables = _dfcf_data(f'{code} 收盘价 {date_range}')
        if not tables:
            return None
        tbl = tables[0].get('table', {})
        head = tbl.get('headName', [])
        if not head or len(head) < 25:
            return None
        # 找标准字段码 (325898) 或任意非空字段
        close_key = None
        for k in tbl:
            if k == 'headName':
                continue
            if k == '325898' or (isinstance(tbl[k], list) and len(tbl[k]) >= 25):
                close_key = k
                break
        if not close_key:
            return None

        closes_raw = tbl[close_key]
        n = len(closes_raw)

        # ── 换手率 (可能返回 100000000006291 等变体字段码) ──
        turnovers_raw = None
        try:
            tables_t = _dfcf_data(f'{code} 换手率 {date_range}')
            if tables_t:
                tbl_t = tables_t[0].get('table', {})
                for k in tbl_t:
                    if k != 'headName' and isinstance(tbl_t[k], list) and len(tbl_t[k]) >= 20:
                        turnovers_raw = tbl_t[k]
                        break
        except Exception:
            pass

        # ── 流通市值 ──
        cap = None
        try:
            tables_c = _dfcf_data(f'{code} 流通市值')
            if tables_c:
                tbl_c = tables_c[0].get('table', {})
                for k, v in tbl_c.items():
                    if k == 'headName':
                        continue
                    if isinstance(v, list) and len(v) > 0 and '亿' in str(v[0]):
                        cap = float(str(v[0]).replace('亿元', '').replace('亿', '').replace(',', ''))
                        break
        except Exception:
            pass

        # ── 组装数据: 收盘价 + close±2%估算高/低 + open=close ──
        records = []
        for i in range(n):
            d = head[i].replace('(日)', '') if isinstance(head[i], str) else str(head[i])
            close_val = float(str(closes_raw[i]).replace('元', '').replace(',', ''))
            # KDJ 估算: 高/低价用收盘价 ±2% (与 fallback_scan.py 一致)
            est_high = close_val * 1.02
            est_low = close_val * 0.98
            turnover_val = None
            if turnovers_raw and i < len(turnovers_raw):
                try:
                    turnover_val = float(str(turnovers_raw[i]).replace('%', '').replace(',', ''))
                except (ValueError, TypeError):
                    pass
            records.append({
                'date': d,
                'open': close_val,   # 开盘价用收盘价替代
                'close': close_val,
                'high': est_high,
                'low': est_low,
                'turnover': turnover_val,
                'cap': None,
            })

        records.reverse()  # 妙想最新在前 → 时间升序

        if cap is not None:
            records[-1]['cap'] = cap

        print(f"  ⚠️ 五合一套餐格式不符, 分拆查询 (close±2% 估算 KDJ)", file=sys.stderr)
        return code, records

    except Exception as e:
        print(f"  ⚠️ 分拆查询失败: {e}", file=sys.stderr)
        return None


def fetch_kline_push2his(secid: str) -> tuple:
    """push2his 日K线 (妙想不可用时的降级方案)"""
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={secid}"
        f"&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f61,f21"
        f"&klt=101&fqt=0&end={datetime.now().strftime('%Y%m%d')}&lmt=60"
    )
    with urllib.request.urlopen(url, timeout=10, context=ssl._create_unverified_context()) as resp:
        raw = json.loads(resp.read())
    if raw.get("rc") != 0 or not raw.get("data") or not raw["data"].get("klines"):
        raise RuntimeError(f"push2his API error: {raw.get('rc')}")
    name = raw["data"]["name"]
    klines = raw["data"]["klines"]
    data = []
    for line in klines:
        parts = line.split(",")
        data.append({
            "date": parts[0],
            "open": float(parts[1]),
            "close": float(parts[2]),
            "high": float(parts[3]),
            "low": float(parts[4]),
            "turnover": float(parts[7]) if len(parts) > 7 and parts[7] != '-' else None,
            "cap": float(parts[8]) if len(parts) > 8 and parts[8] != '-' else None,
        })
    return name, data


def fetch_kline(secid: str) -> tuple:
    """主数据拉取: 妙想优先 → push2his 降级"""
    result = _try_fetch_miaoxiang(secid)
    if result is not None:
        return result
    print(f"  🔄 妙想不可用, 降级 push2his ...", file=sys.stderr)
    return fetch_kline_push2his(secid)


# ── 技术指标 ──────────────────────────────────────────────────

def calc_boll(closes, period=20, sigma=2):
    window = closes[-period:]
    ma = sum(window) / period
    std = math.sqrt(sum((c - ma) ** 2 for c in window) / period)
    return ma + sigma * std, ma, ma - sigma * std


def calc_kdj(data, period=14, warmup_bars=20):
    """KDJ · 前 warmup_bars 根暖初始值"""
    if len(data) <= warmup_bars + period:
        k_prev = d_prev = 50.0
        start = period
    else:
        k_run = d_run = 50.0
        for i in range(period, warmup_bars):
            window = data[i - period + 1 : i + 1]
            ll = min(d["low"] for d in window)
            hh = max(d["high"] for d in window)
            rsv = (data[i]["close"] - ll) / (hh - ll) * 100 if hh != ll else 50
            k_run = 2 / 3 * k_run + 1 / 3 * rsv
            d_run = 2 / 3 * d_run + 1 / 3 * k_run
        k_prev, d_prev = k_run, d_run
        start = warmup_bars

    k_vals, d_vals = [], []
    for i in range(start, len(data)):
        window = data[i - period + 1 : i + 1]
        ll = min(d["low"] for d in window)
        hh = max(d["high"] for d in window)
        rsv = (data[i]["close"] - ll) / (hh - ll) * 100 if hh != ll else 50
        k_new = 2 / 3 * k_prev + 1 / 3 * rsv
        d_new = 2 / 3 * d_prev + 1 / 3 * k_new
        k_vals.append(k_new); d_vals.append(d_new)
        k_prev, d_prev = k_new, d_new
    k, d = k_vals[-1], d_vals[-1]
    return k, d, 3 * k - 2 * d


def calc_macd(closes, fast=12, slow=26, signal=9, return_full=False):
    ema_f = closes[0]; ema_s = closes[0]
    dif_vals = []
    for c in closes:
        ema_f = c * 2 / (fast + 1) + ema_f * (1 - 2 / (fast + 1))
        ema_s = c * 2 / (slow + 1) + ema_s * (1 - 2 / (slow + 1))
        dif_vals.append(ema_f - ema_s)
    dea = dif_vals[0]
    dea_vals = []
    for d in dif_vals:
        dea = d * 2 / (signal + 1) + dea * (1 - 2 / (signal + 1))
        dea_vals.append(dea)
    macd_vals = [2 * (d - de) for d, de in zip(dif_vals, dea_vals)]
    if return_full:
        return dif_vals, dea_vals, macd_vals
    return dif_vals[-1], dea_vals[-1], macd_vals[-1], macd_vals[-2]


def detect_macd_patterns(dif, dea, bars):
    """Detect MACD 8-pattern framework (v2.8). Returns list of matched pattern names."""
    patterns = []
    n = len(dif)
    if n < 40:
        return patterns

    # ── 零轴下二次金叉：小鸭出水 / 海底捞月 ──
    gc_below, dc_below = [], []
    for i in range(1, n):
        if dif[i] < 0 and dea[i] < 0:
            if dif[i-1] <= dea[i-1] and dif[i] > dea[i]:
                gc_below.append(i)
            elif dif[i-1] >= dea[i-1] and dif[i] < dea[i]:
                dc_below.append(i)
    if len(gc_below) >= 2:
        last_gc = gc_below[-1]
        if last_gc >= n - 15:
            recent_bars = bars[last_gc:]
            if any(b > 0 for b in recent_bars[-3:]):
                patterns.append('小鸭出水(零轴下二次金叉)')
            elif dc_below and gc_below[-2] < dc_below[-1]:
                patterns.append('海底捞月(零轴下二次金叉)')

    # ── 零轴上回踩不破：空中缆车 / 漫步青云 ──
    for i in range(10, n):
        if dif[i] > 0 and dea[i] > 0:
            if dif[i-1] >= dea[i-1] and dif[i] < dea[i]:
                min_dif_after = min(dif[i:])
                if min_dif_after > 0:
                    for j in range(i+1, n):
                        if dif[j-1] <= dea[j-1] and dif[j] > dea[j]:
                            if j >= n - 10:
                                patterns.append('空中缆车(零轴上回踩不破)')
                            break
                    else:
                        if dif[-1] > dea[-1] * 0.8:
                            patterns.append('漫步青云(零轴上回踩不破)')
                break

    # ── 佛手向上：零轴上金叉→回调未死叉→抬头 ──
    for i in range(5, n-3):
        if dif[i] > 0 and dea[i] > 0:
            if dif[i-1] <= dea[i-1] and dif[i] > dea[i]:
                recent_dif = dif[-5:]
                recent_dea = dea[-5:]
                if all(d > e for d, e in zip(recent_dif, recent_dea)):
                    min_ratio = min(d/e for d, e in zip(recent_dif, recent_dea))
                    if min_ratio < 1.05 and bars[-1] > bars[-3]:
                        patterns.append('佛手向上(零轴上金叉回调不破)')
                break
            break

    # ── 天鹅展翅：零轴下金叉→回调未死叉→抬头 ──
    for i in range(5, n-3):
        if dif[i] < 0 and dea[i] < 0:
            if dif[i-1] <= dea[i-1] and dif[i] > dea[i]:
                recent_dif = dif[-5:]
                recent_dea = dea[-5:]
                if all(d > e for d, e in zip(recent_dif, recent_dea)):
                    min_ratio = min(d/e for d, e in zip(recent_dif, recent_dea))
                    if min_ratio < 1.08 and bars[-1] > bars[-3]:
                        patterns.append('天鹅展翅(零轴下金叉回调不破)')
                break
            break

    # ── 空中缆绳：零轴下金叉→上穿零轴→粘合→再抬头 ──
    for i in range(5, n-10):
        if dif[i] < 0 and dif[i-1] <= dea[i-1] and dif[i] > dea[i]:
            for j in range(i+5, n-5):
                if dif[j] > 0 and dea[j] > 0:
                    sticky = False
                    for k in range(j, n-3):
                        gap = abs(dif[k] - dea[k]) / max(abs(dea[k]), 0.01)
                        if gap < 0.15:
                            sticky = True
                    if sticky and dif[-1] > dea[-1] and bars[-1] > bars[-2]:
                        patterns.append('空中缆绳(穿零轴粘合再抬头)')
                    break
            break

    # ── 海底电缆：零轴下长期粘合→金叉 ──
    recent20_dif = dif[-20:]
    recent20_dea = dea[-20:]
    if all(d < 0 for d in recent20_dif):
        max_gap = max(abs(d - e) / max(abs(e), 0.01) for d, e in zip(recent20_dif, recent20_dea))
        if max_gap < 0.2 and dif[-1] > dea[-1]:
            patterns.append('海底电缆(零轴下粘合金叉)')

    return patterns


# ── 妙想基本面查询 ────────────────────────────────────────────

def fetch_shareholder_count(code: str) -> dict | None:
    """股东户数变动 (季频)"""
    try:
        tables = _dfcf_data(f'{code} 股东户数')
        if not tables:
            return None
        tbl = tables[0].get('table', {})
        dates = sorted([k for k in tbl.keys() if k != 'headName'], reverse=True)
        if len(dates) < 2:
            return None

        def _parse_val(key):
            v = tbl[key]
            if isinstance(v, list) and len(v) > 0:
                v = v[0]
            return float(re.sub(r'[户人,]', '', str(v)))

        latest, prev = _parse_val(dates[0]), _parse_val(dates[1])
        change_pct = (latest - prev) / prev * 100

        consecutive = 1
        direction = '集中' if change_pct < 0 else '分散'
        for i in range(1, min(len(dates)-1, 5)):
            curr, next_v = _parse_val(dates[i]), _parse_val(dates[i+1])
            curr_change = (curr - next_v) / next_v * 100
            curr_dir = '集中' if curr_change < 0 else '分散'
            if curr_dir == direction:
                consecutive += 1
            else:
                break

        return {
            'latest': latest, 'prev': prev,
            'change_pct': change_pct,
            'trend': direction, 'consecutive_q': consecutive,
        }
    except Exception as e:
        print(f"  ⚠️ 股东数据获取失败: {e}", file=sys.stderr)
        return None


def fetch_chip(code: str) -> dict | None:
    """筹码峰数据"""
    try:
        tables = _dfcf_data(f'{code} 筹码分布 获利盘比例')
        chip = {}
        for t in tables:
            tbl = t.get('table', {})
            if not tbl:
                continue
            for k, v in tbl.items():
                if k == 'headName':
                    continue
                val = v[0] if isinstance(v, list) and len(v) > 0 else v
                try:
                    chip[k] = float(re.sub(r'[%元,]', '', str(val)))
                except (ValueError, TypeError):
                    pass
        result = {
            'avg_cost': chip.get('010000_CMPJCB'),
            'profit_pct': chip.get('010000_HLP'),
            'conc_70': chip.get('010000_CMFB_461_JZD70'),
            'conc_90': chip.get('010000_CMFB_461_JZD90'),
        }
        # 数据为空时打 stderr
        if result['avg_cost'] is None and result['profit_pct'] is None:
            print(f"  ⚠️ 筹码数据解析为空 (query成功但无有效字段)", file=sys.stderr)
        return result
    except Exception as e:
        print(f"  ⚠️ 筹码数据获取失败: {e}", file=sys.stderr)
        return None


def fetch_peg(code: str) -> dict | None:
    """PEG: PE(TTM) + 净利润同比增长率"""
    try:
        tables = _dfcf_data(f'{code} 市盈率 TTM')
        pe = None
        for t in tables:
            tbl = t.get('table', {})
            for k, v in tbl.items():
                if k == 'headName':
                    continue
                val = v[0] if isinstance(v, list) and len(v) > 0 else v
                if '倍' in str(val) and '港' not in k and '.HK' not in k:
                    pe = float(re.sub(r'[倍]', '', str(val)))
                    break

        try:
            tables = _dfcf_data(f'{code} 净利润同比增长率')
        except Exception:
            tables = []
        growth = None
        for t in tables:
            tbl = t.get('table', {})
            for k, v in tbl.items():
                if k == 'headName':
                    continue
                val = v[0] if isinstance(v, list) and len(v) > 0 else v
                if '%' in str(val):
                    growth = float(str(val).replace('%', ''))
                    break
            if growth is not None:
                break

        if pe and growth is not None:
            peg = pe / growth if growth > 0 else None
            return {'pe': pe, 'growth': growth, 'peg': peg}
        if pe is None:
            print(f"  ⚠️ PEG: PE(TTM)数据缺失", file=sys.stderr)
        elif growth is None:
            print(f"  ⚠️ PEG: 净利增速数据缺失", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ⚠️ PEG数据获取失败: {e}", file=sys.stderr)
        return None


# ── 换手率阈值 (按流通市值分档) ──────────────────────────────

def _turnover_thresholds(cap: float | None) -> dict:
    if cap is None:
        return {'lock': 1.0, 'churn': 10.0, 'anomaly_mult': 3.0}
    if cap < 50:
        return {'lock': 1.5, 'churn': 8.0,  'anomaly_mult': 2.5}
    if cap < 200:
        return {'lock': 1.0, 'churn': 10.0, 'anomaly_mult': 3.0}
    if cap < 500:
        return {'lock': 0.8, 'churn': 12.0, 'anomaly_mult': 3.5}
    return {'lock': 0.5, 'churn': 15.0, 'anomaly_mult': 4.0}


# ── 主扫描 ────────────────────────────────────────────────────

def scan(secid: str):
    name, data = fetch_kline(secid)

    assert len(data) >= 25, (
        f"Need at least 25 bars for KDJ+MACD warmup, got {len(data)}. "
        f"Try a stock with more trading history."
    )

    closes = [d["close"] for d in data]
    today = data[-1]

    upper, mid, lower = calc_boll(closes)
    k, d, j = calc_kdj(data)
    dif_arr, dea_arr, macd_arr = calc_macd(closes, return_full=True)
    dif, dea, macd_bar = dif_arr[-1], dea_arr[-1], macd_arr[-1]
    macd_prev = macd_arr[-2] if len(macd_arr) >= 2 else macd_bar

    bb_pos = (today["close"] - lower) / (upper - lower) * 100 if upper != lower else 50

    # 数据时效性
    bar_date = datetime.strptime(today["date"], "%Y-%m-%d").date()
    today_date = date.today()
    stale_tag = ""
    if bar_date < today_date:
        stale_tag = f"  [数据滞后: {bar_date}, 非今日实时]"
    elif datetime.now().hour < 15:
        stale_tag = "  [盘中数据, 非收盘价]"

    cap = today.get('cap')
    code = secid.split('.')[-1]
    chip = fetch_chip(code)
    sh = fetch_shareholder_count(code)
    peg_data = fetch_peg(code)

    c1 = today["close"] <= mid
    c2 = k < 30
    c3 = j < 20
    c4 = macd_bar > macd_prev and macd_bar < 0
    passed = sum([c1, c2, c3, c4])

    print(f"{'='*60}")
    cap_str = f"  流通市值: {cap:.0f}亿" if cap else ""
    print(f"  {name}  {secid}  |  {today['date']}  收盘: {today['close']:.2f}{stale_tag}{cap_str}")
    print(f"{'='*60}")
    print(f"  BOLL(20,2): 上={upper:.2f} 中={mid:.2f} 下={lower:.2f}  位置:{bb_pos:.0f}%")
    print(f"  KDJ(14,3):  K={k:.1f}  D={d:.1f}  J={j:.1f}")
    print(f"  MACD(12,26,9): DIF={dif:.2f} DEA={dea:.2f} 柱={macd_bar:.3f}  {'金叉' if dif>dea else '死叉'}")

    macd_patterns = detect_macd_patterns(dif_arr, dea_arr, macd_arr)
    if macd_patterns:
        print(f"  {'─'*50}")
        for pat in macd_patterns:
            print(f"  🔍 MACD形态: {pat}")

    if chip and chip['avg_cost']:
        print(f"  {'─'*50}")
        print(f"  📊 筹码峰: 均价={chip['avg_cost']:.2f}  获利={chip['profit_pct']:.1f}%  "
              f"70%集中={chip['conc_70']:.1f}%  90%集中={chip['conc_90']:.1f}%")
        if today['close'] < chip['avg_cost']:
            disc = (1 - today['close'] / chip['avg_cost']) * 100
            print(f"     💰 当前价在均价之下 {disc:.1f}% —— 筹码低位，安全边际好")
        else:
            prem = (today['close'] / chip['avg_cost'] - 1) * 100
            print(f"     ⚠️  当前价在均价之上 {prem:.1f}% —— 获利盘有兑现压力")

    if sh:
        print(f"  {'─'*50}")
        human_latest = f"{sh['latest']/10000:.1f}万" if sh['latest'] > 10000 else f"{sh['latest']:.0f}"
        arrow = '↓' if sh['change_pct'] < 0 else '↑'
        print(f"  👥 股东户数: {human_latest}  环比{arrow}{abs(sh['change_pct']):.1f}%")
        if sh['consecutive_q'] >= 2:
            print(f"     📉 连续{sh['consecutive_q']}个季度{sh['trend']} —— 筹码在持续集中")
            if sh['trend'] == '集中' and sh['change_pct'] < -5:
                print(f"     🟢 股东户数持续缩减>5%：控盘迹象，筹码锁定度高")
        elif sh['change_pct'] > 20:
            print(f"     🔴 股东户数暴增>20%：筹码快速分散，散户化风险")
        elif sh['change_pct'] > 10:
            print(f"     🟡 股东户数增加>10%：筹码在扩散，关注后续季度")

    # 换手率 + 量价背离
    th = _turnover_thresholds(cap)
    cap_tier = ("小盘" if cap and cap < 50 else
                "中盘" if cap and cap < 200 else
                "大盘" if cap and cap < 500 else
                "超大" if cap else "?")
    turnovers = [d['turnover'] for d in data if d.get('turnover') is not None]
    if turnovers:
        t5 = sum(turnovers[-5:]) / min(5, len(turnovers))
        t20 = sum(turnovers[-20:]) / min(20, len(turnovers))
        t_today = turnovers[-1]
        print(f"  {'─'*50}")
        print(f"  🔄 换手率 [{cap_tier}]: 今日={t_today:.2f}%  5日均={t5:.2f}%  20日均={t20:.2f}%")

        if t20 < th['lock']:
            print(f"     🔒 20日均换手<{th['lock']}% —— 筹码高度锁定 ({cap_tier}控盘特征)")
        elif t20 < th['lock'] * 2:
            print(f"     🟡 20日均换手{th['lock']}-{th['lock']*2}% —— 筹码偏紧，但不到极端控盘")

        if len(data) >= 2:
            prev_close = data[-2]['close']
            price_delta_pct = abs(today['close'] / prev_close - 1)
            if t_today > t20 * 2 and price_delta_pct < 0.005:
                print(f"     ⚠️  高换手({t_today/t20:.1f}×均线) + 价格微动({price_delta_pct*100:.2f}%)"
                      f" —— 疑似对倒或换手，量价背离")

        if t_today > t20 * th['anomaly_mult'] and t_today > 3:
            print(f"     ⚡ 今日换手率飙升 ({t_today/t20:.1f}×均线) —— 异动！查是否有对应消息")

        if t_today > th['churn']:
            print(f"     🔴 今日换手>{th['churn']}%：筹码松动或游资进出，不适合中线策略")

    # PEG
    if peg_data and peg_data.get('pe'):
        pe = peg_data['pe']
        growth = peg_data['growth']
        peg = peg_data.get('peg')
        print(f"  {'─'*50}")
        peg_str = f"{peg:.2f}" if peg is not None else "N/A"
        if growth is not None and growth < 0:
            peg_icon, peg_judge = '🔴', f'净利负增长({growth:.1f}%), PEG不适用 -- 基本面恶化'
        elif peg is None:
            peg_icon, peg_judge = '🟡', f'增速异常, PEG不可算 (PE={pe:.1f}x, growth={growth:.1f}%)'
        elif peg < 1:
            peg_icon, peg_judge = '🟢', f'高增速完全覆盖高PE, 估值可接受 (PEG={peg_str})'
        elif peg < 1.5:
            peg_icon, peg_judge = '🟡', f'估值略高但逻辑自洽, 需其他灯强确认 (PEG={peg_str})'
        elif peg < 2:
            peg_icon, peg_judge = '🟠', f'偏贵, 故事跑在业绩前面, 谨慎 (PEG={peg_str})'
        else:
            peg_icon, peg_judge = '🔴', f'故事溢价过高, 估值灯亮红 (PEG={peg_str})'
        print(f"  {peg_icon} PEG: PE(TTM)={pe:.1f}x  净利增速={growth:.1f}%  PEG={peg_str}")
        print(f"     {peg_judge}")

    print(f"  {'─'*50}")
    print(f"  ① 收盘≤中轨 ({today['close']:.2f}≤{mid:.2f})  {'✅' if c1 else '❌'}")
    print(f"  ② K<30        ({k:.1f}<30)        {'✅' if c2 else '❌'}")
    print(f"  ③ J<20        ({j:.1f}<20)        {'✅' if c3 else '❌'}")
    # ④: MACD 绿柱收窄 (仅绿柱适用, 红柱不适用)
    hint = " (红柱不适用)" if macd_bar >= 0 else ""
    print(f"  ④ MACD绿柱收窄 ({macd_bar:.3f}>{macd_prev:.3f})  {'✅' if c4 else '❌'}{hint}")
    print(f"  {'─'*50}")

    if passed == 4:
        print(f"  🟢 四灯全亮！买入信号")
        if chip and chip['avg_cost'] and today['close'] < chip['avg_cost']:
            print(f"  🟢 筹码低位确认 —— 双重共振")
        if sh and sh['change_pct'] < -5:
            print(f"  🟢 股东户数持续缩减 —— 筹码集中加成")
    else:
        print(f"  🔴 不满足 ({passed}/4)")

    print()
    return passed == 4


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_scan.py <secid>  (e.g. 1.688008)")
        sys.exit(1)
    try:
        scan(sys.argv[1])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
