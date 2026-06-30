# 投研技能系统

> 开源方法论 · 闭源数据

一个模块化的A股投研工具集，覆盖数据获取、技术回测、估值分析、研报生成。

## 快速开始

```bash
git clone git@github.com:imartinw29/Fugui-research-lab.git
cd Fugui-research-lab
cp config.example.yaml config.yaml   # 填入你的 API Key
mkdir -p private/                     # 创建私人目录（已 gitignore）
```

## 目录结构

```
├── SKILL.md                 # 能力总览（纯方法论）
├── prompt/                  # 各场景系统提示词
├── scripts/                 # Python 工具代码
│   ├── backtest.py          # 回测引擎
│   ├── indicators.py        # 技术指标计算
│   └── report.py            # 报告生成
├── templates/               # 报告模板
├── examples/                # 脱敏示例（000001等中性代码）
├── observations/            # 方法论层面的规律记录
├── experiments/             # 策略实验（BB_KDJ_MACD / Kelly / 等）
├── docs/                    # 详细文档
│   ├── methodology.md
│   └── workflows/           # 各技能工作流
├── fugui-finance-package/   # 东方财富API数据引擎
├── lucky-bamboo/            # 策略脚本（quick_scan / fallback_scan）
├── config.example.yaml      # 配置示例
└── private/ ← gitignore     # 你的自选池/持仓/回测记录
```

## 设计原则

| 层 | 位置 | 包含 | 公开 |
|----|------|------|------|
| **Skill** | SKILL.md / prompt/ | 流程与方法 | ✅ |
| **Code** | scripts/ / fugui-finance-package/ / lucky-bamboo/ | 可执行代码 | ✅ |
| **Template** | templates/ | 报告模板 | ✅ |
| **Example** | examples/ | 脱敏示例（中性代码） | ✅ |
| **Observation** | observations/ | 方法论规律（无股票名） | ✅ |
| **Experiment** | experiments/ | 策略版本与实验 | ✅ |
| **Config** | config.example.yaml | 配置模板 | ✅ |
| **Private** | private/ ← gitignore | 自选池/持仓/回测/配置 | ❌ |
| **Data** | data/ ← gitignore | 缓存数据 | ❌ |
| **Reports** | reports/ ← gitignore | 个人研报 | ❌ |

**Skill 永远描述流程，不描述"我验证过什么"。**
**代码从配置文件加载自选池，不硬编码股票代码。**
**观察日志记录方法论规律，不记录具体结果。**
