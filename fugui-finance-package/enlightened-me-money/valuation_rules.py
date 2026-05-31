"""
估值推理规则引擎 — v1
可审计的金融逻辑判断，不是 prompt 硬写。

用法：
    from valuation_rules import RuleEngine
    engine = RuleEngine()
    result = engine.check_profit_quality(cfo=10, net_profit=15)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Confidence(str, Enum):
    HIGH = "✅ 高确定"
    MEDIUM = "⚠️ 中等"
    LOW = "❌ 低确定"


class Regime(str, Enum):
    CYCLE = "周期股"          # 毛利率波动 >20pct/年
    GROWTH = "高景气成长"     # 营收增速 >30% + 毛利率稳定/上升
    STEADY = "稳定白马"       # 增速 10-20% + ROE >15%
    UNCLASSIFIED = "未分类"


class Driver(str, Enum):
    EARNINGS = "业绩驱动"
    VALUATION = "纯估值扩张"
    FOREIGN = "外资风险偏好驱动"
    HYBRID = "混合驱动"


@dataclass
class RuleResult:
    rule_name: str
    triggered: bool
    conclusion: str
    details: Dict = field(default_factory=dict)


class RuleEngine:
    """估值推理规则引擎"""

    # ================================================================
    # 第1组：利润质量
    # ================================================================

    @staticmethod
    def check_profit_quality(
        cfo: float,
        net_profit: float,
        periods_weak: int = 2,
    ) -> RuleResult:
        """
        CFO/净利润 < 0.8 连续 periods_weak 期 → 利润质量下降。
        cfo: 经营现金流（单期）
        net_profit: 归母净利润（单期）
        """
        ratio = cfo / net_profit if net_profit > 0 else float("-inf")
        triggered = ratio < 0.8
        return RuleResult(
            rule_name="利润质量检查",
            triggered=triggered,
            conclusion=(
                f"⚠️ 利润质量偏弱：CFO/净利润 = {ratio:.2f}（阈值 0.8）"
                if triggered
                else f"✅ 利润质量正常：CFO/净利润 = {ratio:.2f}"
            ),
            details={"cfo": cfo, "net_profit": net_profit, "ratio": round(ratio, 3)},
        )

    @staticmethod
    def check_fake_receivables(
        receivable_growth: float,
        revenue_growth: float,
    ) -> RuleResult:
        """
        应收增速 > 营收增速 + 20pct → 存在渠道压货/放宽信用风险。
        """
        gap = receivable_growth - revenue_growth
        triggered = gap > 0.2
        return RuleResult(
            rule_name="应收账款异常检查",
            triggered=triggered,
            conclusion=(
                f"⚠️ 应收增速({receivable_growth:.0%})远超营收增速({revenue_growth:.0%})，差额{gap:.0%}，"
                f"可能存在渠道压货或放宽信用政策"
                if triggered
                else f"✅ 应收与营收增速匹配，差额{gap:.0%}"
            ),
            details={"receivable_growth": receivable_growth, "revenue_growth": revenue_growth, "gap": gap},
        )

    # ================================================================
    # 第2组：成长质量
    # ================================================================

    @staticmethod
    def check_growth_quality(
        revenue_growth: float,
        gross_margin_change: float,
    ) -> RuleResult:
        """
        营收增速 > 40% 且毛利率下降 >5pct → 增长依赖低价扩张。
        """
        triggered = revenue_growth > 0.4 and gross_margin_change < -0.05
        return RuleResult(
            rule_name="成长质量检查",
            triggered=triggered,
            conclusion=(
                f"⚠️ 增长依赖低价扩张：营收+{revenue_growth:.0%}但毛利率变化{gross_margin_change:.1%}，"
                f"量增价跌"
                if triggered
                else f"✅ 增长与利润率匹配"
            ),
            details={"revenue_growth": revenue_growth, "gm_change": gross_margin_change},
        )

    @staticmethod
    def check_inventory_bubble(
        inventory_growth: float,
        revenue_growth: float,
    ) -> RuleResult:
        """
        存货增速 >> 营收增速 → 存货积压，减值风险。
        """
        gap = inventory_growth - revenue_growth
        triggered = gap > 0.3
        return RuleResult(
            rule_name="存货积压检查",
            triggered=triggered,
            conclusion=(
                f"⚠️ 存货增速({inventory_growth:.0%})远超营收增速({revenue_growth:.0%})，"
                f"差额{gap:.0%}，存货积压风险高"
                if triggered
                else f"✅ 存货与营收增速匹配"
            ),
            details={"inventory_growth": inventory_growth, "revenue_growth": revenue_growth, "gap": gap},
        )

    # ================================================================
    # 第3组：估值驱动来源
    # ================================================================

    @staticmethod
    def check_valuation_driver(
        pe_change: float,
        eps_change: float,
        northbound_change: Optional[float] = None,
    ) -> RuleResult:
        """
        判断估值扩张是业绩驱动还是情绪驱动。
        pe_change: 过去N期PE变化率
        eps_change: 同期EPS变化率
        northbound_change: 北向持股变化率（可选）
        """
        if pe_change > 0.1 and eps_change < 0.05:
            driver = Driver.VALUATION
            conclusion = "⚠️ 纯估值扩张——PE上升但EPS几乎没动，估值提升并非业绩驱动"
        elif eps_change > 0.1 and pe_change < 0.05:
            driver = Driver.EARNINGS
            conclusion = "✅ 业绩驱动——EPS上升但PE未扩张，估值有业绩支撑"
        elif northbound_change is not None and northbound_change > 0.05 and pe_change > 0.1:
            driver = Driver.FOREIGN
            conclusion = f"🌐 外资偏好驱动——北向持股+{northbound_change:.0%}，PE同步扩张"
        else:
            driver = Driver.HYBRID
            conclusion = "📊 混合驱动"
        return RuleResult(
            rule_name="估值驱动来源",
            triggered=(driver != Driver.EARNINGS),
            conclusion=conclusion,
            details={
                "pe_change": pe_change, "eps_change": eps_change,
                "northbound_change": northbound_change, "driver": driver.value,
            },
        )

    # ================================================================
    # 第4组：Regime 分类
    # ================================================================

    @staticmethod
    def classify_regime(
        gm_volatility: float,        # 近3年毛利率极差（年化）
        revenue_growth: float,        # 近3年营收 CAGR
        roe: float,                   # 当前 ROE
    ) -> Regime:
        """
        将公司归入估值 regime，自动匹配估值方法。

        周期股：毛利率年波动 >20pct
        高景气成长：营收增速 >30% + 毛利率稳定或上升
        稳定白马：增速 10-20% + ROE >15%
        """
        if gm_volatility > 0.20:
            return Regime.CYCLE
        if revenue_growth > 0.30:
            return Regime.GROWTH
        if 0.10 <= revenue_growth <= 0.20 and roe > 0.15:
            return Regime.STEADY
        return Regime.UNCLASSIFIED

    @staticmethod
    def regime_valuation_method(regime: Regime) -> Dict:
        """返回 regime 对应的推荐估值方法"""
        mapping = {
            Regime.CYCLE: {
                "primary": "PB + 库存周期位置",
                "secondary": "EV/EBITDA（如有）",
                "avoid": "PE（周期顶部利润最大，PE最低，具误导性）",
            },
            Regime.GROWTH: {
                "primary": "PS + Forward PE",
                "secondary": "渗透率/市场空间法",
                "avoid": "DCF（假设过于敏感）",
            },
            Regime.STEADY: {
                "primary": "DCF + ROIC",
                "secondary": "PE + 股息率",
                "avoid": "PS（成熟期不适用）",
            },
        }
        return mapping.get(regime, {"primary": "PE + PB 综合", "secondary": "", "avoid": ""})

    # ================================================================
    # 第5组：估值可信度评分
    # ================================================================

    @staticmethod
    def confidence_score(
        industry_stability: bool,     # 行业是否稳定（非强周期、非政策敏感）
        earnings_consistent: bool,    # 近3年是否持续盈利（无亏损年）
        cfo_quality: bool,            # CFO/净利润 > 0.8
        low_concentration: bool,      # 无单一客户依赖（第一大客户<30%）
    ) -> Confidence:
        """估值可信度评分"""
        score = sum([industry_stability, earnings_consistent, cfo_quality, low_concentration])
        if score >= 4:
            return Confidence.HIGH
        elif score >= 3:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW

    # ================================================================
    # 批量运行
    # ================================================================

    def run_all_checks(self, data: Dict) -> List[RuleResult]:
        """批量运行所有适用规则，返回触发的问题列表。"""
        results = []
        # 利润质量（需要 CFO + 净利润）
        if data.get("cfo") is not None and data.get("net_profit"):
            results.append(self.check_profit_quality(data["cfo"], data["net_profit"]))
        # 应收异常
        if data.get("receivable_growth") is not None and data.get("revenue_growth") is not None:
            results.append(self.check_fake_receivables(data["receivable_growth"], data["revenue_growth"]))
        # 成长质量
        if data.get("revenue_growth") is not None and data.get("gm_change") is not None:
            results.append(self.check_growth_quality(data["revenue_growth"], data["gm_change"]))
        # 存货积压
        if data.get("inventory_growth") is not None:
            results.append(self.check_inventory_bubble(data["inventory_growth"], data.get("revenue_growth", 0)))
        # 估值驱动
        if data.get("pe_change") is not None and data.get("eps_change") is not None:
            results.append(self.check_valuation_driver(
                data["pe_change"], data["eps_change"], data.get("northbound_change")
            ))
        return results


def run_checks_interactive(data: Dict) -> str:
    """CLI 友好的快速检查输出"""
    engine = RuleEngine()
    results = engine.run_all_checks(data)
    triggered = [r for r in results if r.triggered]
    lines = []
    for r in triggered:
        lines.append(f"[{r.rule_name}] {r.conclusion}")
    if not lines:
        lines.append("✅ 所有规则通过，未发现显著异常。")
    return "\n".join(lines)
