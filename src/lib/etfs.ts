// Frontend mirror of backend/scripts/data.py UNIVERSE.
// Placeholder expected returns / volatilities are used until the optimizer
// endpoint is wired up; getOptimizedPortfolio() in lib/api.ts will replace
// the defaults with real numbers when the backend returns them.

export type EtfCategory = 'equity' | 'gold' | 'debt' | 'liquid'

export type Etf = {
  ticker: string
  label: string
  category: EtfCategory
  note: string
  // annualized, decimal — e.g. 0.13 = 13%
  expectedReturn: number
  vol: number
  color: string
}

export const ETFS: Etf[] = [
  { ticker: 'NIFTYBEES.NS',  label: 'Nifty 50',        category: 'equity', note: 'Broad-market equity',  expectedReturn: 0.13, vol: 0.18, color: '#6D8196' },
  { ticker: 'JUNIORBEES.NS', label: 'Nifty Next 50',   category: 'equity', note: 'Mid-cap tilt',         expectedReturn: 0.15, vol: 0.22, color: '#a0b4c4' },
  { ticker: 'BANKBEES.NS',   label: 'Bank Nifty',      category: 'equity', note: 'Banking sector',       expectedReturn: 0.14, vol: 0.24, color: '#5DCAA5' },
  { ticker: 'ITBEES.NS',     label: 'Nifty IT',        category: 'equity', note: 'IT sector',            expectedReturn: 0.14, vol: 0.23, color: '#97C459' },
  { ticker: 'PHARMABEES.NS', label: 'Nifty Pharma',    category: 'equity', note: 'Pharma sector',        expectedReturn: 0.11, vol: 0.20, color: '#c9d97a' },
  { ticker: 'GOLDBEES.NS',   label: 'Gold ETF',        category: 'gold',   note: 'Physical gold proxy',  expectedReturn: 0.08, vol: 0.14, color: '#EF9F27' },
  { ticker: 'SETF10GILT.NS', label: '10Y Gilt ETF',    category: 'debt',   note: 'Sovereign debt proxy', expectedReturn: 0.07, vol: 0.06, color: '#8497b5' },
  { ticker: 'LIQUIDBEES.NS', label: 'Liquid Fund',     category: 'liquid', note: 'Cash proxy',           expectedReturn: 0.05, vol: 0.005, color: '#F09595' },
]

export const TICKERS = ETFS.map(e => e.ticker)

export function etf(ticker: string): Etf | undefined {
  return ETFS.find(e => e.ticker === ticker)
}

// Default portfolios keyed by risk-profile slug used elsewhere in the app.
// Sum to 100 for each profile. These are placeholders — replaced by the
// optimizer endpoint when it is wired up.
export const DEFAULT_WEIGHTS_BY_PROFILE: Record<string, Record<string, number>> = {
  guardian: {
    'NIFTYBEES.NS': 10, 'JUNIORBEES.NS': 0, 'BANKBEES.NS': 5, 'ITBEES.NS': 5, 'PHARMABEES.NS': 0,
    'GOLDBEES.NS': 15, 'SETF10GILT.NS': 40, 'LIQUIDBEES.NS': 25,
  },
  defender: {
    'NIFTYBEES.NS': 18, 'JUNIORBEES.NS': 4, 'BANKBEES.NS': 6, 'ITBEES.NS': 6, 'PHARMABEES.NS': 3,
    'GOLDBEES.NS': 13, 'SETF10GILT.NS': 32, 'LIQUIDBEES.NS': 18,
  },
  moderator: {
    'NIFTYBEES.NS': 25, 'JUNIORBEES.NS': 8, 'BANKBEES.NS': 8, 'ITBEES.NS': 8, 'PHARMABEES.NS': 5,
    'GOLDBEES.NS': 10, 'SETF10GILT.NS': 22, 'LIQUIDBEES.NS': 14,
  },
  builder: {
    'NIFTYBEES.NS': 28, 'JUNIORBEES.NS': 12, 'BANKBEES.NS': 10, 'ITBEES.NS': 10, 'PHARMABEES.NS': 5,
    'GOLDBEES.NS': 8, 'SETF10GILT.NS': 17, 'LIQUIDBEES.NS': 10,
  },
  explorer: {
    'NIFTYBEES.NS': 30, 'JUNIORBEES.NS': 18, 'BANKBEES.NS': 12, 'ITBEES.NS': 12, 'PHARMABEES.NS': 6,
    'GOLDBEES.NS': 6, 'SETF10GILT.NS': 10, 'LIQUIDBEES.NS': 6,
  },
}

