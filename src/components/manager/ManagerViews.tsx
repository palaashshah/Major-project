'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ETFS,
  aggregateByCategory,
  defaultWeightsFor,
  portfolioMetrics,
} from '@/lib/etfs'
import { getOptimizedPortfolio } from '@/lib/api'

type Investor = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
  assigned_manager_id?: string
}

// Small hook to try the optimizer, fall back to profile defaults.
function useAllocation(investorId?: string, profile?: string) {
  const defaults = useMemo(() => defaultWeightsFor(profile), [profile])
  const [weights, setWeights] = useState<Record<string, number>>(defaults)
  const [source, setSource] = useState<'defaults' | 'optimizer'>('defaults')

  useEffect(() => {
    setWeights(defaults)
    setSource('defaults')
  }, [defaults, investorId])

  useEffect(() => {
    if (!investorId) return
    let cancelled = false
    getOptimizedPortfolio(investorId).then(result => {
      if (cancelled || !result) return
      setWeights(result.weights)
      setSource('optimizer')
    })
    return () => { cancelled = true }
  }, [investorId])

  return { weights, source }
}

// ── Submission Queue ─────────────────────────────────────────────────────────

type SubmissionQueueProps = {
  investors: Investor[]
  onOpen: (id: string) => void
  onRunOptimization: (id: string) => void
}

