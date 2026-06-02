
# 📊 Financial & ESG Risk Analysis — Automotive Industry
### A data science case study on Tesla, Ford, and Volkswagen (2021–2024)
**Author:** Milan Thapa

---

## 🎯 Objectives
- Analyze financial performance (2021–2024) for Tesla, Ford, and Volkswagen
- Forecast key financial ratios for 2025–2026 using Linear Regression
- Compare ESG risk scores and their link to financial health

---

## 🗂️ Project Structure
```
financial-esg-automotive/
├── Datafpro.py           # Main analysis script
├── requirements.txt      # Python dependencies
└── data/                 # Excel financial statements
```

---

## 📊 Key Results

### Financial Ratios (2024)
| Company | Net Margin | ROA | Debt/Equity | ESG Risk |
|---|---|---|---|---|
| Tesla | 7.3% | 5.8% | 0.66 | 24.76 ✅ |
| Ford | 3.2% | 2.1% | 5.36 | 27.57 ⚠️ |
| Volkswagen | 3.3% | 1.7% | 2.39 | 26.89 🔶 |

> **ESG vs Profitability Correlation: -0.98**
> Lower ESG risk strongly correlates with better financial performance.

---

## 🔍 Key Findings

**Tesla** emerged as the clear financial leader, with net margins stabilizing at 7.3% in 2024 and the lowest ESG risk score (24.76). Its debt-to-equity ratio of 0.66 reflects a lean, efficient balance sheet.

**Ford** had the most volatile performance, suffering a sharp margin collapse in 2022 before partial recovery. It carries the highest ESG risk (27.57) and a concerning leverage ratio of 5.36, signaling significant financial exposure.

**Volkswagen** remained stable but inefficient, with the lowest ROA at 1.7% and an elevated ESG risk score (26.89), pointing to structural challenges in a large legacy operation.

**Forecast (2025–2026):** Tesla is projected to maintain profitability (~7.5% net margin), while Ford and Volkswagen face a declining trend — raising concerns about long-term competitiveness.

**Core Insight:** A -0.98 correlation between ESG risk and profitability confirms that lower ESG risk is not just ethical — it is financially advantageous. In the evolving automotive landscape, sustainability and financial health are increasingly inseparable.

---

## 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=flat)
![Seaborn](https://img.shields.io/badge/Seaborn-4C72B0?style=flat)

`pandas` `numpy` `matplotlib` `seaborn` `scikit-learn` `yfinance`

---

## 📁 Data Sources
- **Financial statements:** Yahoo Finance exports (2021–2024)
- **ESG scores:** Yahoo Finance via `yfinance` API
- **Currency conversion:** exchangerate-api.com (EUR → USD for Volkswagen)
