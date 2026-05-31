# 东方财富妙想 API 结构参考

## 基础信息

### API 端点
- **基础 URL**: `https://mkapi2.dfcfs.com/finskillshub`
- **认证方式**: API Key (MX_APIKEY)
- **请求格式**: JSON
- **响应格式**: JSON

### 通用请求头
```http
POST /api/claw/query HTTP/1.1
Host: mkapi2.dfcfs.com
Content-Type: application/json
Authorization: Bearer {MX_APIKEY}
```

## 数据查询 API (`/api/claw/query`)

### 请求结构
```json
{
  "query": "贵州茅台 2025年净利润",
  "sessionId": "optional_session_id",
  "stream": false
}
```

### 响应结构
```json
{
  "success": true,
  "data": {
    "queryId": "query_20260414_115844_01e5b7",
    "summary": "查询结果摘要",
    "tables": [
      {
        "title": "表格标题",
        "columns": [
          {
            "field": "column1",
            "displayName": "列名1",
            "dateMsg": "2026.04.14"
          }
        ],
        "data": [
          {"column1": "value1", "column2": "value2"}
        ]
      }
    ]
  }
}
```

## 股票筛选 API (`/api/claw/stock-screen`)

### 请求结构
```json
{
  "query": "市盈率小于20",
  "limit": 20,
  "offset": 0
}
```

### 响应结构
```json
{
  "success": true,
  "data": {
    "data": {
      "allResults": {
        "result": {
          "columns": [
            {
              "field": "SECURITY_CODE",
              "displayName": "代码",
              "dateMsg": "2026.04.14"
            },
            {
              "field": "SECURITY_NAME",
              "displayName": "名称"
            }
          ],
          "dataList": [
            {
              "SECURITY_CODE": "002773",
              "SECURITY_NAME": "康弘药业",
              "LATEST_PRICE": "27.14"
            }
          ]
        }
      }
    }
  }
}
```

**关键路径**: `result["data"]["data"]["allResults"]["result"]`

## 资讯搜索 API (`/api/claw/news-search`)

### 请求结构
```json
{
  "query": "贵州茅台",
  "limit": 5,
  "offset": 0
}
```

### 响应结构 (预期)
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "title": "新闻标题",
        "content": "新闻内容摘要",
        "source": "来源",
        "time": "2026-04-14 11:58:44",
        "url": "https://..."
      }
    ]
  }
}
```

## 数据字段说明

### 股票数据字段
| 字段名 | 说明 | 示例 |
|--------|------|------|
| `SECURITY_CODE` | 股票代码 | `"002773"` |
| `SECURITY_NAME` | 股票名称 | `"康弘药业"` |
| `LATEST_PRICE` | 最新价 | `"27.14"` |
| `CHANGE_PERCENT` | 涨跌幅 | `"-2.41"` |
| `PE_TTM` | 市盈率(TTM) | `"20.00"` |
| `TOTAL_MARKET_CAP` | 总市值 | `"250.05亿"` |
| `TURNOVER_RATE` | 换手率 | `"3.07"` |

### 表格列元数据
| 字段 | 说明 | 类型 |
|------|------|------|
| `field` | 英文字段名 | string |
| `displayName` | 显示名称(中文) | string |
| `dateMsg` | 日期信息 | string |
| `name` | 备用字段名 | string |
| `key` | 备用键名 | string |

## 错误响应

### 通用错误格式
```json
{
  "success": false,
  "error": {
    "code": "API_ERROR",
    "message": "错误描述",
    "details": {}
  }
}
```

### 常见错误码
| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `AUTH_FAILED` | 认证失败 | 检查 API 密钥 |
| `RATE_LIMIT` | 频率限制 | 降低请求频率 |
| `QUERY_PARSE_ERROR` | 查询解析错误 | 调整查询语句 |
| `DATA_NOT_FOUND` | 数据未找到 | 确认查询条件 |
| `SERVER_ERROR` | 服务器错误 | 稍后重试 |

## 使用限制

### 频率限制
- **默认限制**: 未知（建议保守使用）
- **建议间隔**: 请求间至少 1 秒间隔
- **批量处理**: 避免连续高频请求

### 数据限制
- **股票筛选**: 单次最多返回 100 条
- **数据查询**: 结果数量取决于查询条件
- **历史数据**: 可能有限制时间范围

### 字段限制
- 部分字段可能需要特定权限
- 实时数据有延迟（通常 15-30 秒）
- 部分指标为估算值

## 最佳实践

### 1. 查询优化
```python
# 明确查询条件
query = "贵州茅台 2025年 营业收入"  # ✅ 明确
query = "茅台数据"  # ❌ 模糊

# 使用标准术语
query = "市盈率(TTM)"  # ✅ 标准
query = "PE值"  # ❌ 非标准
```

### 2. 错误处理
```python
try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if not data.get("success"):
        error_msg = data.get("error", {}).get("message", "Unknown error")
        raise Exception(f"API error: {error_msg}")
        
except requests.exceptions.Timeout:
    # 处理超时
except requests.exceptions.RequestException as e:
    # 处理网络错误
```

### 3. 数据解析
```python
def parse_stock_data(response_data):
    """解析股票筛选响应"""
    result = response_data.get("data", {}).get("data", {}).get("allResults", {}).get("result", {})
    
    columns = result.get("columns", [])
    data_list = result.get("dataList", [])
    
    # 构建列映射
    column_map = {}
    for col in columns:
        en_key = col.get("field") or col.get("name") or col.get("key")
        cn_name = col.get("displayName") or col.get("title") or col.get("label") or en_key
        if en_key and cn_name:
            column_map[str(en_key)] = str(cn_name)
    
    return column_map, data_list
```

## 更新记录

### 2026-04-14
- 初始版本，基于实际使用经验
- 包含数据查询、股票筛选 API 结构
- 添加字段说明和最佳实践