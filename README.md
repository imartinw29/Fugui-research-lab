# Fugui Research Lab

A personal research lab for methods, workflows, and durable thinking.

## What's in this repo

```
Fugui-research-lab/
├── fugui-finance-package/     ← 数据引擎 + 估值引擎
│   ├── dfcf_finance/          ← 东方财富API（行情/选股/财报/筹码峰）
│   └── spring-river-warm/     ← 春江水暖估值引擎
├── lucky-bamboo/              ← 策略技能组
│   ├── scripts/               ← 四灯扫描/回测/尾盘选股
│   └── references/            ← 投资框架/仓位管理/筹码峰
└── docs/                      ← 文档站
```

**分工：** `fugui-finance-package` 管"有什么"（数据获取、估值计算），`lucky-bamboo` 管"怎么办"（买卖信号、仓位管理、止损纪律）。一个提供原材料，一个提供决策框架。

## Local preview

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

## Deploy

This repo is configured for GitHub Pages via GitHub Actions.
