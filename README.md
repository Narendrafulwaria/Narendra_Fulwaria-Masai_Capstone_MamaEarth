# Narendra_Fulwaria-Masai_Capstone_MamaEarth
# Mamaearth Returns & Growth Intelligence Pipeline

Three connected layers: **SQL** (relational store + reports) → **Python/pandas** (cleaning + analysis) → **GenAI narrator** (SCR business narrative).
No layer reports a number it did not compute itself or receive from the layer before it.

## Repository structure

```
├── README.md
├── sql/            schema.sql, seed_data.sql, reports.sql
├── data/           customers.csv, products.csv, orders.csv   (raw, never edited)
├── analysis/       clean_and_eda.py, visualize.py
├── visualizations/ return_rate_by_payment.png, monthly_revenue_trend.png
└── narrator/       findings.json, generate_narrative.py, sample_output.txt
```

## Requirements

- MySQL 8.x (or any SQL engine that supports the syntax used)
- Python 3.9+ with: `pip install pandas numpy matplotlib google-genai`

## Run order

### 1. SQL layer (Part 1)

```bash
mysql -u root -p < sql/schema.sql       # creates database mamaearth_analytics + 3 tables
mysql -u root -p < sql/seed_data.sql    # loads 45 customers, 16 products, 180 orders via INSERT
mysql -u root -p < sql/reports.sql      # runs reports (a)-(i)
```

Expected row counts after loading: 45 / 16 / 180. Expected headline outputs: total_orders 180,
total_revenue 99860.20, avg_order_value 554.78. Report (i) alters `customers`; to re-run `reports.sql`,
re-run `schema.sql` and `seed_data.sql` first.

### 2. Python analysis layer (Part 2)

```bash
python analysis/clean_and_eda.py    # cleaning, EDA, prints every intermediate result
python analysis/visualize.py        # writes both PNGs to visualizations/
```

Part 2 reads the raw CSVs in `data/` directly (independent of the SQL database).
The final step of `clean_and_eda.py` **writes `narrator/findings.json`** from the computed variables.
Nothing in that file is typed by hand. Key results: cleaned revenue 97,358.30; COD return rate 44.4%;
highest-risk segment COD + Tier-2 at 54.5%; true peak month March (20,318.90).

### 3. GenAI narrator layer (Part 3)

```bash
# Option A: no API key (offline, deterministic template, zero configuration)
python narrator/generate_narrative.py

# Option B: with Gemini (free-tier key from Google AI Studio, never a paid-only key)
export GEMINI_API_KEY="your-key-here"          # macOS / Linux
# setx GEMINI_API_KEY "your-key-here"          # Windows (reopen the terminal)
python narrator/generate_narrative.py

# Verify the five required figures in the saved Gemini sample
python narrator/generate_narrative.py --check narrator/sample_output.txt
```

If no key is set, or the API call fails, the script automatically falls back to the offline path.
Online runs save `narrator/sample_output.txt`; offline runs save `narrator/sample_output_offline.txt`.

## How data flows between layers

| From | To | What is passed |
|---|---|---|
| `data/*.csv` | SQL layer | loaded into MySQL by `seed_data.sql` |
| `data/*.csv` | Python layer | read directly with `pd.read_csv` |
| `analysis/clean_and_eda.py` | `narrator/findings.json` | verified totals, return rates, segment, peak month |
| `narrator/findings.json` | `generate_narrative.py` | the only source of numbers in the narrative |

## Reconciliation between layers

SQL raw total (Report a) = 99,860.20. Python cleaned total = 97,358.30.
The difference of 2,501.90 is entirely the 5 duplicate (double-submit) orders O0176–O0180
removed in Part 2. Imputing discount/rating does not change any order value.
