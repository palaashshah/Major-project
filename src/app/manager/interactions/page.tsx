'use client'
import { useState, useEffect } from 'react'
import { getInvestors, getAllInteractions } from '@/lib/api'

type Interaction = {
  id: string
  investor_id: string
  timestamp?: string
  interaction_type: string
  notes: string
  manager_id?: string
}

type Investor = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
}

// maps interaction type to accent color
function getTypeColor(type: string) {
  const map: Record<string, string> = {
    call:    '#6D8196',
    email:   '#97C459',
    meeting: '#EF9F27',
  }
  return map[type?.toLowerCase()] ?? '#CBCBCB'
}

// formats ISO timestamp → readable date
function formatDate(ts?: string) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  })
}

export default function InteractionsHistory() {
  const [investors, setInvestors] = useState<Investor[]>([])
  const [interactions, setInteractions] = useState<Interaction[]>([])

  useEffect(() => {
    async function fetchData() {
      const ints = await getAllInteractions()
      const invs = await getInvestors()
      setInteractions(Array.isArray(ints) ? ints : [])
      setInvestors(invs)
    }
    fetchData()
  }, []) // ← empty array — run once on load only

  // finds investor name by matching investor_id
  function getInvestorName(investorId: string) {
    const investor = investors.find(inv => inv.id === investorId)
    return investor?.name ?? 'Unknown'
  }

  return (
    <div style={{ flex: 1, background: '#4A4A4A' }}>
      <div style={{ padding: '2rem' }}>

        <h1 style={{ fontSize: '22px', fontWeight: 500, color: '#FFFFE3', marginBottom: '2rem' }}>
          Interactions
        </h1>

        <div style={{
          background: 'rgba(255,255,227,0.06)',
          border: '0.5px solid rgba(203,203,203,0.15)',
          borderRadius: '12px',
          padding: '1.25rem',
        }}>
          <p style={{
            fontSize: '12px', color: '#CBCBCB',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            marginBottom: '1rem'
          }}>
            All interactions
          </p>

          {interactions.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#CBCBCB' }}>No interactions logged yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {interactions.map(i => (
                <div key={i.id} style={{
                  display: 'flex', gap: '12px', alignItems: 'flex-start',
                  paddingBottom: '10px',
                  borderBottom: '0.5px solid rgba(203,203,203,0.1)',
                }}>

                  {/* colored dot */}
                  <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: getTypeColor(i.interaction_type),
                    marginTop: '5px', flexShrink: 0,
                  }} />

                  <div style={{ flex: 1 }}>
                    {/* investor name */}
                    <p style={{ fontSize: '12px', color: '#6D8196', marginBottom: '2px' }}>
                      {getInvestorName(i.investor_id)}
                    </p>

                    {/* type + date */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <span style={{ fontSize: '13px', fontWeight: 500, color: '#FFFFE3', textTransform: 'capitalize' }}>
                        {i.interaction_type}
                      </span>
                      <span style={{ fontSize: '11px', color: '#CBCBCB' }}>
                        {formatDate(i.timestamp)}
                      </span>
                    </div>

                    {/* notes */}
                    <p style={{ fontSize: '13px', color: '#CBCBCB', lineHeight: 1.5 }}>
                      {i.notes}
                    </p>
                  </div>

                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}