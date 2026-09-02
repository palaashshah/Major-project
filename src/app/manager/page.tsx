'use client'
import { useState, useEffect } from 'react'
import { getInvestors } from '@/lib/api'
import StatCard from '@/components/dashboard/StatCard'
import AUMSplitChart from '@/components/dashboard/AUMSplitChart'
import PerformanceChart from '@/components/dashboard/PerformanceChart'

type Investor = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
  assigned_manager_id?: string
}

export default function ManagerDashboard() {
  const [investors, setInvestors] = useState<Investor[]>([])

  useEffect(() => {
    async function fetchData() {
      const data = await getInvestors()
      setInvestors(data)
    }
    fetchData()
  }, [])

  // total AUM across all investors
  const totalAUM = investors.reduce((sum, inv) => sum + (inv.total_aum ?? 0), 0)

  return (
    <div style={{ flex: 1, background: '#4A4A4A' }}>

      
      {/* ── main content ── */}
      <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}></div>
        <h1 style={{ fontSize: '22px', fontWeight: 500, color: '#FFFFE3', marginBottom: '2rem' }}>Dashboard</h1>

        {/* stat cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '2rem' }}>
          <StatCard label="Total clients" value={String(investors.length)} />
          <StatCard label="Total AUM" value={'₹' + totalAUM.toLocaleString('en-IN')} />
          <StatCard label="Total gain" value="₹12,40,000" trend="+8.3%" positive={true} />
          <StatCard label="Pending review" value="3" />
        </div>

        {/* charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '2rem' }}>
          <AUMSplitChart />
          <PerformanceChart />
        </div>
      </div>
    </div>
  )
}

// 'use client'
// import { useState, useEffect } from 'react'
// import { useRouter } from 'next/navigation'
// import {getInvestors} from "@/lib/api"

// // define a TypeScript type for Investor
// type Investor = {
//   id: string
//   name: string
//   risk_score?: string
//   total_aum?: number
//   investment_horizon?: string
// }

// export default function ManagerDashboard() {
//   const router = useRouter()
//   const [investors, setInvestors] = useState<Investor[]>([])

//   useEffect(() => {
//     // anything here runs automatically when the component loads
//     // define an async function inside
//     async function fetchData() {
//         const data = await getInvestors()  // wait for the API
//         setInvestors(data)                  // then store it
//     }
//     fetchData()  // call it immediately
//     }, [])  // empty [] = run once on page load

//   return (
//     <div>
//       <h1>Manager Dashboard</h1>
//       <table>
//         <thead>
//           <tr>
//             <th>Name</th>
//             <th>Risk Score</th>
//             <th>Assets Under Management</th>
//             <th>Time Horizon</th>
//           </tr>
//         </thead>
//         <tbody>
//           {/* map over investors here, one <tr> per investor */}
//           {investors.map((investor) => (
//             <tr key={investor.id} onClick={() => router.push('/manager/' + investor.id)}>
//               <td>{investor.name}</td>
//               <td>{investor.risk_score}</td>
//               <td>{investor.total_aum}</td>
//               <td>{investor.investment_horizon}</td>
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   )
// }