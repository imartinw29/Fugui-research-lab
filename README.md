# Fugui Research Lab

个人投研实验室——方法、工具、工作流、深度研报，全部在这里。

## 目录结构

```
Fugui-research-lab/
├── fugui-finance-package/     ← 数据引擎 + 估值引擎
│   ├── dfcf_finance/          ← 东方财富API（行情/选股/财报/筹码峰/诊断）
│   └── spring-river-warm/     ← 春江水暖估值引擎
├── lucky-bamboo/              ← 策略技能组
│   ├── scripts/               ← 四灯扫描 v2.9 / quick_scan / fallback_scan
│   ├── references/            ← 投资框架 / 仓位管理 / 筹码峰
│   └── observation-log/       ← 观察日志
├── research/                  ← 🔒 深度研报（私有）
├── course-dev/                ← 🔒 课件开发（私有）
├── docs/                      ← 文档
│   ├── SKILLS-INDEX.md        ← 技能总索引（11 个投研技能 + 联动地图）
│   ├── workflows/             ← 各技能工作流说明
│   ├── methods/               ← 方法论
│   └── notes/                 ← 研究笔记
└── site/                      ← MkDocs 站点（待发布）
```

## 分工

| 模块 | 管什么 | 一句话 |
|------|--------|--------|
| `fugui-finance-package` | "有什么" | 数据获取、估值计算、技术指标 |
| `lucky-bamboo` | "怎么办" | 买卖信号、四灯判定、双参KDJ接力 |
| `research/` | "怎么看" | 叙事/护城河/估值/基本面/技术面五维分析 |
| `course-dev/` | "怎么教" | 一看二拆三封，框架性思维课件 |
| `docs/` | "怎么找" | 技能索引、联动地图、工作流文档 |

## 技能总览

[SKILLS-INDEX.md](docs/SKILLS-INDEX.md) — 11 个投研技能完整索引，含触发词、输入输出、联动地图。

核心技能管道：数据获取 → 行业分析 → 可比估值 → 研报生成 → PPT 组装。

## MKins 预览

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

## 部署

GitHub Pages（GitHub Actions 自动构建）
