'use client'
import { useState, useEffect } from 'react'
import { getInvestors } from '@/lib/api'
import InvestorCard from '@/components/dashboard/InvestorCard'

type Investor = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
  assigned_manager_id?: string
}

export default function InvestorPage(){

    const [search, setSearch] = useState('')
    const [investors, setInvestors] = useState<Investor[]>([])
    useEffect(() => {
        async function fetchData() {
        const data = await getInvestors()
        setInvestors(data)
        }
        fetchData()
    }, [])

    const filtered = investors.filter(inv =>
        inv.name.toLowerCase().includes(search.toLowerCase()) ||
        inv.risk_score?.toLowerCase().includes(search.toLowerCase())
    )
    const [loading, setLoading] = useState(true)
    useEffect(() => {
    async function fetchData() {
        const data = await getInvestors()
        setInvestors(data)
        setLoading(false)  // ← turn off loading when done
    }
    fetchData()
    }, [])

    if (loading) return (
    <div style={{ flex: 1, background: '#4A4A4A', padding: '2rem' }}>
        <p style={{ color: '#CBCBCB', fontSize: '13px' }}>Loading investors...</p>
    </div>
    )
    return (
        <div style={{ flex: 1, background: '#4A4A4A' }}>
            <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>

                {/* topbar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '22px', fontWeight: 500, color: '#FFFFE3' }}>Investors</h1>
                <input
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search by name or risk profile..."
                    style={{
                    background: 'rgba(255,255,227,0.07)',
                    border: '0.5px solid rgba(203,203,203,0.25)',
                    borderRadius: '8px', padding: '8px 14px',
                    fontSize: '13px', color: '#FFFFE3', width: '240px', outline: 'none',
                    }}
                />
                </div>

                {/* investor cards grid */}
                <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
                    All clients
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '14px' }}>
                    {filtered.map(inv => (
                    <InvestorCard key={inv.id} {...inv} />
                    ))}
                </div>
            </div>
        </div>
    )
}