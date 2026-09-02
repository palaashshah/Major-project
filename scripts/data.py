import yfinance as yf
import pandas as pd

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
    data = yf.download(tickers, period = period)
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

