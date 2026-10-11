import sys
import os
import uuid
from datetime import datetime
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add the parent directory ('backend/') to sys.path so we can import models & database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models import DataSnapshot, AssetMean, AssetCovariance
from models import DataSnapshot, AssetMean, AssetCovariance, MarketData

UNIVERSE = [
    "NIFTYBEES.NS",     # broad-market equity
    "JUNIORBEES.NS",    # mid-cap
    "BANKBEES.NS",      # sector: banking
    "ITBEES.NS",        # sector: IT
    "PHARMABEES.NS",    # sector: pharma
    "GOLDBEES.NS",      # gold
    "SETF10GILT.NS",    # gilt/debt proxy
    "LIQUIDBEES.NS",    # liquid fund proxy
]

# for ticker in UNIVERSE:
#     data = yf.download(ticker, period="5y", auto_adjust=False)
#     print(data.head())
#     print(data.tail())
#     print(len(data))


def download_prices(tickers: list[str], period: str = "5y") -> pd.DataFrame:
    """
    Downloads price data for the given tickers and returns
    a DataFrame of closing prices only: dates as index, one column per ticker.
    """
    data = yf.download(tickers, period=period, auto_adjust=True)
    return (data['Close'])

# prices = download_prices(UNIVERSE)
# print(prices.head())
# print(prices.shape)

# d = yf.download("NIFTYBEES.NS", period="5y", auto_adjust=False)
# print((d['Close'] - d['Adj Close']).describe())