export function defaultWeightsFor(profile?: string): Record<string, number> {
  const key = (profile ?? 'moderator').toLowerCase()
  return DEFAULT_WEIGHTS_BY_PROFILE[key] ?? DEFAULT_WEIGHTS_BY_PROFILE.moderator
}

export const CONSTRAINTS = {
  minLiquid: 3,           // LIQUIDBEES.NS floor
  minDebt: 15,            // SETF10GILT + LIQUIDBEES
  maxEquity: 75,          // sum of the 5 equity-category ETFs
  maxSingleAsset: 40,     // per-ticker cap
}

// Category → aggregate weight helper (used by charts / rationale).
export function aggregateByCategory(weights: Record<string, number>): Record<EtfCategory, number> {
  const agg: Record<EtfCategory, number> = { equity: 0, gold: 0, debt: 0, liquid: 0 }
  ETFS.forEach(e => { agg[e.category] += weights[e.ticker] ?? 0 })
  return agg
}

// Portfolio-level metrics from weights + ETF metadata. Assumes assets are
// uncorrelated — good enough for the UI preview; the real optimizer will
// return proper mean/vol/Sharpe from the covariance matrix.
export function portfolioMetrics(weights: Record<string, number>) {
  const expReturn = ETFS.reduce((s, a) => s + ((weights[a.ticker] ?? 0) / 100) * a.expectedReturn, 0)
  const variance  = ETFS.reduce((s, a) => s + Math.pow((weights[a.ticker] ?? 0) / 100, 2) * Math.pow(a.vol, 2), 0)
  const vol       = Math.sqrt(variance)
  const sharpe    = (expReturn - 0.055) / (vol || 0.0001)
  return { expReturn: expReturn * 100, vol: vol * 100, sharpe }
}

export function checkConstraints(weights: Record<string, number>): string[] {
  const violations: string[] = []
  const total = ETFS.reduce((s, a) => s + (weights[a.ticker] ?? 0), 0)
  if (Math.round(total) !== 100) violations.push(`Weights sum to ${total.toFixed(1)}%, must equal 100%`)

  const liquid = weights['LIQUIDBEES.NS'] ?? 0
  if (liquid < CONSTRAINTS.minLiquid) violations.push(`LIQUIDBEES below ${CONSTRAINTS.minLiquid}% liquidity floor`)

  const debtTotal = (weights['SETF10GILT.NS'] ?? 0) + liquid
  if (debtTotal < CONSTRAINTS.minDebt) violations.push(`Debt (gilt + liquid) below ${CONSTRAINTS.minDebt}% minimum`)

  const equityTotal = ETFS.filter(e => e.category === 'equity').reduce((s, e) => s + (weights[e.ticker] ?? 0), 0)
  if (equityTotal > CONSTRAINTS.maxEquity) violations.push(`Total equity exposure exceeds ${CONSTRAINTS.maxEquity}% cap`)

  ETFS.forEach(a => {
    if ((weights[a.ticker] ?? 0) > CONSTRAINTS.maxSingleAsset) {
      violations.push(`${a.ticker} exceeds ${CONSTRAINTS.maxSingleAsset}% single-asset cap`)
    }
  })

  return violations
}
