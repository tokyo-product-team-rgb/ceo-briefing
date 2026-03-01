# S&P 500 Valuation Buy Signal Methodology

## Source
- **JPMorgan Guide to the Markets (Q4 2024)** — Forward P/E vs. 10-year returns scatter plot
- **Howard Marks (Oaktree Capital)** — My First Million Pod interview (Feb 2026)
- **Robert Shiller** — CAPE ratio methodology (Yale)
- **Data sources:** IBES, Refinitiv Datastream, Standard & Poor's

## Core Finding

Forward P/E at time of purchase has a strong **negative correlation** with subsequent 10-year annualized returns.

| Forward P/E | Historical 10-Year Return |
|-------------|---------------------------|
| 8-10x       | 15-20% annualized         |
| 10-12x      | 12-15% annualized         |
| 12-14x      | 8-12% annualized          |
| 14-17x      | 5-8% annualized           |
| 17-20x      | 2-5% annualized           |
| 20-23x      | 0-2% annualized           |
| 23x+        | −2% to +2% (flat)         |

## Key Quote (Howard Marks)

> "JPMorgan published a chart showing the relationship between the S&P 500 P/E at purchase and the return over the next 10 years. If you bought the S&P when the P/E ratio was 23, **in every case** your annualized return over the next 10 years was between +2% and −2%."

## Buy Signal Thresholds

| Signal       | Forward P/E | Shiller CAPE | Action                    |
|--------------|-------------|--------------|---------------------------|
| 🔴 EXPENSIVE | >21x        | >28x         | Wait, build cash          |
| 🟠 CAUTION   | 18-21x      | 22-28x       | Selective, quality focus  |
| 🟡 HOLD      | 15-18x      | 18-22x       | Fair value, hold positions|
| 🟢 BUY       | 12-15x      | 14-18x       | Attractive entry          |
| 💚 STRONG BUY| <12x        | <14x         | Back up the truck         |

## Historical Context

| Date | Event | Forward P/E | Next 10Y CAGR |
|------|-------|-------------|---------------|
| Aug 1982 | Volcker bottom | ~8x | +18.0% |
| Dec 1974 | Stagflation low | ~7x | +14.0% |
| Oct 2002 | Dot-com bottom | ~14x | +8.3% |
| Mar 2009 | GFC bottom | ~10x | +14.5% |
| Mar 2020 | COVID crash | ~13x | +12%+ (ongoing) |
| Feb 2026 | Current | ~24x | 0-2% expected |

## P/E Zone Patterns

| P/E Zone | Signal | Frequency |
|----------|--------|-----------|
| <10x | 💚 Generational buy | 2-3× per lifetime |
| 10-12x | 🟢 Strong buy | Major crises |
| 12-15x | 🟢 Good entry | Significant corrections |
| 15-17x | 🟡 Fair value | Normal pullbacks |
| 17-20x | 🟠 Mediocre | Muted returns |
| >20x | 🔴 Poor entry | Current zone |

**What creates buying opportunities:**
- Recessions (avg P/E drop: 30-40%)
- Financial crises (avg P/E drop: 40-50%)
- Panic events (flash crashes, wars)

**Current context:** S&P would need to drop ~30% (to ~4,850) to reach P/E 17x fair value, or ~50% (to ~3,500) for P/E 12x strong buy territory.

## Implementation in CEO Briefing

Added to:
1. **Economic Health Composite** — New "Valuation Signal (20%)" indicator section
2. **Markets & Economy** — Dedicated "S&P 500 Buy Signal" card with table

Updates needed when:
- Forward P/E changes significantly (recalculate from S&P level / forward earnings)
- Market drops 20%+ (signal may change to BUY)
- Quarterly earnings revisions shift forward estimates

## Data Sources for Updates

- **Shiller CAPE:** https://www.multpl.com/shiller-pe
- **Forward P/E:** https://www.yardeni.com/pub/peacockfeval.pdf
- **S&P 500 Earnings:** https://www.spglobal.com/spdji/en/indices/equity/sp-500/
