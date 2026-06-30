# Fugui Research Lab

> An AI-assisted equity research framework for A-share markets — valuation, quantitative backtesting, and automated report generation.

> 我们不是为了寻找每天都能交易的机会，而是为了持续理解少数值得长期跟踪的公司，并在风险收益比最优的时候采取行动。

## What it does

Fugui Research Lab combines Eastern Fortune (东方财富) market data APIs with structured analytical pipelines to produce institutional-grade equity research. It supports the full workflow: data ingestion → sector analysis → peer comparison → valuation modeling → report generation.

## Quick start

```bash
git clone git@github.com:imartinw29/Fugui-research-lab.git
cd Fugui-research-lab

# Configure
cp config.example.yaml config.yaml      # Add API credentials
mkdir -p private/
cp private/watchlist.example.yaml private/watchlist.yaml

# Install and run
pip install -r requirements.txt
python lucky-bamboo/scripts/backtest_bb_kdj_macd.py
```

## Architecture

```
├── prompt/                  # System prompts for each analytical scenario
│   ├── valuation.md         # Valuation analysis framework
│   ├── report.md            # Deep research report framework
│   └── backtest.md          # Technical backtest framework
├── templates/               # Reusable report templates
├── examples/                # Sanitized demos (neutral tickers)
├── fugui-finance-package/   # Eastern Fortune API data engine
│   ├── dfcf_finance/        # Quotes, financials, screening, chip distribution
│   └── spring-river-warm/   # Valuation engine
├── lucky-bamboo/            # Strategy scripts
│   ├── scripts/             # Backtesting, scanning, signal generation
│   └── references/          # API documentation and notes
├── docs/                    # Methodology and workflow documentation
├── observations/            # Methodology-level pattern records
├── experiments/             # Strategy experiments and versioning
├── config.example.yaml      # Configuration template
└── private/                 # User-managed (gitignored)
```

## Capabilities

| Capability | Trigger | Description |
|-----------|---------|-------------|
| Data | `data()` | Real-time quotes, financials, screening, chip distribution |
| Sector Analysis | sector-overview | Market size, competitive landscape, valuation context |
| Peer Comparison | comps-analysis | Operating metrics + valuation multiples + statistical distribution |
| Report Generation | research-report | Pipeline: sector → comps → report |
| Technical Backtest | technical-backtest | Bollinger/KDJ/MACD multi-signal with performance attribution |
| Deep Research | deep-research | Horizontal-vertical analysis: history + competitors + synthesis |

## Design principles

- Skill definitions describe workflows, not personal trading history.
- Source code loads tickers from configuration files — zero hardcoded symbols.
- Observation logs record methodological patterns, not specific backtest results.
- Personal watchlists, holdings, and API keys belong in `private/` (gitignored).

## Roadmap

- [x] Multi-factor backtesting (Bollinger + KDJ + MACD)
- [x] Automated deep research reports
- [x] Sector overview and peer comparison pipelines
- [x] Darwinian prompt/parameter evolution
- [ ] Factor attribution analysis
- [ ] Portfolio optimization (Kelly criterion)
- [ ] Interactive visualization dashboard

## License

MIT
