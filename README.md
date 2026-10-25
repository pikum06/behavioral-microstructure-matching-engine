# Behavioral Microstructure Matching Engine

## ABOUT

An analytical research framework and visual execution suite engineered to evaluate high-frequency market microstructure dynamics, limit order book (LOB) queue priority, and behavioral liquidity matching matrices across volatile trading regimes.

This repository processes order flow telemetry to model how non-linear trader behavior, order cancellation spikes, and toxic liquidity impact fill probability, execution latency, and spread capture efficiency.

---

## Repository Directory Structure

```text
.
├── outcomes/
│   ├── graphs/
│   │   ├── adjustment_type_pie.png
│   │   ├── architect_research_exhibit3.png
│   │   ├── architect_results3.png
│   │   └── matching_matrix3.png
│   └── models/
│       ├── behavioral_cols.json
│       ├── behavioral_norm_params.npz
│       └── global_behavioral_autoencoder.h5
├── research/
│   ├── data_cleaning/
│   │   ├── acs/
│   │   │   ├── clean_data.py
│   │   │   ├── global_model.py
│   │   │   └── main.py
│   │   └── optiver/
│   │       └── data_clean_parquet.py
│   ├── behavioral_encode.py
│   ├── contract_architect.py
│   ├── main.py
│   ├── micro_encoder.py
│   └── visualize_contract.py
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Datasets & Data Pipeline

The matching engine integrates high-frequency limit order book (LOB) microdata alongside socio-demographic microdata to calibrate behavioral trauma decay and market microstructure volatility parameters.

### 1. High-Frequency Market Microstructure Data

* **Dataset:** [Optiver Realized Volatility Prediction](https://www.kaggle.com/competitions/optiver-realized-volatility-prediction/data)
* **Source:** Kaggle / Optiver (2021)
* **Direct Access:** [![Kaggle](https://img.shields.io/badge/Kaggle-Dataset_Page-20BEFF?style=flat-square&logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/optiver-realized-volatility-prediction/data)
* **Scale:** 2.73 GB (229 files in Apache Parquet & CSV format)
* **Resolution:** 1-second interval order book snapshots and trade execution logs

#### Data Schema Breakdown
| File / Component | Key Fields | Description |
| :--- | :--- | :--- |
| `book_[train/test].parquet` | `stock_id`, `time_id`, `seconds_in_bucket`, `bid_price1/2`, `ask_price1/2`, `bid_size1/2`, `ask_size1/2` | Top-2 depth levels of the order book. Captures order book imbalance, bid-ask spread dynamics, and liquidity depth. |
| `trade_[train/test].parquet` | `stock_id`, `time_id`, `seconds_in_bucket`, `price`, `size`, `order_count` | Executed market transactions. Used to compute realized order flow toxicity and volume-weighted trade impact. |
| `train.csv` / `test.csv` | `stock_id`, `time_id`, `target` | Ground-truth 10-minute realized volatility target values: $\sigma = \sqrt{\sum_{t} r_t^2}$ |

**Citation**

```
@misc{optiver2021realizedvolatility,
  author    = {Meyer, Andrew and BerniceOptiver and CameronOptiver and IXAGPOPU and Liu, Jiashen and Pietrobon, Matteo and OptiverMerle and Dane, Sohier and Vallentine, Stefan},
  title     = {Optiver Realized Volatility Prediction},
  year      = {2021},
  publisher = {Kaggle},
  url       = {[https://www.kaggle.com/competitions/optiver-realized-volatility-prediction](https://www.kaggle.com/competitions/optiver-realized-volatility-prediction)}
}
```

### 2. Socio-Demographic & Household Microdata

* **Dataset:** [2015 American Community Survey (ACS) Public Use Microdata Sample](https://www.kaggle.com/datasets/census/2015-american-community-survey)
* **Source:** U.S. Census Bureau / Kaggle Data Hub
* **Direct Access:** [![Kaggle](https://img.shields.io/badge/Kaggle-Dataset_Page-20BEFF?style=flat-square&logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/census/2015-american-community-survey)
* **License:** Public Domain (CC0)
* **Granularity:** Individual and household-level microdata

#### Data Schema Breakdown
| Feature Category | Key Fields | Description |
| :--- | :--- | :--- |
| **Cohort Weighting** | `PWGTP` | Person-level expansion weights applied for accurate population-level demographic synthesis. |
| **Economic Indicators** | Income, Employment, Demographics | Microdata variables used to model household financial cushions, liquidity constraints, and time-preference decay. |

**Citation**

```
@misc{us_census_acs_2015,
  author    = {U.S. Census Bureau},
  title     = {2015 American Community Survey Public Use Microdata Sample},
  year      = {2015},
  publisher = {Kaggle Data Hub},
  url       = {[https://www.kaggle.com/datasets/census/2015-american-community-survey](https://www.kaggle.com/datasets/census/2015-american-community-survey)}
}
```

---

## Microstructure & Matching Pipeline

## Microstructure & Matching Pipeline

```mermaid
graph TD
    %% Data Cleaning & Preprocessing
    subgraph Data Cleaning Pipeline
        A1[research/data_cleaning/acs/main.py] -->|Executes global_model & clean_data| A2[outcomes/models/]
        B1[research/data_cleaning/optiver/data_clean_parquet.py] --> B2[Parquet Datasets]
    end

    %% Research Pipeline Execution
    subgraph Research Execution Pipeline
        C[research/main.py] --> D[research/behavioral_encode.py]
        C --> E[research/micro_encoder.py]
        D -->|CSV Data Inputs| F[research/contract_architect.py]
        E -->|Parquet Data Inputs| F
        F --> G[research/visualize_contract.py]
    end

    %% Final Output Graphs
    subgraph Output Exhibits
        G --> H1[outcomes/graphs/adjustment_type_pie.png]
        G --> H2[outcomes/graphs/architect_research_exhibit3.png]
        G --> H3[outcomes/graphs/architect_results3.png]
        G --> H4[outcomes/graphs/matching_matrix3.png]
    end
```

---

## Core Analytics & Research Focus

1. **Microstructure Telemetry & Behavioral Bias Encoding (`micro_encoder.py` & `behavioral_encode.py`):**
   - **Microstructure Signals:** `micro_encoder.py` processes high-frequency order book data to compute Weighted Average Price (WAP), log-return realized volatility, and Order Flow Imbalance (OFI) to quantify net buying/selling pressure.
   - **Behavioral Profiling:** `behavioral_encode.py` parses demographic survey data (ACS) to derive a user `bias_score` based on historical economic exposure, classifying individual trader tendencies (e.g., Frugality vs. Overconfidence).

2. **Personalized Risk & Contract Architecture (`contract_architect.py`):**
   - Combines microstructure market risk ($\text{Realized Volatility} \times (1 + \vert{}\text{OFI}\vert{})$) with psychological bias scores:
     - **Overconfidence Buffer (`bias > 0.4`):** Dynamically scales hedge ratio by **1.5x** to cushion against over-leveraging.
     - **Frugality Efficiency (`bias < -0.4`):** Optimizes hedge ratio to **0.8x** for cost efficiency.
     - **Standard Alignment:** Preserves **1.0x** base market risk hedge ratio.

3. **Visual Execution Diagnostics & Sensitivity Heatmaps (`visualize_contract.py`):**
   - Generates three analytical diagnostic exhibits saved to `outcomes/`:
     - `architect_research_exhibit3.png`: Population bias distribution alongside market volatility sensitivity bands.
     - `architect_results3.png`: User age vs. final hedge ratio scatter plots categorized by behavioral correction type.
     - `matching_matrix3.png`: 2D heatmap matrix evaluating target hedge ratios across market micro-volatility and user behavioral bias.
     - `adjustment_matrix.png`: 
---

## Setup & Execution

1. **Installation:**

   `pip install -r requirements.txt`

2. **Sequence to run the files**
```mermaid
flowchart LR
    A["1️⃣ micro_encoder.py<br/><i>(Microstructure Signals)</i>"] --> B["2️⃣ behavioral_encode.py<br/><i>(Behavioral Profiling)</i>"]
    B --> C["3️⃣ contract_architect.py<br/><i>(Contract Matching)</i>"]
    C --> D["4️⃣ visualize_contract.py<br/><i>(Plots & Exhibits)</i>"]

    style A fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    style B fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    style C fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#fff
    style D fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#fff
```
---

## Visual Outcomes

1. **architect_research_exhibit3.png**

![Contract Sensitivity: Microstructure vs. Behavioral Hedge](outcomes/graphs/architect_research_exhibit3.png)

The above graph represents the mechanical advantage of the Behavioral-Microstructure Matching Engine. As the users are exposed to different degrees of actual market volatility in this simulation, the scaling of the Hedge Ratio is depicted by the red curve. This design, in contrast to conventional static models, makes use of real-time market microstructure data to modify protection levels; in particular, it increases the hedge when a user's own behavioral bias clashes with the current market “fear” (liquidity shocks).

2. **architect_results3.png**

![Contract Sensitivity: Microstructure vs. Behavioral Hedge](outcomes/graphs/architect_results3.png)

As shown in the above figure, the system successfully extracts and quantifies the “Experience Effect” across a demographic dataset of 1.4 milliion users sourced from the American Consumer Survey (ACS) 2015. By applying a smooth-decay exponential function tom ormative economic years, such as the 2008 Recession, the model maps a distinct population distribution of risk-tolerance. This data serves as the foundational layer for “Personalized Black-Scholes” contracts, ensuring that institutional protection is calibrated to an individual's unique historical economic exposure.

3. **matching_matrix3.png**

![Contract Sensitivity: Microstructure vs. Behavioral Hedge](outcomes/graphs/matching_matrix3.png)

A high precision heatmap for institutional risk management is shown in the above figure. The matrix finds crucial “High-Risk Zones” where protocol solvency is most susceptible to psychological panic by intersecting User Behavioral Bias with Market Realized Volatility. Decentralized banking protocols can anticipate and reduce systemic risk prior to a de-pegging or liquidation event by using this picture as the “Proof of Efficacy” for a hardware-agnostic security layer.

4. **`adjustment_type_pie.png`**
   ![Behavioral Adjustments Proportion](outcomes/graphs/adjustment_type_pie.png)
   *Proportional breakdown of behavioral correction policies across the full 1.5 million population, highlighting distribution across Overconfidence Buffers, Frugality Optimizations, and Standard Risk Alignments.*

