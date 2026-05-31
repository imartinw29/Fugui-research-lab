#!/usr/bin/env python3
"""
东方财富金融工具 v3.0 — 数据层 + 分析层
数据层：行情/财务、资讯搜索、智能选股、自选股管理
分析层：个股诊断、财报解读、宏观研究、行业分析、公司深度
统一 OOP + 自动路由 + 结构化 prompt 输出
"""

import os
import sys
import json
import requests
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class Scene(Enum):
    DATA            = "data"
    NEWS            = "news"
    SCREEN          = "screen"
    WATCHLIST_GET   = "wget"
    WATCHLIST_MGR   = "wmgr"


class AnalysisScene(Enum):
    STOCK_DIAGNOSIS  = "stock_diagnosis"
    FINANCIAL_REPORT = "financial_report"
    MACRO_RESEARCH   = "macro_research"
    INDUSTRY_ANALYSIS = "industry_analysis"
    COMPANY_DEEP      = "company_deep"
    SMART_SCREENING   = "smart_screening"


class DFCFFinance:
    """东方财富妙想 API 统一封装"""

    API_BASE = "https://mkapi2.dfcfs.com/finskillshub/api/claw"

    ENDPOINTS = {
        Scene.DATA:          f"{API_BASE}/query",
        Scene.NEWS:          f"{API_BASE}/news-search",
        Scene.SCREEN:        f"{API_BASE}/stock-screen",
        Scene.WATCHLIST_GET: f"{API_BASE}/self-select/get",
        Scene.WATCHLIST_MGR: f"{API_BASE}/self-select/manage",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MX_APIKEY") or os.getenv("EASTMONEY_APIKEY")
        if not self.api_key:
            raise ValueError("MX_APIKEY / EASTMONEY_APIKEY 均未设置")
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "dfcf-finance-tool/3.0",
        })

    # ── 私有 ────────────────────────────────────────────────────

    def _call(self, url: str, payload: Dict) -> Dict:
        try:
            r = self.session.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"请求失败: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"响应解析失败: {e}"}

    def _resp(self, ok: bool, data: Any, msg: str) -> Dict:
        return {
            "success": ok,
            "data": data,
            "message": msg,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # ── 数据层：5 场景 ──────────────────────────────────────────

    def data(self, query: str) -> Dict:
        raw = self._call(self.ENDPOINTS[Scene.DATA], {"toolQuery": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data", {})
        status = inner.get("status", inner.get("code", -1))
        if status != 0:
            return self._resp(False, raw, inner.get("message", "查询失败"))
        return self._resp(True, raw, "查询成功")

    def news(self, query: str) -> Dict:
        raw = self._call(self.ENDPOINTS[Scene.NEWS], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data", {})
        status = inner.get("status", inner.get("code", -1))
        if status != 0:
            return self._resp(False, raw, inner.get("message", "搜索失败"))
        return self._resp(True, raw, "搜索成功")

    def screen(self, query: str) -> Dict:
        raw = self._call(self.ENDPOINTS[Scene.SCREEN], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data") or {}
        status = inner.get("status", raw.get("status", raw.get("code", -1)))
        if status != 0:
            return self._resp(False, raw, raw.get("message") or inner.get("message") or "筛选失败")
        return self._resp(True, raw, "筛选成功")

    def watchlist_get(self) -> Dict:
        raw = self._call(self.ENDPOINTS[Scene.WATCHLIST_GET], {"query": "查询我的自选股列表"})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        return self._resp(True, raw, "获取成功")

    def watchlist_manage(self, action: str, stock: str) -> Dict:
        if action not in ("add", "delete"):
            return self._resp(False, None, "action 必须是 add 或 delete")
        query = f"把{stock}添加到我的自选股列表" if action == "add" else f"把{stock}从我的自选股列表删除"
        raw = self._call(self.ENDPOINTS[Scene.WATCHLIST_MGR], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        return self._resp(True, raw, f"{'添加' if action == 'add' else '删除'}成功")

    # ── 分析层：6 场景 ──────────────────────────────────────────

    def stock_diagnosis(self, stock: str) -> Dict:
        """
        个股诊断：综合行情+财务+资讯，输出结构化分析框架。
        返回 prompt 模板 + 数据，由 LLM 生成最终分析。
        """
        # 并行获取 3 类数据
        price_data = self.data(f"{stock} 最新价 涨跌幅 总市值 PE(TTM) PB 换手率 量比")
        fin_data  = self.data(f"{stock} 营业总收入 归属净利润 ROE 毛利率 资产负债率 经营现金流")
        news_data = self.news(f"{stock} 最新")

        prompt = f"""你是一位资深A股分析师。请基于以下数据对 **{stock}** 进行综合诊断。

## 行情与估值
{self._extract_table_summary(price_data)}

## 核心财务
{self._extract_table_summary(fin_data)}

## 近期资讯
{self._extract_news_summary(news_data)}

请按以下结构输出诊断报告：

### 1. 估值水位
- 当前 PE/PB 在历史区间的分位
- 与同行业可比公司对比
- 估值结论：低估 / 合理 / 高估

### 2. 财务健康度
- 营收与利润趋势
- ROE 与毛利率变化
- 资产负债结构
- 财务健康度评分（1-10）

### 3. 近期催化剂/风险
- 利好事件
- 风险事件
- 综合研判

### 4. 操作建议
- 短线（1-4周）
- 中线（1-3月）
- 长线（6月+）
"""
        return self._resp(True, {
            "stock": stock,
            "scene": "stock_diagnosis",
            "prompt": prompt,
            "raw": {"price": price_data, "financial": fin_data, "news": news_data},
        }, "个股诊断框架已生成")

    def financial_report(self, stock: str) -> Dict:
        """财报解读：最新财报核心数据 + 同比环比分析。"""
        fin_data  = self.data(f"{stock} 营业总收入 归属净利润 扣非净利润 ROE 毛利率 净利率 资产负债率 经营现金流 每股收益")
        news_data = self.news(f"{stock} 财报 年报 季报")

        prompt = f"""你是一位财务分析专家。请解读 **{stock}** 的最新财报。

## 财务数据
{self._extract_table_summary(fin_data)}

## 相关公告/研报
{self._extract_news_summary(news_data)}

请按以下结构输出：

### 1. 核心指标一览
| 指标 | 本期 | 同比 | 环比 |

### 2. 营收与利润拆解
- 增长驱动因素
- 利润质量评估

### 3. 盈利能力变化
- ROE 杜邦拆解
- 毛利率趋势

### 4. 风险提示
- 资产负债表风险
- 现金流风险

### 5. 财报综合评价
"""
        return self._resp(True, {
            "stock": stock, "scene": "financial_report",
            "prompt": prompt,
            "raw": {"financial": fin_data, "news": news_data},
        }, "财报解读框架已生成")

    def macro_research(self, topic: str) -> Dict:
        """宏观研究：政策/数据/事件驱动分析。"""
        news_data = self.news(topic)

        prompt = f"""你是一位宏观策略分析师。请对以下主题进行深度研究。

## 研究主题
{topic}

## 相关资讯/数据
{self._extract_news_summary(news_data)}

请按以下结构输出：

### 1. 事件/数据核心
- 发生了什么
- 关键数字

### 2. 传导路径
- 对A股行业的影响链条
- 受益/受损方向

### 3. 历史参照
- 类似事件的历史走势
- 本轮差异

### 4. 投资启示
- 短期关注
- 中长期配置思路
"""
        return self._resp(True, {
            "topic": topic, "scene": "macro_research",
            "prompt": prompt,
            "raw": {"news": news_data},
        }, "宏观研究框架已生成")

    def industry_analysis(self, industry: str) -> Dict:
        """行业分析：用 screen 找标的 + news 抓趋势 + data 比估值。"""
        screen_data = self.screen(f"{industry} 行业 市盈率小于100 毛利率大于10%")
        news_data   = self.news(f"{industry} 行业 趋势 政策")

        prompt = f"""你是一位行业研究员。请对 **{industry}** 行业进行深度分析。

## 行业成分股（选股结果）
{self._extract_table_summary(screen_data)}

## 行业资讯
{self._extract_news_summary(news_data)}

请按以下结构输出：

### 1. 行业概览
- 市场规模与增速
- 产业链位置

### 2. 竞争格局
- CR3/CR5 集中度
- 龙头企业对比

### 3. 估值水温
- 行业 PE 中枢
- 当前水位

### 4. 核心标的
- 3-5 只重点关注个股及逻辑
"""
        return self._resp(True, {
            "industry": industry, "scene": "industry_analysis",
            "prompt": prompt,
            "raw": {"screen": screen_data, "news": news_data},
        }, "行业分析框架已生成")

    def company_deep_dive(self, stock: str) -> Dict:
        """公司深度：基本面全景扫描。"""
        price_data = self.data(f"{stock} 最新价 总市值 PE(TTM) PB 换手率 量比 涨跌幅 年初至今涨幅")
        fin_data   = self.data(f"{stock} 营业总收入 归属净利润 ROE 毛利率 净利率 资产负债率 经营现金流 每股收益 每股净资产")
        news_data  = self.news(f"{stock} 深度 研报")

        prompt = f"""你是一位买方研究员。请对 **{stock}** 做一次全景深度分析。

## 行情估值
{self._extract_table_summary(price_data)}

## 财务全景
{self._extract_table_summary(fin_data)}

## 研报观点
{self._extract_news_summary(news_data)}

请按以下结构输出：

### 1. 公司画像
- 主营业务（3句话）
- 行业地位

### 2. 成长性评估
- 近3年收入/利润 CAGR
- 增长驱动力

### 3. 护城河分析
- 品牌/技术/成本/规模/网络效应
- 护城河宽度评分（1-10）

### 4. 估值定价
- PE/PB 横向对比（选3家可比公司）
- DCF/PE 合理区间估算

### 5. 投资结论
- 当前是否值得买入/持有/卖出
- 目标价区间
- 核心风险
"""
        return self._resp(True, {
            "stock": stock, "scene": "company_deep",
            "prompt": prompt,
            "raw": {"price": price_data, "financial": fin_data, "news": news_data},
        }, "公司深度分析框架已生成")

    # ── 辅助方法 ────────────────────────────────────────────────

    @staticmethod
    def _extract_table_summary(result: Dict) -> str:
        """从 API 返回中提取表格数据摘要，失败则返回原始 JSON 摘要。"""
        if not result.get("success"):
            return f"[数据获取失败: {result.get('message', 'unknown')}]"
        raw = result.get("data", {})
        try:
            data_section = raw.get("data", raw)
            tables = data_section.get("data", {}).get("searchDataResultDTO", {}).get("dataTableDTOList", [])
            if not tables:
                tables = data_section.get("dataTableDTOList", [])
            lines = []
            for t in tables[:5]:
                tbl = t.get('table', {})
                if tbl:
                    hdr = tbl.get('headName', [])
                    lines.append(f"  [时间] {' | '.join(str(h) for h in hdr)}")
                    for k, v in tbl.items():
                        if k == 'headName': continue
                        lines.append(f"  {k}: {' | '.join(str(x) for x in v)}")
                else:
                    heads = [h.get('fieldName', '') for h in t.get('headList', [])]
                    lines.append(f"  [列] {' | '.join(heads[:8])}")
                    for row in t.get('dataTableDTORows', [])[:5]:
                        cells = [c.get('fieldValue', '') for c in row.get('dataTableDTOCells', [])]
                        lines.append(f"  {' | '.join(str(c)[:20] for c in cells[:8])}")
            return '\n'.join(lines) if lines else f"[数据为空] raw_keys={list(raw.keys())[:5]}"
        except Exception as e:
            return f"[解析失败: {e}] raw_keys={list(raw.keys())[:5] if isinstance(raw, dict) else 'not_dict'}"

    @staticmethod
    def _extract_news_summary(result: Dict) -> str:
        """从新闻结果中提取标题摘要。"""
        if not result.get("success"):
            return f"[搜索失败: {result.get('message', 'unknown')}]"
        raw = result.get("data", {})
        try:
            items = raw.get("data", {}).get("data", raw.get("data", []))
            if isinstance(items, dict):
                items = items.get("newsList", items.get("items", items.get("list", [])))
            if not isinstance(items, list):
                items = []
            lines = []
            for item in items[:8]:
                if isinstance(item, dict):
                    title = item.get("title", item.get("TITLE", ""))
                    source = item.get("source", item.get("SOURCE", ""))
                    date = item.get("date", item.get("DATE", item.get("publishTime", "")))
                    lines.append(f"- [{source}] {title} ({date})" if source else f"- {title} ({date})")
            return '\n'.join(lines) if lines else f"[无新闻项] type={type(items).__name__} len={len(items) if isinstance(items, list) else 'N/A'}"
        except Exception as e:
            return f"[解析失败: {e}]"

    @staticmethod
    def _extract_screen_summary(result: Dict) -> str:
        """从选股结果中提取标的摘要。"""
        if not result.get("success"):
            return f"[筛选失败: {result.get('message', 'unknown')}]"
        raw = result.get("data", {})
        try:
            stocks = raw.get("data", {}).get("data", raw.get("data", []))
            if isinstance(stocks, dict):
                stocks = stocks.get("stocks", stocks.get("list", []))
            if not isinstance(stocks, list):
                stocks = []
            lines = []
            for s in stocks[:10]:
                if isinstance(s, dict):
                    name = s.get("stockName", s.get("name", s.get("code", "")))
                    code = s.get("stockCode", s.get("code", ""))
                    lines.append(f"- {name}({code})")
            return '\n'.join(lines) if lines else f"[筛选结果为空]"
        except Exception as e:
            return f"[解析失败: {e}]"

    # ── 增强路由 ─────────────────────────────────────────────────

    def route(self, query: str) -> Dict:
        """自动识别意图 → 数据层或分析层。"""
        q = query.strip()

        # ── 分析层路由（优先） ──
        if self._match_analysis(q, AnalysisScene.COMPANY_DEEP):
            stock = self._extract_stock(q)
            return self.company_deep_dive(stock)
        if self._match_analysis(q, AnalysisScene.FINANCIAL_REPORT):
            stock = self._extract_stock(q)
            return self.financial_report(stock)
        if self._match_analysis(q, AnalysisScene.STOCK_DIAGNOSIS):
            stock = self._extract_stock(q)
            return self.stock_diagnosis(stock)
        if self._match_analysis(q, AnalysisScene.MACRO_RESEARCH):
            return self.macro_research(q)
        if self._match_analysis(q, AnalysisScene.INDUSTRY_ANALYSIS):
            industry = self._extract_industry(q)
            return self.industry_analysis(industry)

        # ── 数据层路由 ──
        if any(w in q for w in ["自选", "watchlist", "我的股票"]):
            if any(w in q for w in ["添加", "加入", "新增"]):
                return self.watchlist_manage("add", self._pop_stock(q, ["添加", "加入", "新增"]))
            if any(w in q for w in ["删除", "移除"]):
                return self.watchlist_manage("delete", self._pop_stock(q, ["删除", "移除"]))
            return self.watchlist_get()
        if any(w in q.lower() for w in ["新闻", "公告", "研报", "资讯", "消息", "动态"]):
            return self.news(q)
        if any(w in q for w in ["选股", "筛选", "市盈率", "市净率", "涨幅", "换手率", "ROE", "roe"]):
            return self.screen(q)
        return self.data(q)

    # ── 分析层路由辅助 ──────────────────────────────────────────

    _ANALYSIS_KEYWORDS = {
        AnalysisScene.STOCK_DIAGNOSIS:  ["诊断", "体检", "评估"],
        AnalysisScene.FINANCIAL_REPORT: ["财报", "年报", "季报", "解读财报", "业绩"],
        AnalysisScene.MACRO_RESEARCH:   ["宏观", "政策", "央行", "加息", "降息", "CPI", "PPI", "PMI", "GDP"],
        AnalysisScene.INDUSTRY_ANALYSIS:["行业分析", "行业研究", "赛道", "板块分析"],
        AnalysisScene.COMPANY_DEEP:     ["深度分析", "深度研究", "基本面", "护城河"],
    }

    def _match_analysis(self, q: str, scene: AnalysisScene) -> bool:
        return any(kw in q for kw in self._ANALYSIS_KEYWORDS[scene])

    @staticmethod
    def _extract_stock(q: str) -> str:
        """从 query 中提取股票名/代码，失败返回原 query。"""
        import re
        m = re.search(r'(\d{6})', q)
        if m: return m.group(1)
        # 移除场景关键词后剩下的就是股票名
        for kw in ["诊断", "财报", "解读", "分析", "深度", "体检", "评估", "年报", "季报", "业绩"]:
            q = q.replace(kw, "")
        return q.strip().rstrip("的").strip() or q

    @staticmethod
    def _extract_industry(q: str) -> str:
        """提取行业名。"""
        for kw in ["行业分析", "行业研究", "赛道分析", "板块分析", "行业", "板块"]:
            idx = q.find(kw)
            if idx > 0:
                return q[:idx+len(kw.replace("分析","").replace("研究",""))].strip()
        return q

    @staticmethod
    def _pop_stock(q: str, keywords: list) -> str:
        for kw in keywords:
            idx = q.find(kw)
            if idx == -1: continue
            rest = q[idx + len(kw):].strip()
            for tail in ["到", "至", "的", "自", "从", "列表", "股票", "自选", "中", "里"]:
                if rest.startswith(tail):
                    rest = rest[len(tail):].strip()
            if rest: return rest
        return q


# ── CLI 入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python dfcf_finance.py <自然语言查询>")
        print("数据层: python dfcf_finance.py 佰维存储最新股价")
        print("         python dfcf_finance.py 存储芯片新闻")
        print("         python dfcf_finance.py 市盈率小于30的科技股")
        print("分析层: python dfcf_finance.py 佰维存储诊断")
        print("         python dfcf_finance.py 宁德时代财报解读")
        print("         python dfcf_finance.py 半导体行业分析")
        print("         python dfcf_finance.py 人工智能宏观研究")
        print("         python dfcf_finance.py 澜起科技深度分析")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    try:
        tool = DFCFFinance()
        result = tool.route(query)

        if result["success"]:
            scene = result.get("data", {}).get("scene", "data")
            print(f"✅ [{scene}] {result['message']}")
            # 分析层：输出 prompt 预览
            prompt = result.get("data", {}).get("prompt", "")
            if prompt:
                print(f"\n{'='*50}")
                print(f"📋 分析 Prompt 模板 ({len(prompt)} chars)")
                print(f"{'='*50}")
                print(prompt[:800])
                if len(prompt) > 800:
                    print(f"\n... (省略 {len(prompt)-800} chars)")
        else:
            print(f"❌ {result['message']}")
            if result.get("data"):
                print(json.dumps(result["data"], indent=2, ensure_ascii=False)[:500])
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
