# 东方财富公开API — 网络连通性备忘

> 2026-06-04 实战验证

## 可用端点

| 端点 | 子域 | 协议 | 用途 |
|------|------|------|------|
| `/api/qt/clist/get` | `push2his.eastmoney.com` | HTTPS ✅ | 全A股列表+排序 |
| `/api/qt/stock/trends2/get` | `push2his.eastmoney.com` | HTTPS ✅ | 单股1分钟分时数据 |
| `/api/qt/stock/kline/get` | `push2his.eastmoney.com` | HTTPS ✅ | 日K/分钟K线 |

## WSL环境连通性

| 调用方式 | push2his (HTTPS) | push2 (HTTP) |
|----------|:---:|:---:|
| `web_extract()` | ✅ 可用 | ❌ |
| `execute_code → web_extract()` | ✅ 可用 | ❌ |
| `terminal → python3 urllib` | ⚠️ 间歇可用 | ❌ |
| `terminal → python3 requests` | ❌ RemoteDisconnected | ❌ |
| `terminal → curl` | ✅ curl HTTPS 可通 | ❌ 000 |

**结论：** 脚本内用 `urllib.request.urlopen`（非 `requests`）。终端脚本不可靠时，fallback 为 `web_extract` + regex 手工解析 JSON。东财 API 返回的 JSON 可能含非法转义字符（如 `*ST` 中的 `*`），用 `json.loads(text, strict=False)` 或 regex 直接提取字段。

## 已知不可达

- `push2.eastmoney.com` — HTTP/HTTPS 均不可达（WSL直连）
- 代理 `10.10.3.2:7890` — 407 认证要求（OpenClash 代理需认证）

## 妙想Skills API vs 公开API

| | 妙想 (mkapi2.dfcfs.com) | 公开 (push2his) |
|---|---|---|
| 需要密钥 | ✅ MX_APIKEY | ❌ |
| 日K数据 | ✅ | ✅ |
| 分钟K线 | ❌ | ✅ |
| 分时数据 | ❌ | ✅ (trends2, 1分钟bar) |
| 选股筛选 | ⚠️ screen() 中文条件解析不稳定 | ❌ (需程序化过滤) |
