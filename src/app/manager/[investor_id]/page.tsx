'use client'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { getInvestor, getInteractions } from '@/lib/api'
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

// placeholder stock symbols until optimizer is wired in
const PLACEHOLDER_STOCKS = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'WIPRO']

function getInitials(name: string) {
  if (!name) return '—'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

export default function InvestorProfile() {
  const params = useParams()
  const investorId = params.investor_id as string

  const [investor, setInvestor] = useState<Investor | null>(null)
  const [interactions, setInteractions] = useState<Interaction[]>([])

  useEffect(() => {
    async function fetchData() {
      const inv = await getInvestor(investorId)
      setInvestor(inv)
      const ints = await getInteractions(investorId)
      setInteractions(ints)
    }
    fetchData()
  }, [investorId])

  return (
    <div style={{ flex: 1, background: '#4A4A4A' }}>

      {/* ── main content ── */}
      <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>

        {/* investor header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '2rem' }}>
          <div style={{
            width: '52px', height: '52px', borderRadius: '50%',
            background: 'rgba(109,129,150,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px', fontWeight: 500, color: '#FFFFE3',
          }}>
            {investor ? getInitials(investor.name) : '—'}
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 500, color: '#FFFFE3', marginBottom: '4px' }}>
              {investor?.name ?? 'Loading...'}
            </h1>
            <p style={{ fontSize: '13px', color: '#CBCBCB' }}>
              {investor?.risk_score} · {investor?.investment_horizon} horizon · Manager: {investor?.assigned_manager_id}
            </p>
          </div>
        </div>

        {/* stat cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '2rem' }}>
          <StatCard label="AUM" value={investor?.total_aum ? '₹' + investor.total_aum.toLocaleString('en-IN') : '—'} />
          <StatCard label="Total gain" value="₹84,000" trend="+8.3%" positive={true} />
          <StatCard label="Horizon" value={investor?.investment_horizon ?? '—'} />
          <StatCard label="Risk profile" value={investor?.risk_score ?? '—'} />
        </div>

        {/* charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '2rem' }}>
          <AUMSplitChart />
          <PerformanceChart />
        </div>

        {/* stock symbols placeholder */}
        <div style={{
          background: 'rgba(255,255,227,0.06)',
          border: '0.5px solid rgba(203,203,203,0.15)',
          borderRadius: '12px', padding: '1.25rem', marginBottom: '2rem',
        }}>
          <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
            Holdings <span style={{ color: '#6D8196', fontSize: '10px' }}>· placeholder</span>
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {PLACEHOLDER_STOCKS.map(symbol => (
              <span key={symbol} style={{
                padding: '4px 12px', borderRadius: '20px',
                background: 'rgba(109,129,150,0.2)',
                fontSize: '12px', fontWeight: 500, color: '#a0b4c4',
                fontFamily: 'monospace',
              }}>
                {symbol}
              </span>
            ))}
          </div>
        </div>

        {/* interaction history */}
        <InteractionList interactions={interactions} />
        <div style={{marginTop: '2rem'}}> 
          <LogInteractionForm investorId={investorId} />
        </div>
        <div style={{marginTop: '2rem'}}> 
          {investor && <EditProfileForm investorId={investorId} investor={investor} />}
        </div>
      </div>
    </div>
  )
}



// 'use client'
// import { useState, useEffect } from 'react'
// import { useParams } from 'next/navigation'
// import { getInteractions, getInvestor } from "@/lib/api"

// type Investor = {
//   id: string
//   name: string
//   risk_score?: string
//   total_aum?: number
//   investment_horizon?: string
// }

// type Interaction = {
//     id: string
//     investor_id: string
//     timestamp?: string
//     interaction_type: string
//     notes: string
//     manager_id?: string
// }

// export default function InvestorInfo(){

//     const [investor, setInvestor] = useState<Investor | null>(null)
//     const [interactions, setInteractions] = useState<Interaction[]>([])
    
//     const params = useParams()
//     const investorId = params.investor_id as string

//     useEffect(() => {
//     async function fetchData() {
//         // fetch investor AND interactions using investorId
//         const investor_data = await getInvestor(investorId)  // wait for the API
//         setInvestor(investor_data)

//         const interaction_data = await getInteractions(investorId)  // wait for the API
//         setInteractions(interaction_data)
//     }
//     fetchData()
//     }, [investorId])  // re-run if investorId changes
//     return (
//             <div>
//                 <h1>{investor?.name}</h1>
//                 <p>Risk Score: {investor?.risk_score}</p>
//                 <p>AUM: {investor?.total_aum}</p>
//                 <p>Horizon: {investor?.investment_horizon}</p>
//                 <h2>Interactions</h2>
//                 {interactions.map((i) => (
//                 <div key={i.id}>
//                     <p>{i.interaction_type} — {i.notes}</p>
//                 </div>
//                 ))}
//             </div>
//         )

// }