export function SubmissionQueue({ investors, onOpen, onRunOptimization }: SubmissionQueueProps) {
  const pending = investors.slice(0, 6)

  return (
    <div style={{ padding: '2rem', maxWidth: 1000 }}>
      <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 6 }}>Submission Queue</h1>
      <p style={{ fontSize: 13, color: '#CBCBCB', marginBottom: '1.5rem' }}>
        New investor intakes awaiting an optimization run on the 8-ETF universe.
      </p>

      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12,
      }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr auto',
          padding: '10px 16px', gap: 12,
          borderBottom: '0.5px solid rgba(203,203,203,0.15)',
          fontSize: 11, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          <span>Investor</span><span>Risk</span><span>Horizon</span><span>AUM</span><span />
        </div>

        {pending.length === 0 && (
          <p style={{ padding: '1.5rem', fontSize: 13, color: '#CBCBCB' }}>No submissions in the queue.</p>
        )}

        {pending.map(inv => (
          <div key={inv.id} style={{
            display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr auto',
            padding: '12px 16px', gap: 12, alignItems: 'center',
            borderBottom: '0.5px solid rgba(203,203,203,0.08)',
            fontSize: 13, color: '#FFFFE3',
          }}>
            <span onClick={() => onOpen(inv.id)} style={{ cursor: 'pointer' }}>{inv.name}</span>
            <span style={{ color: '#a0b4c4', textTransform: 'capitalize' }}>{inv.risk_score ?? '—'}</span>
            <span style={{ color: '#CBCBCB', textTransform: 'capitalize' }}>{inv.investment_horizon ?? '—'}</span>
            <span style={{ fontFamily: 'monospace' }}>{inv.total_aum ? '₹' + inv.total_aum.toLocaleString('en-IN') : '—'}</span>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => onOpen(inv.id)} style={btnGhost}>Open</button>
              <button onClick={() => onRunOptimization(inv.id)} style={btnPrimary}>Run optimization</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Rationale Panel ──────────────────────────────────────────────────────────

type RationaleProps = {
  investorId?: string
  investorName?: string
  riskProfile?: string
}

export function RationalePanel({ investorId, investorName = 'Priya Desai', riskProfile = 'moderator' }: RationaleProps) {
  const { weights, source } = useAllocation(investorId, riskProfile)
  const agg = aggregateByCategory(weights)

  const points = useMemo(() => {
    const eq = agg.equity
    const tilt = eq >= 60 ? 'growth-oriented' : eq >= 40 ? 'balanced' : 'defensive'
    const topEquityEtf = ETFS
      .filter(e => e.category === 'equity')
      .sort((a, b) => (weights[b.ticker] ?? 0) - (weights[a.ticker] ?? 0))[0]

    return [
      `Portfolio tilts ${tilt} with ${eq.toFixed(0)}% total equity exposure across NIFTYBEES / JUNIORBEES / BANKBEES / ITBEES / PHARMABEES — consistent with a ${riskProfile} risk profile.`,
      `Equity leadership is ${topEquityEtf.ticker} at ${(weights[topEquityEtf.ticker] ?? 0).toFixed(0)}%, providing ${topEquityEtf.note.toLowerCase()}.`,
      `SETF10GILT.NS at ${(weights['SETF10GILT.NS'] ?? 0).toFixed(0)}% acts as the duration-and-income anchor; kept moderate given the current rate environment.`,
      `GOLDBEES.NS at ${(weights['GOLDBEES.NS'] ?? 0).toFixed(0)}% is a low-correlation inflation and geopolitical hedge.`,
      `LIQUIDBEES.NS at ${(weights['LIQUIDBEES.NS'] ?? 0).toFixed(0)}% preserves liquidity for opportunistic rebalancing over the next quarter.`,
      `Sector exclusions (if any) are applied when constructing the equity sleeve.`,
    ]
  }, [weights, agg.equity, riskProfile])

  return (
    <div style={{ padding: '2rem', maxWidth: 900 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3' }}>Rationale</h1>
        <SourceBadge source={source} />
      </div>
      <p style={{ fontSize: 13, color: '#CBCBCB', marginBottom: '1.5rem' }}>
        Explanation prepared for {investorName}. Also shown on their portal.
      </p>

      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12, padding: '1.5rem',
      }}>
        <ol style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {points.map((p, i) => (
            <li key={i} style={{ display: 'flex', gap: 12 }}>
              <span style={{
                width: 22, height: 22, borderRadius: '50%',
                background: 'rgba(109,129,150,0.25)',
                color: '#a0b4c4', fontSize: 11, fontWeight: 600,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>{i + 1}</span>
              <p style={{ fontSize: 13, color: '#FFFFE3', lineHeight: 1.6 }}>{p}</p>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}

// ── Proposal Report (with print-to-PDF) ──────────────────────────────────────

type ProposalReportProps = {
  investorId?: string
  investorName?: string
  riskProfile?: string
  auditTrail?: { at: string; who: string; action: string }[]
}

export function ProposalReport({ investorId, investorName = 'Priya Desai', riskProfile = 'moderator', auditTrail }: ProposalReportProps) {
  const printRef = useRef<HTMLDivElement>(null)
  const { weights, source } = useAllocation(investorId, riskProfile)
  const metrics = useMemo(() => portfolioMetrics(weights), [weights])
  const trail = auditTrail ?? [
    { at: '2026-09-18 10:22', who: 'System', action: 'Optimizer generated draft allocation over 8-ETF universe' },
    { at: '2026-09-19 14:07', who: 'M. Iyer', action: 'Adjusted NIFTYBEES −3%, GOLDBEES +3%' },
    { at: '2026-09-20 09:41', who: 'M. Iyer', action: 'Approved final proposal' },
  ]

  function download() {
    const el = printRef.current
    if (!el) return
    const html = el.innerHTML
    const win = window.open('', '_blank', 'width=900,height=1000')
    if (!win) return
    win.document.write(`<!doctype html><html><head><title>Proposal — ${investorName}</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; color: #222; }
        h1 { font-size: 22px; margin-bottom: 4px; }
        h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #666; margin: 24px 0 8px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; }
        th { color: #666; font-weight: 500; text-transform: uppercase; font-size: 11px; letter-spacing: 0.08em; }
        p { font-size: 13px; line-height: 1.6; }
        .muted { color: #666; }
      </style></head><body>${html}</body></html>`)
    win.document.close()
    win.focus()
    setTimeout(() => win.print(), 400)
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 900 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3' }}>Proposal</h1>
            <SourceBadge source={source} />
          </div>
          <p style={{ fontSize: 13, color: '#CBCBCB', marginTop: 4 }}>Generated on approval · one-click PDF download.</p>
        </div>
        <button onClick={download} style={btnPrimary}>Download PDF</button>
      </div>

      <div ref={printRef} style={{ background: '#FFFFE3', color: '#4A4A4A', borderRadius: 12, padding: '2rem' }}>
        <h1 style={{ fontSize: 22, marginBottom: 4 }}>Portfolio Proposal</h1>
        <p style={{ fontSize: 13, color: '#666' }}>
          {investorName} · risk profile <span style={{ fontFamily: 'monospace' }}>{riskProfile}</span> ·
          prepared {new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
        </p>

        <h2 style={sectionHead}>Recommended Allocation (8-ETF universe)</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              <th style={th}>Ticker</th>
              <th style={th}>Name</th>
              <th style={th}>Category</th>
              <th style={{ ...th, textAlign: 'right' }}>Weight</th>
            </tr>
          </thead>
          <tbody>
            {ETFS.map(e => (
              <tr key={e.ticker}>
                <td style={{ ...td, fontFamily: 'monospace' }}>{e.ticker}</td>
                <td style={td}>{e.label}</td>
                <td style={{ ...td, color: '#666', textTransform: 'capitalize' }}>{e.category}</td>
                <td style={{ ...td, textAlign: 'right', fontFamily: 'monospace' }}>{(weights[e.ticker] ?? 0).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h2 style={sectionHead}>Key Metrics</h2>
        <p style={{ fontSize: 13, lineHeight: 1.6 }}>
          Expected annual return ~{metrics.expReturn.toFixed(1)}% ·
          Volatility ~{metrics.vol.toFixed(1)}% ·
          Sharpe ~{metrics.sharpe.toFixed(2)} (risk-free 5.5%). Estimates use per-ETF μ/σ; the optimizer snapshot supplies the full covariance-based figures when available.
        </p>

        <h2 style={sectionHead}>Rationale</h2>
        <p style={{ fontSize: 13, lineHeight: 1.6 }}>
          Allocation aligned with the investor&apos;s stated horizon and {riskProfile} risk score. Weights balance long-term growth (NIFTYBEES, JUNIORBEES) with sector diversification (BANKBEES, ITBEES, PHARMABEES), income (SETF10GILT), inflation hedge (GOLDBEES) and liquidity (LIQUIDBEES). Sector exclusions have been applied to the equity sleeve.
        </p>

        <h2 style={sectionHead}>Audit trail</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <tbody>
            {trail.map((t, i) => (
              <tr key={i}>
                <td style={{ ...td, color: '#666', fontFamily: 'monospace', fontSize: 12, width: 160 }}>{t.at}</td>
                <td style={{ ...td, width: 100 }}>{t.who}</td>
                <td style={td}>{t.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Drift Alerts ─────────────────────────────────────────────────────────────

type DriftAlertsProps = {
  investors: Investor[]
  onOpen: (id: string) => void
}

export function DriftAlerts({ investors, onOpen }: DriftAlertsProps) {
  const drivers = [
    'NIFTYBEES overweight vs target',
    'GOLDBEES underweight vs target',
    'LIQUIDBEES drift +6.1%',
    'BANKBEES underweight vs target',
    'SETF10GILT overweight vs target',
  ]
  const alerts = investors.slice(0, 5).map((inv, i) => ({
    investor: inv,
    drift: 5.4 + i * 1.7,
    driver: drivers[i % drivers.length],
    since: `${3 + i} days`,
  }))

  return (
    <div style={{ padding: '2rem', maxWidth: 900 }}>
      <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 6 }}>Drift Alerts</h1>
      <p style={{ fontSize: 13, color: '#CBCBCB', marginBottom: '1.5rem' }}>Portfolios with allocation drift &gt; 5% from approved targets.</p>

      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12,
      }}>
        {alerts.length === 0 && (
          <p style={{ padding: '1.5rem', fontSize: 13, color: '#CBCBCB' }}>No drift alerts at this time.</p>
        )}
        {alerts.map(a => (
          <div key={a.investor.id} style={{
            display: 'grid', gridTemplateColumns: '2fr 1fr 2fr 1fr auto',
            padding: '14px 16px', gap: 12, alignItems: 'center',
            borderBottom: '0.5px solid rgba(203,203,203,0.08)',
          }}>
            <span style={{ fontSize: 13, color: '#FFFFE3' }}>{a.investor.name}</span>
            <span style={{ fontSize: 13, color: a.drift > 8 ? '#F09595' : '#EF9F27', fontFamily: 'monospace' }}>{a.drift.toFixed(1)}%</span>
            <span style={{ fontSize: 12, color: '#CBCBCB' }}>{a.driver}</span>
            <span style={{ fontSize: 12, color: '#6D8196' }}>since {a.since}</span>
            <button onClick={() => onOpen(a.investor.id)} style={btnGhost}>Review</button>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Audit Log ────────────────────────────────────────────────────────────────

export function AuditLog({ investors }: { investors: Investor[] }) {
  const entries = investors.slice(0, 8).flatMap((inv, i) => [
    { at: '2026-09-18 09:00', who: 'System', action: 'Proposal generated over 8-ETF universe', investor: inv.name },
    { at: '2026-09-19 15:22', who: i % 2 ? 'M. Iyer' : 'A. Rao', action: i % 3 === 0 ? 'Weights adjusted' : 'Proposal approved', investor: inv.name },
  ])

  return (
    <div style={{ padding: '2rem', maxWidth: 1000 }}>
      <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 6 }}>Audit Log</h1>
      <p style={{ fontSize: 13, color: '#CBCBCB', marginBottom: '1.5rem' }}>Every approval, edit, and rejection — searchable trail.</p>

      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12,
      }}>
        {entries.map((e, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '160px 120px 1fr 1fr',
            padding: '10px 16px', gap: 12,
            borderBottom: '0.5px solid rgba(203,203,203,0.08)',
            fontSize: 12,
          }}>
            <span style={{ color: '#6D8196', fontFamily: 'monospace' }}>{e.at}</span>
            <span style={{ color: '#a0b4c4' }}>{e.who}</span>
            <span style={{ color: '#FFFFE3' }}>{e.action}</span>
            <span style={{ color: '#CBCBCB' }}>{e.investor}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Investor Portal (read-only) ──────────────────────────────────────────────

export function InvestorPortalView({ investor }: { investor?: Investor | null }) {
  const { weights, source } = useAllocation(investor?.id, investor?.risk_score)
  const metrics = useMemo(() => portfolioMetrics(weights), [weights])

  return (
    <div style={{ padding: '2rem', maxWidth: 900 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3' }}>Investor Portal</h1>
        <SourceBadge source={source} />
      </div>
      <p style={{ fontSize: 13, color: '#CBCBCB', marginBottom: '1.5rem' }}>
        Read-only view for {investor?.name ?? 'the investor'}. Shows the latest approved 8-ETF allocation, metrics and rationale.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div style={{ background: 'rgba(255,255,227,0.06)', border: '0.5px solid rgba(203,203,203,0.15)', borderRadius: 12, padding: '1.25rem' }}>
          <p style={{ fontSize: 12, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Latest allocation</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {ETFS.map(a => {
              const w = weights[a.ticker] ?? 0
              return (
                <div key={a.ticker}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                    <span style={{ color: '#FFFFE3' }}>
                      <span style={{ fontFamily: 'monospace', color: '#a0b4c4' }}>{a.ticker}</span>
                      <span style={{ color: '#CBCBCB' }}> · {a.label}</span>
                    </span>
                    <span style={{ fontFamily: 'monospace', color: '#CBCBCB' }}>{w.toFixed(0)}%</span>
                  </div>
                  <div style={{ height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: w + '%', background: a.color }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,227,0.06)', border: '0.5px solid rgba(203,203,203,0.15)', borderRadius: 12, padding: '1.25rem' }}>
          <p style={{ fontSize: 12, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Key metrics</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <MetricBlock label="Expected return" value={metrics.expReturn.toFixed(1) + '%'} />
            <MetricBlock label="Volatility" value={metrics.vol.toFixed(1) + '%'} />
            <MetricBlock label="Sharpe" value={metrics.sharpe.toFixed(2)} />
            <MetricBlock label="Since inception" value="+8.3%" positive />
          </div>
        </div>
      </div>

      <div style={{ background: 'rgba(255,255,227,0.06)', border: '0.5px solid rgba(203,203,203,0.15)', borderRadius: 12, padding: '1.5rem' }}>
        <p style={{ fontSize: 12, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Why this allocation</p>
        <p style={{ fontSize: 13, color: '#FFFFE3', lineHeight: 1.7 }}>
          Your portfolio spreads across a broad-market anchor (NIFTYBEES), a mid-cap tilt (JUNIORBEES) and three sector sleeves
          (BANKBEES, ITBEES, PHARMABEES). GOLDBEES and SETF10GILT reduce equity drawdowns and add inflation and duration hedges.
          LIQUIDBEES holds enough cash for near-term needs and opportunistic rebalancing.
        </p>
      </div>
    </div>
  )
}

// ── shared bits ──────────────────────────────────────────────────────────────

function MetricBlock({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div>
      <p style={{ fontSize: 10, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
      <p style={{ fontSize: 20, color: positive ? '#97C459' : '#FFFFE3', fontFamily: 'monospace' }}>{value}</p>
    </div>
  )
}

function SourceBadge({ source }: { source: 'defaults' | 'optimizer' }) {
  const isOpt = source === 'optimizer'
  return (
    <span style={{
      fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em',
      padding: '4px 8px', borderRadius: 4,
      background: isOpt ? 'rgba(151,196,89,0.15)' : 'rgba(203,203,203,0.12)',
      color: isOpt ? '#97C459' : '#CBCBCB',
    }}>
      {isOpt ? 'From optimizer' : 'Profile defaults'}
    </span>
  )
}

const th = { textAlign: 'left' as const, padding: '8px 10px', borderBottom: '1px solid #ddd', color: '#666', fontSize: 11, textTransform: 'uppercase' as const, letterSpacing: '0.08em', fontWeight: 500 }
const td = { padding: '8px 10px', borderBottom: '1px solid #eee' }
const sectionHead = { fontSize: 12, textTransform: 'uppercase' as const, letterSpacing: '0.08em', color: '#666', margin: '24px 0 8px' }

const btnPrimary = {
  padding: '8px 14px',
  fontSize: 12,
  fontWeight: 600,
  borderRadius: 6,
  border: 'none',
  background: '#FFFFE3',
  color: '#4A4A4A',
  cursor: 'pointer',
} as const

const btnGhost = {
  padding: '7px 12px',
  fontSize: 12,
  borderRadius: 6,
  background: 'transparent',
  border: '1px solid rgba(203,203,203,0.3)',
  color: '#FFFFE3',
  cursor: 'pointer',
} as const
