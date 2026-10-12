'use client'
import { useEffect, useMemo, useState } from 'react'
import { getInvestors, getInteractions, getAllInteractions } from '@/lib/api'

import InvestorOnboarding from '@/components/InvestorOnboarding'
import KYCUpload from '@/components/kyc/KYCUpload'
import ReviewCustomization from '@/components/manager/ReviewCustomization'
import {
  SubmissionQueue,
  RationalePanel,
  ProposalReport,
  DriftAlerts,
  AuditLog,
  InvestorPortalView,
} from '@/components/manager/ManagerViews'

import StatCard from '@/components/dashboard/StatCard'
import AUMSplitChart from '@/components/dashboard/AUMSplitChart'
import PerformanceChart from '@/components/dashboard/PerformanceChart'
import InteractionList from '@/components/dashboard/InteractionList'
import LogInteractionForm from '@/components/dashboard/LogInteractionForm'
import EditProfileForm from '@/components/dashboard/EditProfileForm'

type Investor = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
  assigned_manager_id?: string
  demographics?: Record<string, unknown>
  preferences_constraints?: Record<string, unknown>
}

type Interaction = {
  id: string
  investor_id: string
  timestamp?: string
  interaction_type: string
  notes: string
  manager_id?: string
}

type ViewKey =
  | 'dashboard'
  | 'onboarding'
  | 'kyc'
  | 'submissions'
  | 'investors'
  | 'investor-detail'
  | 'review'
  | 'rationale'
  | 'proposal'
  | 'portal'
  | 'interactions'
  | 'drift'
  | 'audit'

type NavItem = { key: ViewKey; label: string }
type NavGroup = { title: string; items: NavItem[] }

const NAV: NavGroup[] = [
  {
    title: 'Overview',
    items: [{ key: 'dashboard', label: 'Dashboard' }],
  },
  {
    title: 'Client',
    items: [
      { key: 'onboarding', label: 'Investor Intake' },
      { key: 'kyc', label: 'KYC Verification' },
      { key: 'portal', label: 'Investor Portal' },
    ],
  },
  {
    title: 'Manager',
    items: [
      { key: 'submissions', label: 'Submission Queue' },
      { key: 'investors', label: 'Investors' },
      { key: 'review', label: 'Review & Customize' },
      { key: 'rationale', label: 'Rationale' },
      { key: 'proposal', label: 'Proposal (PDF)' },
      { key: 'interactions', label: 'Interactions' },
      { key: 'drift', label: 'Drift Alerts' },
      { key: 'audit', label: 'Audit Log' },
    ],
  },
]

export default function AppShell() {
  const [activeView, setActiveView] = useState<ViewKey>('dashboard')
  const [investors, setInvestors] = useState<Investor[]>([])
  const [selectedInvestorId, setSelectedInvestorId] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    getInvestors().then((data) => setInvestors(Array.isArray(data) ? data : [])).catch(() => setInvestors([]))
  }, [])

  const selectedInvestor = useMemo(
    () => investors.find(i => i.id === selectedInvestorId) ?? null,
    [investors, selectedInvestorId]
  )

  function openInvestor(id: string) {
    setSelectedInvestorId(id)
    setActiveView('investor-detail')
  }

  function runOptimization(id: string) {
    setSelectedInvestorId(id)
    setActiveView('review')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#4A4A4A', color: '#FFFFE3' }}>
      {/* ── SIDEBAR ── */}
      <aside style={{
        width: 240, minWidth: 240,
        background: '#3a3a3a',
        borderRight: '0.5px solid rgba(203,203,203,0.15)',
        padding: '1.5rem 1rem',
        display: 'flex', flexDirection: 'column', gap: '1.5rem',
        position: 'sticky', top: 0, height: '100vh', overflowY: 'auto',
      }}>
        <div>
          <p style={{ fontSize: 15, fontWeight: 500, letterSpacing: '0.04em', color: '#FFFFE3' }}>
            Open<span style={{ color: '#6D8196' }}>Glass</span>
          </p>
          <p style={{ fontSize: 10, color: '#6D8196', letterSpacing: '0.12em', textTransform: 'uppercase', marginTop: 2 }}>
            Portfolio Management
          </p>
        </div>

        {NAV.map(group => (
          <div key={group.title}>
            <p style={{ fontSize: 10, color: '#6D8196', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8, paddingLeft: 8 }}>
              {group.title}
            </p>
            <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {group.items.map(item => {
                const active = activeView === item.key || (item.key === 'investors' && activeView === 'investor-detail')
                return (
                  <button
                    key={item.key}
                    onClick={() => setActiveView(item.key)}
                    style={{
                      textAlign: 'left', border: 'none', cursor: 'pointer',
                      padding: '7px 10px', borderRadius: 6, fontSize: 13,
                      color: active ? '#FFFFE3' : '#CBCBCB',
                      background: active ? 'rgba(109,129,150,0.28)' : 'transparent',
                    }}
                  >
                    {item.label}
                  </button>
                )
              })}
            </nav>
          </div>
        ))}
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main style={{ flex: 1, minWidth: 0, overflowY: 'auto', maxHeight: '100vh' }}>
        {activeView === 'dashboard' && <DashboardView investors={investors} onOpen={openInvestor} />}
        {activeView === 'onboarding' && <InvestorOnboarding />}
        {activeView === 'kyc' && <KYCUpload />}
        {activeView === 'submissions' && (
          <SubmissionQueue
            investors={investors}
            onOpen={openInvestor}
            onRunOptimization={runOptimization}
          />
        )}
        {activeView === 'investors' && (
          <InvestorList investors={investors} search={search} setSearch={setSearch} onOpen={openInvestor} />
        )}
        {activeView === 'investor-detail' && selectedInvestor && (
          <InvestorDetail
            investor={selectedInvestor}
            onEditReview={() => setActiveView('review')}
            onOpenProposal={() => setActiveView('proposal')}
          />
        )}
        {activeView === 'investor-detail' && !selectedInvestor && (
          <EmptyState message="No investor selected. Open one from the Investors or Submission Queue view." />
        )}
        {activeView === 'review' && (
          <ReviewCustomization
            investorId={selectedInvestor?.id}
            investorName={selectedInvestor?.name}
            riskProfile={selectedInvestor?.risk_score ?? 'moderator'}
          />
        )}
        {activeView === 'rationale' && (
          <RationalePanel
            investorId={selectedInvestor?.id}
            investorName={selectedInvestor?.name}
            riskProfile={selectedInvestor?.risk_score ?? 'moderator'}
          />
        )}
        {activeView === 'proposal' && (
          <ProposalReport
            investorId={selectedInvestor?.id}
            investorName={selectedInvestor?.name}
            riskProfile={selectedInvestor?.risk_score ?? 'moderator'}
          />
        )}
        {activeView === 'portal' && <InvestorPortalView investor={selectedInvestor} />}
        {activeView === 'interactions' && <AllInteractionsView investors={investors} />}
        {activeView === 'drift' && <DriftAlerts investors={investors} onOpen={openInvestor} />}
        {activeView === 'audit' && <AuditLog investors={investors} />}
      </main>
    </div>
  )
}

