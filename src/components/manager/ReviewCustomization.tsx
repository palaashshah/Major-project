'use client'
import { useEffect, useMemo, useState } from 'react'
import {
  ETFS,
  defaultWeightsFor,
  portfolioMetrics,
  checkConstraints,
} from '@/lib/etfs'
import { getOptimizedPortfolio } from '@/lib/api'

type Props = {
  investorId?: string
  investorName?: string
  riskProfile?: string
  onApprove?: (weights: Record<string, number>) => void
  onReject?: (reason: string) => void
}

export default function ReviewCustomization({
  investorId,
  investorName = 'Priya Desai',
  riskProfile = 'moderator',
  onApprove,
  onReject,
}: Props) {
  const defaults = useMemo(() => defaultWeightsFor(riskProfile), [riskProfile])
  const [weights, setWeights] = useState<Record<string, number>>(defaults)
  const [source, setSource] = useState<'defaults' | 'optimizer'>('defaults')
  const [loading, setLoading] = useState(false)
  const [decision, setDecision] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [rejectReason, setRejectReason] = useState('')

  // reset weights when the profile / investor changes
  useEffect(() => {
    setWeights(defaults)
    setSource('defaults')
  }, [defaults, investorId])

  // try the optimizer endpoint; fall back silently to the defaults above
  useEffect(() => {
    if (!investorId) return
    let cancelled = false
    setLoading(true)
    getOptimizedPortfolio(investorId)
      .then(result => {
        if (cancelled || !result) return
        setWeights(result.weights)
        setSource('optimizer')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [investorId])

  const total = ETFS.reduce((s, a) => s + (weights[a.ticker] ?? 0), 0)
  const metrics = useMemo(() => portfolioMetrics(weights), [weights])
  const violations = useMemo(() => checkConstraints(weights), [weights])
  const canApprove = violations.length === 0

  function setWeight(ticker: string, value: number) {
    setWeights(prev => ({ ...prev, [ticker]: value }))
  }

  function normalize() {
    const s = ETFS.reduce((sum, a) => sum + (weights[a.ticker] ?? 0), 0)
    if (s === 0) return
    const scaled = ETFS.reduce((acc, a) => {
      acc[a.ticker] = Math.round(((weights[a.ticker] ?? 0) / s) * 100)
      return acc
    }, {} as Record<string, number>)
    setWeights(scaled)
  }

  function reset() {
    setWeights(defaults)
    setSource('defaults')
  }

  if (decision === 'approved') {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={badge('#97C459')}>✓</div>
        <h1 style={{ fontSize: 24, color: '#FFFFE3', marginBottom: 8 }}>Proposal approved for {investorName}</h1>
        <p style={{ fontSize: 13, color: '#CBCBCB' }}>PDF proposal is available in the Proposal tab. Audit entry recorded.</p>
        <button onClick={() => setDecision('pending')} style={btnGhost}>Continue editing</button>
      </div>
    )
  }

  if (decision === 'rejected') {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={badge('#F09595')}>✕</div>
        <h1 style={{ fontSize: 24, color: '#FFFFE3', marginBottom: 8 }}>Proposal rejected for {investorName}</h1>
        <p style={{ fontSize: 13, color: '#CBCBCB', maxWidth: 500 }}>Reason: {rejectReason || '(no reason provided)'}</p>
        <button onClick={() => setDecision('pending')} style={btnGhost}>Back to review</button>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 1100 }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 4 }}>Review &amp; Customize</h1>
          <p style={{ fontSize: 13, color: '#CBCBCB' }}>
            Allocation for <span style={{ color: '#FFFFE3' }}>{investorName}</span> · risk profile
            <span style={{ color: '#a0b4c4', fontFamily: 'monospace', marginLeft: 6 }}>{riskProfile}</span>
          </p>
        </div>
        <span style={{
          fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em',
          padding: '4px 8px', borderRadius: 4,
          background: source === 'optimizer' ? 'rgba(151,196,89,0.15)' : 'rgba(203,203,203,0.12)',
          color: source === 'optimizer' ? '#97C459' : '#CBCBCB',
        }}>
          {loading ? 'Loading optimizer…' : source === 'optimizer' ? 'From optimizer' : 'Profile defaults'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16 }}>
        <div style={panel}>
          <p style={panelTitle}>Editable weights · 8 ETF universe</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {ETFS.map(a => {
              const w = weights[a.ticker] ?? 0
              return (
                <div key={a.ticker}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#FFFFE3' }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: a.color }} />
                      <span style={{ fontFamily: 'monospace', color: '#a0b4c4', fontSize: 12 }}>{a.ticker}</span>
                      <span style={{ color: '#CBCBCB', fontSize: 12 }}>· {a.label}</span>
                    </span>
                    <span style={{ fontSize: 12, color: '#CBCBCB', fontFamily: 'monospace' }}>{w.toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={60}
                    value={w}
                    onChange={e => setWeight(a.ticker, Number(e.target.value))}
                    style={{ width: '100%', accentColor: a.color }}
                  />
                  <p style={{ fontSize: 10, color: '#6D8196', marginTop: 2 }}>
                    {a.note} · μ {(a.expectedReturn * 100).toFixed(1)}% · σ {(a.vol * 100).toFixed(1)}%
                  </p>
                </div>
              )
            })}
          </div>

          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button onClick={normalize} style={btnGhost}>Normalize to 100</button>
            <button onClick={reset} style={btnGhost}>Reset to profile default</button>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={panel}>
            <p style={panelTitle}>Live metrics</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
              <Metric label="Expected return" value={metrics.expReturn.toFixed(2) + '%'} />
              <Metric label="Volatility" value={metrics.vol.toFixed(2) + '%'} />
              <Metric label="Sharpe" value={metrics.sharpe.toFixed(2)} tone={metrics.sharpe > 0.5 ? '#97C459' : '#EF9F27'} />
            </div>
            <p style={{ marginTop: 10, fontSize: 11, color: '#6D8196' }}>
              Sum of weights: {total.toFixed(1)}% · estimates assume ETFs are uncorrelated (real cov matrix comes from the optimizer snapshot).
            </p>
          </div>

          <div style={{
            background: violations.length ? 'rgba(240,149,149,0.08)' : 'rgba(151,196,89,0.08)',
            border: '0.5px solid ' + (violations.length ? 'rgba(240,149,149,0.35)' : 'rgba(151,196,89,0.35)'),
            borderRadius: 12, padding: '1.25rem',
          }}>
            <p style={{ fontSize: 12, color: violations.length ? '#F09595' : '#97C459', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              {violations.length ? `${violations.length} constraint violation${violations.length > 1 ? 's' : ''}` : 'All constraints satisfied'}
            </p>
            {violations.length ? (
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
                {violations.map(v => (
                  <li key={v} style={{ fontSize: 12, color: '#FFFFE3', paddingLeft: 12, position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 0, color: '#F09595' }}>•</span>
                    {v}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: 12, color: '#CBCBCB' }}>Ready to approve or send for adjustment.</p>
            )}
          </div>

          <div style={panel}>
            <p style={panelTitle}>Decision</p>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="Reason (required to reject)…"
              rows={2}
              style={{
                width: '100%', padding: '8px 10px', borderRadius: 6,
                background: 'rgba(255,255,255,0.06)', color: '#FFFFE3',
                border: '1px solid rgba(203,203,203,0.2)', fontSize: 12,
                outline: 'none', resize: 'vertical', marginBottom: 10,
              }}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => { onApprove?.(weights); setDecision('approved') }}
                disabled={!canApprove}
                style={{
                  flex: 1, padding: '10px 12px', fontSize: 12, borderRadius: 6,
                  background: canApprove ? '#97C459' : 'rgba(255,255,255,0.1)',
                  color: canApprove ? '#1c2a10' : 'rgba(255,255,255,0.3)',
                  border: 'none', fontWeight: 600,
                  cursor: canApprove ? 'pointer' : 'not-allowed',
                }}
              >
                Approve
              </button>
              <button
                onClick={() => { onReject?.(rejectReason); setDecision('rejected') }}
                disabled={!rejectReason.trim()}
                style={{
                  flex: 1, padding: '10px 12px', fontSize: 12, borderRadius: 6,
                  background: rejectReason.trim() ? '#F09595' : 'rgba(255,255,255,0.1)',
                  color: rejectReason.trim() ? '#2a1010' : 'rgba(255,255,255,0.3)',
                  border: 'none', fontWeight: 600,
                  cursor: rejectReason.trim() ? 'pointer' : 'not-allowed',
                }}
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value, tone = '#FFFFE3' }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p style={{ fontSize: 10, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
      <p style={{ fontSize: 20, color: tone, fontFamily: 'monospace' }}>{value}</p>
    </div>
  )
}

const panel = {
  background: 'rgba(255,255,227,0.06)',
  border: '0.5px solid rgba(203,203,203,0.15)',
  borderRadius: 12, padding: '1.25rem',
} as const

const panelTitle = {
  fontSize: 12, color: '#CBCBCB', textTransform: 'uppercase' as const, letterSpacing: '0.06em', marginBottom: 12,
}

const btnGhost = {
  padding: '7px 12px', fontSize: 12, borderRadius: 6,
  background: 'transparent', border: '1px solid rgba(203,203,203,0.3)',
  color: '#FFFFE3', cursor: 'pointer', marginTop: 20,
} as const

function badge(color: string) {
  return {
    width: 60, height: 60, borderRadius: '50%',
    border: `2px solid ${color}`, color,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 26, marginBottom: 16,
  } as const
}
