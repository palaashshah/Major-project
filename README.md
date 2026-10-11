# Integrated Investor Relationship & Portfolio Decision Support System

A final-year major project. It joins a CRM module (investor profiles, risk questionnaire,
interaction history) to a quantitative portfolio optimization engine. A relationship manager
selects an investor, and the system computes a portfolio for that person's risk constraints,
explains why, and logs everything for audit.

**It claims:** consistent, suitable, explainable, auditable recommendations.
**It does not claim:** to beat the market or predict returns. Expected return and risk
figures are estimates from historical data. This is an academic project, not investment advice.


## How it works

1. The investor answers ten questions. The backend scores risk **capacity** and risk
   **tolerance** separately, each from 0 to 100. The lower one governs.
2. The score sets a target share of equity; the investment horizon can cap it.
3. A mean-variance (Markowitz) optimizer finds the best weights across a fixed set of
   Indian ETFs, inside those limits, a 35% per-instrument cap and any sector exclusions.
4. A rule-based rationale explains the result. No machine learning is involved.
5. The manager approves or rejects; the client's decision is logged.
6. An accepted portfolio can be valued on later prices, with an alert when any holding
   drifts more than 5 percentage points from its approved weight.

Every tunable number lives in `backend/config/risk_constraints.py`.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL
- **Optimization:** PyPortfolioOpt (cvxpy), pandas, numpy
- **Market data:** yfinance (batch download of NSE tickers; no real-time feed)
- **Frontend:** Next.js, React, TypeScript
- **Tests:** pytest


## Prerequisites

- Python 3.11 or newer
- PostgreSQL, running locally
- A recent Node.js LTS release (for the frontend)

## Setup

### 1. Database

Create an empty PostgreSQL database, then create a file named `.env` inside `backend/`:

```
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/DATABASE_NAME
```

The `.env` file is ignored by git. Never commit it.

### 2. Backend

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # run this in every new terminal
pip install -r requirements.txt
```

### 3. Market data

From `backend/`:

```bash
python scripts/data.py
```

This creates the tables, downloads about five years of daily prices, stores them, and saves
a snapshot of average returns and covariances. Run it again whenever fresher data is wanted.
The optimizer only ever reads stored snapshots.

### 4. Seed a manager

Investors are assigned to a manager, and login is not built yet. Add one manager row once,
using any PostgreSQL client:

```sql
INSERT INTO users (id, name, role) VALUES ('manager-001', 'Demo Manager', 'manager');
```

### 5. Run the API

From `backend/`:

```bash
uvicorn main:app --reload
```

- API: http://localhost:8000
- Interactive docs, where every endpoint can be tried: http://localhost:8000/docs

### 6. Run the frontend

From the repository root, in a second terminal:

```bash
npm install
npm run dev
```

The site runs at http://localhost:3000 and expects the API at http://localhost:8000.

## Tests

From `backend/`, with the virtual environment active:

```bash
python -m pytest tests -q
```

The tests use made-up market data and need no database or network.

## API overview

| Endpoint | Purpose |
| --- | --- |
| `GET/POST/PUT/DELETE /investors` | Investor profiles |
| `GET/POST /interactions` | Interaction history |
| `POST /risk/score` | Score questionnaire answers without saving |
| `POST /investors/{id}/risk-assessments` | Score and save an assessment |
| `GET /investors/{id}/risk-assessments` | Assessment history |
| `POST /optimize` | Optimize and save a portfolio for an investor |
| `POST /optimize/metrics` | Metrics and rule checks for hand-edited weights |
| `GET /portfolios`, `GET /portfolios/{id}` | Saved portfolios |
| `GET /portfolios/{id}/rationale` | Plain-language explanation |
| `POST /portfolios/{id}/manager-decision` | Approve or reject |
| `POST /portfolios/{id}/client-decision` | Record the client accepting or declining |
| `GET /portfolios/{id}/decisions` | Decision trail |
| `GET /portfolios/{id}/valuation` | Paper value, gain and drift |
| `GET /drift-alerts` | Accepted portfolios that need rebalancing |

### Trying the full flow from the docs page

1. `GET /investors/` and copy an investor `id`.
2. `POST /investors/{id}/risk-assessments` with ten answers, for example:
   `{"answers": {"4": 2, "5": 2, "6": 1, "7": 0, "8": 1, "9": 2, "10": 1, "11": 2, "12": 1, "13": 4}}`
3. `POST /optimize` with `{"investor_id": "..."}`.
4. `GET /portfolios/{portfolio_id}/rationale`.
5. `POST /portfolios/{portfolio_id}/manager-decision`, then `.../client-decision`.
6. `GET /portfolios/{portfolio_id}/valuation`.

The docs page pre-fills example bodies with placeholder values. Remove optional fields you
do not mean to send.

## Helper scripts

Run from `backend/`.

| Script | What it does |
| --- | --- |
| `scripts/data.py` | Downloads prices, stores them, saves a new snapshot |
| `scripts/preview_buckets.py` | Prints one portfolio per risk bucket |
| `scripts/preview_scores.py` | Prints one portfolio for a range of scores |
| `scripts/demo.py` | Prints five sample investors from answers to explanation |
| `scripts/seed_demo_portfolio.py <investor_id> [days_ago]` | Creates a sample portfolio dated in the past, for trying valuation and drift |

## Known limitations

- Expected returns are five-year historical averages, so the optimizer favours whatever did
  best in that window.
- The universe has eight ETFs. Sector exclusions work per instrument; ethical categories
  such as tobacco are recorded but cannot be enforced with this universe.
- The liquid fund's price series is flat, so cash holdings are valued by accruing interest
  at the risk-free rate. This is an assumption, not market data.
- Valuation is a paper calculation. The system places no trades.
- The manager is hardcoded as `manager-001`; there is no login or role checking yet.