// ── Dashboard ────────────────────────────────────────────────────────────────

function DashboardView({ investors, onOpen }: { investors: Investor[]; onOpen: (id: string) => void }) {
  const totalAUM = investors.reduce((s, i) => s + (i.total_aum ?? 0), 0)

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: '1.5rem' }}>Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: '1.5rem' }}>
        <StatCard label="Total clients" value={String(investors.length)} />
        <StatCard label="Total AUM" value={'₹' + totalAUM.toLocaleString('en-IN')} />
        <StatCard label="Total gain" value="₹12,40,000" trend="+8.3%" positive={true} />
        <StatCard label="Pending review" value={String(Math.min(investors.length, 3))} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: '1.5rem' }}>
        <AUMSplitChart />
        <PerformanceChart />
      </div>

      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12, padding: '1.25rem',
      }}>
        <p style={{ fontSize: 12, color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Recent clients</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
          {investors.slice(0, 6).map(inv => (
            <button key={inv.id} onClick={() => onOpen(inv.id)} style={{
              textAlign: 'left', cursor: 'pointer', border: '0.5px solid rgba(203,203,203,0.15)',
              background: 'rgba(255,255,227,0.04)', borderRadius: 10, padding: '12px 14px', color: '#FFFFE3',
            }}>
              <p style={{ fontSize: 13, fontWeight: 500 }}>{inv.name}</p>
              <p style={{ fontSize: 11, color: '#CBCBCB', marginTop: 3, textTransform: 'capitalize' }}>
                {inv.risk_score ?? '—'} · {inv.investment_horizon ?? '—'}
              </p>
            </button>
          ))}
          {investors.length === 0 && <p style={{ fontSize: 13, color: '#CBCBCB' }}>No investors yet.</p>}
        </div>
      </div>
    </div>
  )
}

// ── Investors List (in-shell) ────────────────────────────────────────────────

