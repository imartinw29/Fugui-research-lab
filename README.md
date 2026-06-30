# 投研技能系统

> 一套模块化的A股投研工具集。覆盖数据获取、技术回测、估值分析、研报生成。
> 
> Skill 描述流程，不描述验证结果。代码从配置加载参数，不硬编码标的。观察日志记录方法论规律，不记录具体数据。

## 快速开始

```bash
git clone git@github.com:imartinw29/Fugui-research-lab.git
cd Fugui-research-lab

# 1. 复制并填写配置
cp config.example.yaml config.yaml

# 2. 创建私人目录（不被Git跟踪）
mkdir -p private/
cp private/watchlist.example.yaml private/watchlist.yaml
# 编辑 private/watchlist.yaml，填入自选标的
# 编辑 config.yaml，填入 API Key

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行回测
python lucky-bamboo/scripts/backtest_bb_kdj_macd.py
```

## 目录结构

```
├── SKILL.md                 # 能力总览
├── prompt/                  # 各场景系统提示词
│   ├── valuation.md         # 估值分析框架
│   ├── report.md            # 深度研报框架
│   └── backtest.md          # 技术回测框架
├── templates/               # 报告模板
│   ├── report_template.md
│   └── valuation_template.md
├── examples/                # 脱敏示例（使用中性股票代码演示）
├── observations/            # 方法论层面的规律记录
├── experiments/             # 策略实验与版本管理
├── docs/                    # 详细文档与方法论
├── fugui-finance-package/   # 东方财富API数据引擎
│   ├── dfcf_finance/        # 行情/财报/选股/筹码峰
│   └── spring-river-warm/   # 估值引擎
├── lucky-bamboo/            # 策略脚本
│   ├── scripts/             # 回测/扫描/选股
│   └── references/          # API文档与备忘
├── config.example.yaml      # 配置模板
└── private/                 # 请自行创建（Git忽略）
```

## 设计原则

| 层 | 位置 | 包含内容 | 是否上传 |
|----|------|---------|---------|
| **Skill** | SKILL.md / prompt/ | 通用流程与方法 | ✅ |
| **Code** | scripts/ / fugui-finance-package/ / lucky-bamboo/ | 可执行代码 | ✅ |
| **Template** | templates/ | 报告模板 | ✅ |
| **Example** | examples/ | 脱敏示例（中性代码） | ✅ |
| **Observation** | observations/ | 方法论规律（不含具体标的） | ✅ |
| **Experiment** | experiments/ | 策略实验记录与版本 | ✅ |
| **Config** | config.example.yaml | 配置模板 | ✅ |
| **Private** | private/ | 自选池、持仓、回测记录、密钥 | ❌ |
| **Reports** | research/ | 个人研报 | ❌ |

- Skill 层只描述"怎么做"，不描述"我做过什么"。
- 代码通过 `load_watchlist()` 从配置文件读取标的，不硬编码股票代码。
- 观察日志记录方法论规律（如"某市值区间在当前环境下表现最优"），不记录具体回测结果。
- 个人自选池、持仓数据、API密钥请放入 `private/` 目录，该目录已在 `.gitignore` 中排除。

## 扩展

本项目可作为 Hermes Agent 的技能集使用。将 `prompt/` 目录下的文件导入对应技能的提示词配置即可。
