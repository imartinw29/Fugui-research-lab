# 东方财富金融数据工具 (dfcf-finance-tool)

> **原项目：** 东方财富妙想 Skills API（https://mkapi2.dfcfs.com）
> **整合优化：** 多版本合并 + 冗余代码精简 + OOP 封装 + 自动路由 + 跨平台兼容
> **使用前提：** 需自行申请东方财富妙想 API Key（MX_APIKEY）

## 做了什么

原始东方财富 API 分散在多个脚本中（Hermes 版、nanobot 版、OpenClaw 版），各版互相不知道对方的存在，接口调用方式不统一，错误处理逻辑重复。

本项目将其整合为：
- **统一 OOP 接口**（`DFCFFinance` 类）
- **自动路由**（一句话 query，自动判断行情/资讯/选股/自选股）
- **跨平台兼容**（Hermes / nanobot / OpenClaw 通用）
- **已知坑文档化**（API 参数名陷阱、`success` 字段判断、沙箱环境密钥注入等）

## 免责声明

- 本代码仅做整合与优化，数据能力完全来自东方财富妙想 API
- 使用本工具需自行申请东方财富 API Key
- 本项目与东方财富无任何关联
