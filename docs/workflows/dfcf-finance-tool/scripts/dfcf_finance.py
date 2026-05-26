#!/usr/bin/env python3
"""
东方财富金融工具 - v2.1 收口版
OOP + 5场景 + 统一响应 + 自动路由 + 跨平台通用
"""

import os
import sys
import json
import requests
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class Scene(Enum):
    """五场景枚举"""
    DATA            = "data"
    NEWS            = "news"
    SCREEN          = "screen"
    WATCHLIST_GET   = "wget"
    WATCHLIST_MGR   = "wmgr"


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
            raise ValueError("MX_APIKEY / EASTMONEY_APIKEY 均未设置，请检查环境变量")
        self.session = requests.Session()
        self.session.headers.update({
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "dfcf-finance-tool/2.1",
        })

    # ── 私有 ────────────────────────────────────────────────────

    def _call(self, url: str, payload: Dict) -> Dict:
        """发送请求，网络/解析失败返回含 error 字段的 dict。"""
        try:
            r = self.session.post(url, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"请求失败: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"响应解析失败: {e}"}

    def _ok(self, raw: Dict) -> bool:
        """判断 API 原始返回是否业务成功（status==0 或 success==True）。"""
        return raw.get("success") is True and raw.get("status", 0) == 0

    def _resp(self, ok: bool, data: Any, msg: str) -> Dict:
        return {
            "success": ok,
            "data": data,
            "message": msg,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # ── 场景方法 ─────────────────────────────────────────────────

    def data(self, query: str) -> Dict:
        """
        金融数据查询：行情、财务数据、个股信息。
        注意：/query 接口使用 toolQuery 参数。
        """
        raw = self._call(self.ENDPOINTS[Scene.DATA], {"toolQuery": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data", {})
        status = inner.get("status", inner.get("code", -1))
        if status != 0:
            return self._resp(False, raw, inner.get("message", "查询失败"))
        return self._resp(True, raw, "查询成功")

    def news(self, query: str) -> Dict:
        """资讯搜索：新闻、公告、研报、政策。"""
        raw = self._call(self.ENDPOINTS[Scene.NEWS], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data", {})
        status = inner.get("status", inner.get("code", -1))
        if status != 0:
            return self._resp(False, raw, inner.get("message", "搜索失败"))
        return self._resp(True, raw, "搜索成功")

    def screen(self, query: str) -> Dict:
        """智能选股：自然语言条件筛选。"""
        raw = self._call(self.ENDPOINTS[Scene.SCREEN], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        inner = raw.get("data") or {}
        status = inner.get("status", raw.get("status", raw.get("code", -1)))
        if status != 0:
            return self._resp(False, raw, raw.get("message") or inner.get("message") or "筛选失败")
        return self._resp(True, raw, "筛选成功")

    def watchlist_get(self) -> Dict:
        """查询自选股列表。"""
        raw = self._call(self.ENDPOINTS[Scene.WATCHLIST_GET], {"query": "查询我的自选股列表"})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        return self._resp(True, raw, "获取成功")

    def watchlist_manage(self, action: str, stock: str) -> Dict:
        """
        管理自选股。
        action: 'add' | 'delete'
        stock:  股票名称或代码
        """
        if action not in ("add", "delete"):
            return self._resp(False, None, "action 必须是 add 或 delete")
        if action == "add":
            query = f"把{stock}添加到我的自选股列表"
        else:
            query = f"把{stock}从我的自选股列表删除"
        raw = self._call(self.ENDPOINTS[Scene.WATCHLIST_MGR], {"query": query})
        if "error" in raw:
            return self._resp(False, None, raw["error"])
        verb = "添加" if action == "add" else "删除"
        return self._resp(True, raw, f"{verb}成功")

    # ── 自动路由 ─────────────────────────────────────────────────

    def route(self, query: str) -> Dict:
        """
        根据 query 内容自动路由到对应场景。
        返回标准化响应（success / data / message / timestamp）。
        """
        q = query.strip()
        q_lc = q.lower()

        # 自选股管理（先判断，避免"添加"被新闻路由抢走）
        if any(w in q for w in ["自选", "watchlist", "我的股票"]):
            if any(w in q for w in ["添加", "加入", "新增"]):
                stock = self._pop_stock(q, ["添加", "加入", "新增"])
                return self.watchlist_manage("add", stock)
            if any(w in q for w in ["删除", "移除"]):
                stock = self._pop_stock(q, ["删除", "移除"])
                return self.watchlist_manage("delete", stock)
            return self.watchlist_get()

        # 资讯搜索
        if any(w in q_lc for w in ["新闻", "公告", "研报", "资讯", "消息", "动态"]):
            return self.news(q)

        # 智能选股
        if any(w in q for w in ["选股", "筛选", "市盈率", "市净率", "涨幅", "换手率", "ROE", "roe"]):
            return self.screen(q)

        # 默认 → 金融数据查询
        return self.data(q)

    @staticmethod
    def _pop_stock(q: str, keywords: list) -> str:
        """从含关键词的句子中提取股票名/代码。"""
        for kw in keywords:
            idx = q.find(kw)
            if idx == -1:
                continue
            rest = q[idx + len(kw):].strip()
            for tail in ["到", "至", "的", "自", "从", "列表", "股票", "自选", "中", "里"]:
                if rest.startswith(tail):
                    rest = rest[len(tail):].strip()
            if rest:
                return rest
        return q


# ── CLI 入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python dfcf_finance.py <自然语言查询>")
        print("示例: python dfcf_finance.py 贵州茅台最新股价")
        print("       python dfcf_finance.py 人工智能板块新闻")
        print("       python dfcf_finance.py 市盈率小于20的银行股")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    try:
        tool = DFCFFinance()
        result = tool.route(query)

        if result["success"]:
            print(f"✅ {result['message']}")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
        else:
            print(f"❌ {result['message']}")
            if result.get("data"):
                print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