function InvestorList({
  investors, search, setSearch, onOpen,
}: {
  investors: Investor[]
  search: string
  setSearch: (s: string) => void
  onOpen: (id: string) => void
}) {
  const filtered = investors.filter(inv =>
    inv.name.toLowerCase().includes(search.toLowerCase()) ||
    inv.risk_score?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3' }}>Investors</h1>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search name or risk profile…"
          style={{
            background: 'rgba(255,255,227,0.07)',
            border: '0.5px solid rgba(203,203,203,0.25)',
            borderRadius: 8, padding: '8px 14px',
            fontSize: 13, color: '#FFFFE3', width: 260, outline: 'none',
          }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
        {filtered.map(inv => (
          <button key={inv.id} onClick={() => onOpen(inv.id)} style={{
            textAlign: 'left', cursor: 'pointer', border: '0.5px solid rgba(203,203,203,0.15)',
            background: 'rgba(255,255,227,0.06)', borderRadius: 10, padding: '1rem', color: '#FFFFE3',
          }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: 'rgba(109,129,150,0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 500,
              }}>
                {inv.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div>
                <p style={{ fontSize: 13, fontWeight: 500 }}>{inv.name}</p>
                <p style={{ fontSize: 11, color: '#CBCBCB', textTransform: 'capitalize' }}>
                  {inv.risk_score ?? '—'}
                </p>
              </div>
            </div>
            <div style={{ marginTop: 12, fontSize: 11, color: '#CBCBCB' }}>
              AUM: <span style={{ fontFamily: 'monospace', color: '#FFFFE3' }}>
                {inv.total_aum ? '₹' + inv.total_aum.toLocaleString('en-IN') : '—'}
              </span>
            </div>
          </button>
        ))}
        {filtered.length === 0 && (
          <p style={{ fontSize: 13, color: '#CBCBCB' }}>No investors match your search.</p>
        )}
      </div>
    </div>
  )
}

// ── Investor Detail (router-free) ────────────────────────────────────────────

function InvestorDetail({
  investor,
  onEditReview,
  onOpenProposal,
}: {
  investor: Investor
  onEditReview: () => void
  onOpenProposal: () => void
}) {
  const [interactions, setInteractions] = useState<Interaction[]>([])

  useEffect(() => {
    getInteractions(investor.id).then(setInteractions).catch(() => setInteractions([]))
  }, [investor.id])

  const initials = investor.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'rgba(109,129,150,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 500, color: '#FFFFE3',
          }}>{initials}</div>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 4 }}>{investor.name}</h1>
            <p style={{ fontSize: 13, color: '#CBCBCB', textTransform: 'capitalize' }}>
              {investor.risk_score ?? '—'} · {investor.investment_horizon ?? '—'} horizon · Manager: {investor.assigned_manager_id ?? '—'}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={onEditReview} style={{
            padding: '8px 14px', fontSize: 12, borderRadius: 6, border: '1px solid rgba(203,203,203,0.3)',
            background: 'transparent', color: '#FFFFE3', cursor: 'pointer',
          }}>Review &amp; customize</button>
          <button onClick={onOpenProposal} style={{
            padding: '8px 14px', fontSize: 12, fontWeight: 600, borderRadius: 6, border: 'none',
            background: '#FFFFE3', color: '#4A4A4A', cursor: 'pointer',
          }}>Open proposal</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: '1.5rem' }}>
        <StatCard label="AUM" value={investor.total_aum ? '₹' + investor.total_aum.toLocaleString('en-IN') : '—'} />
        <StatCard label="Total gain" value="₹84,000" trend="+8.3%" positive={true} />
        <StatCard label="Horizon" value={investor.investment_horizon ?? '—'} />
        <StatCard label="Risk profile" value={investor.risk_score ?? '—'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: '1.5rem' }}>
        <AUMSplitChart />
        <PerformanceChart />
      </div>

      <InteractionList interactions={interactions} />

      <div style={{ marginTop: '1.5rem' }}>
        <LogInteractionForm investorId={investor.id} />
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <EditProfileForm investorId={investor.id} investor={investor} />
      </div>
    </div>
  )
}

// ── All interactions view (in-shell) ─────────────────────────────────────────

function AllInteractionsView({ investors }: { investors: Investor[] }) {
  const [interactions, setInteractions] = useState<Interaction[]>([])

  useEffect(() => {
    getAllInteractions().then((d) => setInteractions(Array.isArray(d) ? d : [])).catch(() => setInteractions([]))
  }, [])

  function nameFor(id: string) {
    return investors.find(i => i.id === id)?.name ?? 'Unknown'
  }

  function color(type: string) {
    const m: Record<string, string> = { call: '#6D8196', email: '#97C459', meeting: '#EF9F27' }
    return m[type?.toLowerCase()] ?? '#CBCBCB'
  }

  function fmt(ts?: string) {
    if (!ts) return '—'
    return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: '1.5rem' }}>Interactions</h1>
      <div style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: 12, padding: '1.25rem',
      }}>
        {interactions.length === 0 ? (
          <p style={{ fontSize: 13, color: '#CBCBCB' }}>No interactions logged yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {interactions.map(i => (
              <div key={i.id} style={{
                display: 'flex', gap: 12, alignItems: 'flex-start',
                paddingBottom: 10, borderBottom: '0.5px solid rgba(203,203,203,0.1)',
              }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color(i.interaction_type), marginTop: 5, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 12, color: '#6D8196', marginBottom: 2 }}>{nameFor(i.investor_id)}</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span style={{ fontSize: 13, fontWeight: 500, color: '#FFFFE3', textTransform: 'capitalize' }}>{i.interaction_type}</span>
                    <span style={{ fontSize: 11, color: '#CBCBCB' }}>{fmt(i.timestamp)}</span>
                  </div>
                  <p style={{ fontSize: 13, color: '#CBCBCB', lineHeight: 1.5 }}>{i.notes}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Empty ────────────────────────────────────────────────────────────────────

function EmptyState({ message }: { message: string }) {
  return (
    <div style={{ padding: '3rem', color: '#CBCBCB', fontSize: 14 }}>
      {message}
    </div>
  )
}