def validate_prices(prices: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Checks the price DataFrame for missing values and implausible returns.
    Returns (is_valid, list_of_issue_descriptions).
    """
    issues = []

    # missing values
    missing_counts = prices.isna().sum()
    for ticker, count in missing_counts.items():
        if count > 0:
            issues.append(f"{ticker}: {count} missing values")

    # implausible returns
    daily_returns = prices.pct_change()
    threshold = 0.20
    mask = daily_returns.abs() > threshold

    for ticker in mask.columns:
        bad_dates = mask.index[mask[ticker]]  # dates where that ticker's mask is True
        for date in bad_dates:
            pct = daily_returns.loc[date, ticker] * 100
            issues.append(f"{ticker}: {pct:.1f}% move on {date.date()}")

    is_valid = len(issues) == 0
    return is_valid, issues

def compute_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Resamples daily prices to monthly (last trading day of month),
    then computes monthly percentage returns.
    """
    monthly_prices = prices.resample('ME').last()
    # print(monthly_prices.head())      # <-- should look like prices, e.g. 40-3000 range
    monthly_returns = monthly_prices.pct_change()
    # print(monthly_returns.head())     # <-- should look like small decimals, e.g. -0.05, 0.12
    return monthly_returns

def compute_mean_and_cov(monthly_returns: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """
    Computes annualized mean return vector and annualized covariance matrix
    from monthly returns.
    """
    monthly_returns = monthly_returns.dropna()  # first month is NaN from pct_change()

    monthly_mean = monthly_returns.mean()
    annual_mean = (1 + monthly_mean) ** 12 - 1

    monthly_cov = monthly_returns.cov()
    annual_cov = monthly_cov * 12

    return annual_mean, annual_cov

def save_snapshot(db: Session, mu: pd.Series, cov: pd.DataFrame) -> uuid.UUID:
    """
    Saves an annualized mean return vector and covariance matrix 
    into PostgreSQL as an immutable snapshot.
    """
    snapshot_id = uuid.uuid4()
    ticker_list = list(mu.index)
    
    # 1. Create top-level snapshot metadata record
    snapshot = DataSnapshot(
        snapshot_id=snapshot_id,
        created_at=datetime.now(timezone.utc),
        ticker_list=ticker_list
    )
    db.add(snapshot)

    # 2. Add mean return entries
    for ticker, mean_val in mu.items():
        asset_mean = AssetMean(
            snapshot_id=snapshot_id,
            ticker=ticker,
            mean_return=float(mean_val)
        )
        db.add(asset_mean)

    # 3. Flatten and add covariance matrix entries
    cov_stacked = cov.rename_axis(index='ticker_i', columns='ticker_j').stack().reset_index()
    cov_stacked.columns = ['ticker_i', 'ticker_j', 'cov_value']

    for _, row in cov_stacked.iterrows():
        asset_cov = AssetCovariance(
            snapshot_id=snapshot_id,
            ticker_i=row['ticker_i'],
            ticker_j=row['ticker_j'],
            cov_value=float(row['cov_value'])
        )
        db.add(asset_cov)

    db.commit()
    return snapshot_id

def load_snapshot(db: Session, snapshot_id: uuid.UUID) -> tuple[pd.Series, pd.DataFrame]:
    """
    Retrieves a snapshot from PostgreSQL by ID and reconstructs 
    it as a pandas Series (mean vector) and DataFrame (covariance matrix).
    """
    # 1. Fetch means
    means_query = db.query(AssetMean).filter(AssetMean.snapshot_id == snapshot_id).all()
    if not means_query:
        raise ValueError(f"Snapshot ID {snapshot_id} not found in database.")

    mu_dict = {item.ticker: item.mean_return for item in means_query}
    mu = pd.Series(mu_dict)

    # 2. Fetch covariances and pivot into symmetric matrix
    cov_query = db.query(AssetCovariance).filter(AssetCovariance.snapshot_id == snapshot_id).all()
    cov_data = [{
        'ticker_i': item.ticker_i,
        'ticker_j': item.ticker_j,
        'cov_value': item.cov_value
    } for item in cov_query]

    cov_df = pd.DataFrame(cov_data)
    cov = cov_df.pivot(index='ticker_i', columns='ticker_j', values='cov_value')

    # Enforce matrix alignment with mu index
    cov = cov.reindex(index=mu.index, columns=mu.index)

    return mu, cov

def save_prices(db: Session, prices: pd.DataFrame) -> int:
    """
    Stores daily closing prices, replacing what was stored for these tickers.
    WHY replace: adjusted prices are revised whenever a dividend is paid, so
    mixing an old download with a new one would give an inconsistent series.
    """
    tickers = list(prices.columns)
    db.query(MarketData).filter(MarketData.asset_symbol.in_(tickers)).delete(synchronize_session=False)

    rows = []
    for ticker in tickers:
        for day, price in prices[ticker].dropna().items():
            rows.append({
                "id": f"{ticker}|{day.date()}",
                "asset_symbol": ticker,
                "date": day.date(),
                "close_price": float(price),
                "data_source": "yfinance",
            })
    db.bulk_insert_mappings(MarketData, rows)
    db.commit()
    return len(rows)

def main():
    # 1. Ensure DB tables exist
    Base.metadata.create_all(bind=engine)

    prices = download_prices(UNIVERSE)
    is_valid, issues = validate_prices(prices)
    print(is_valid, issues)

    monthly_returns = compute_monthly_returns(prices)
    mu, cov = compute_mean_and_cov(monthly_returns)

    db = SessionLocal()
    try:
        saved = save_prices(db, prices)
        print(f"Saved {saved} daily prices.")
        print("Saving snapshot to PostgreSQL...")
        snapshot_id = save_snapshot(db, mu, cov)
        print(f"Successfully saved snapshot! Snapshot ID: {snapshot_id}")

        # 5. Load back to verify round-trip integrity
        print("Verifying round-trip by loading snapshot from database...")
        loaded_mu, loaded_cov = load_snapshot(db, snapshot_id)
        
        print("\n--- Loaded Mean Returns ---")
        print(loaded_mu)
        print("\n--- Loaded Covariance Matrix Shape ---")
        print(loaded_cov.shape)

    finally:
        db.close()

if __name__ == "__main__":
    main()