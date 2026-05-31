"""
数据清洗与标准化 — v1
将东方财富 API 返回数据映射为统一 Canonical Schema。

用法：
    from clean_financials import normalize_dfcf, compute_derived
    raw = dfcf_tool.data("688525 佰维存储 营收 净利润...")
    fin = normalize_dfcf(raw)
    fin = compute_derived(fin)  # 附加衍生指标
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FinancialPeriod:
    """单个报告期标准化数据"""
    period: str            # "2026Q1" / "2025FY" 等
    revenue: Optional[float] = None         # 亿
    net_profit: Optional[float] = None      # 亿
    net_profit_deducted: Optional[float] = None
    gross_margin: Optional[float] = None    # 百分比(如 42.2 表示 42.2%)
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None
    cfo_per_share: Optional[float] = None   # 元/股
    roic: Optional[float] = None
    inventory: Optional[float] = None       # 亿
    receivables: Optional[float] = None     # 亿
    contracts: Optional[float] = None       # 合同负债(亿)
    capex: Optional[float] = None           # 资本开支(亿)


@dataclass
class MarketData:
    """行情与估值快照"""
    date: str
    price: float          # 元
    mcap: float           # 亿
    float_mcap: float     # 流通市值(亿)
    pe_ttm: Optional[float] = None
    pe_dynamic: Optional[float] = None
    pb: Optional[float] = None
    ps_ttm: Optional[float] = None
    turnover: Optional[float] = None  # 换手率(%)


@dataclass
class LiquidityData:
    """筹码与资金面"""
    northbound_holding: Optional[float] = None    # 北向持股(亿股)
    northbound_pct: Optional[float] = None        # 占流通股%
    northbound_change: Optional[float] = None     # 最近变化(亿股)
    margin_balance: Optional[float] = None        # 融资余额(亿)
    fund_holding: Optional[float] = None          # 基金持仓(亿股)
    fund_holding_pct: Optional[float] = None
    unlock_next_6m: Optional[float] = None        # 未来6月解禁(亿股)


@dataclass
class NormalizedData:
    """标准化后的完整数据集"""
    code: str
    name: str
    market: MarketData = field(default_factory=MarketData)
    financials: List[FinancialPeriod] = field(default_factory=list)
    liquidity: LiquidityData = field(default_factory=LiquidityData)
    industry: Dict[str, Any] = field(default_factory=dict)  # 行业均值
    derived: Dict[str, Any] = field(default_factory=dict)   # 衍生指标


def parse_dfcf_value(raw_val: Any) -> Optional[float]:
    """解析东方财富的混杂格式 → float"""
    if raw_val is None:
        return None
    if isinstance(raw_val, (int, float)):
        return float(raw_val)
    s = str(raw_val).strip().replace(",", "")
    # 处理 "68.14亿元" / "42.22%" / "-5.748元"
    if s.endswith("亿元") or s.endswith("亿"):
        try:
            return float(s.rstrip("亿元亿"))
        except ValueError:
            return None
    if s.endswith("%"):
        try:
            return float(s.rstrip("%"))
        except ValueError:
            return None
    if s.endswith("元"):
        try:
            return float(s.rstrip("元"))
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def compute_derived(financials: List[FinancialPeriod]) -> Dict[str, Any]:
    """从标准化财务数据计算衍生指标"""
    if len(financials) < 2:
        return {}

    latest = financials[0]
    prev_year = None
    for f in financials:
        if f.period == financials[1].period:
            prev_year = f
            break
    if prev_year is None:
        prev_year = financials[-1]

    derived = {}

    # 同比
    if latest.revenue and prev_year.revenue and prev_year.revenue != 0:
        derived["revenue_yoy"] = (latest.revenue - prev_year.revenue) / abs(prev_year.revenue)
    if latest.gross_margin is not None and prev_year.gross_margin is not None:
        derived["gm_delta"] = latest.gross_margin - prev_year.gross_margin

    # 盈利质量
    if latest.net_profit and latest.net_profit > 0:
        # CFO 粗略估算（若有每股CFO + 总股本）
        pass

    # 存货周转率
    if latest.revenue and latest.inventory and latest.inventory > 0:
        derived["inventory_turnover"] = latest.revenue / latest.inventory

    # PEG（若有PE）
    derived["_note"] = "需补充 PE + 行业数据后补完 PEG / percentile / implied_growth"

    return derived


def calc_ttm(financials: List[FinancialPeriod], field: str) -> Optional[float]:
    """从季度累计数据计算 TTM（假设 financials 按时间降序，FY + 季度混合）"""
    # 简化版：取最近四个单季数据求和
    # 完整实现需区分累计值 vs 单季值
    vals = [getattr(f, field) for f in financials[:5] if getattr(f, field) is not None]
    if len(vals) >= 5:
        # 公式：Q1_latest + FY_prev - Q1_prev（累计值 TTM）
        return vals[0] + vals[1] - vals[4]
    return None
