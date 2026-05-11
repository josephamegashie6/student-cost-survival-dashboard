# Student Financial Intelligence Dashboard

**A financial decision-support system for cost-of-living analytics, affordability monitoring, and financial planning.**

---

## Overview

The **Student Financial Intelligence Dashboard** is a financial analytics platform designed to help students monitor spending behaviour, forecast living costs, evaluate affordability pressure, and make data-driven financial decisions. Built with a Bloomberg-inspired dark finance aesthetic, the system transforms raw financial inputs into structured decision-support outputs across five analytical modules.

> *"A financial intelligence platform — not a budgeting app."*

---

## Problem Statement

Students navigating academic and living expenses face compounding financial pressures: rising housing costs, tuition obligations, variable income streams, and limited financial planning infrastructure. Without structured analytical tools, students lack visibility into their affordability position, spending behaviour patterns, and long-term financial sustainability — resulting in reactive rather than proactive financial decision-making.

---

## Solution

Developed a financial intelligence platform combining:

- **Spending analytics** — monthly cash flow decomposition and expense categorisation
- **Affordability monitoring** — rent burden ratios, tuition pressure indicators, and cost burden analysis
- **Forecasting models** — inflation-adjusted 24-month balance projections and semester affordability modelling
- **Scenario simulation** — rent increase, tuition pressure, income reduction, and spending cut scenarios
- **Behavioural finance alerts** — overspending detection, anomaly identification, and financial stress indicators

---

## System Features

| Module | Description |
|---|---|
| **Cash Flow Analysis** | Monthly inflow/outflow decomposition, fixed vs variable expense categorisation, 12-month savings trajectory |
| **Cost Intelligence** | Rent burden ratio, tuition pressure indicator, transportation and food cost ratios, spending anomaly detection |
| **Financial Health Indicators** | Composite 0–100 stability score, emergency fund coverage, affordability score, financial stress level |
| **Forecasting Engine** | Inflation-adjusted balance projection, semester affordability projection, liquidity risk detection |
| **Scenario Analysis** | Rent increase simulation, tuition pressure, income reduction, spending reduction with waterfall impact analysis |
| **City Analytics** | Multi-city cost-of-living comparison across 18 months with semester-phase financial analysis |

---

## Analytical Workflow

```
Income Inputs
     ↓
Expense Categorisation
     ↓
Cash Flow Analysis
     ↓
Forecast Modelling
     ↓
Risk & Affordability Analysis
     ↓
Financial Planning Insights
```

---

## Technical Architecture

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly (interactive, dark finance theme) |
| Forecasting | Inflation-adjusted multi-period projection model |
| Analytics | Cost burden ratios, affordability scoring, behavioural anomaly detection |
| Deployment | GitHub + Streamlit Cloud |

---

## Dataset

The platform uses a realistic 18-month dataset across three US cities (Saint Louis, Chicago, New York City) with:

- Irregular expense spikes and semester-based variations
- Housing pressure differences by market
- Unexpected spending events (emergency expenses)
- Inflation-adjusted cost progression
- Semester phase categorisation (Pre-Arrival, Fall, Spring, Summer, Winter Break)

---

## KPI Language

| Standard Term | Platform Term |
|---|---|
| Monthly Spending | Total Monthly Outflows |
| Money Left | Projected Net Liquidity |
| Budget Health | Financial Stability Indicator |
| Savings | Cash Reserve Position |
| Rent % | Rent Burden Ratio |
| Emergency Buffer | Emergency Fund Coverage |

---

## Portfolio Positioning

This project demonstrates competency in:

- Financial analytics and decision-support system design
- Cost modelling and affordability analysis
- Data-driven forecasting and scenario planning
- Behavioural finance indicators and risk alerting
- Interactive dashboard development with professional finance aesthetics

Suitable for roles in **financial analysis**, **business analytics**, **fintech**, **operational analytics**, and **data-driven financial planning**.

---

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

---

*Public presentation adapted from a simulated financial planning and cost intelligence workflow for portfolio demonstration purposes.*
