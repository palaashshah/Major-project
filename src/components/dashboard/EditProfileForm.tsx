'use client'
import { useState } from "react"
import { updateInvestor } from '@/lib/api'

type EditProfileFormProps = {
  investorId: string
  investor: {
    name: string
    total_aum?: number
    investment_horizon?: string
    risk_score?: string
  }
}

// fixed valid options — dropdowns, not free text
const HORIZONS = ['short', 'medium', 'long', 'very_long']
const RISK_PROFILES = ['guardian', 'defender', 'moderator', 'builder', 'explorer']

export default function EditProfileForm({ investorId, investor }: EditProfileFormProps) {

  // pre-filled with current investor data from props
  const [name, setName] = useState(investor.name)
  const [totalaum, setTotalAum] = useState(investor.total_aum ?? 0)
  const [horizon, setHorizon] = useState(investor.investment_horizon ?? '')
  const [riskscore, setRiskScore] = useState(investor.risk_score ?? '')
  const [isLoading, setIsLoading] = useState(false)
  const [saved, setSaved] = useState(false) // shows a "Saved!" confirmation briefly

  async function handleSubmit() {
    if (!name) return // don't submit if name is empty
    setIsLoading(true)
    await updateInvestor(investorId, {
      name,
      total_aum: Number(totalaum),
      investment_horizon: horizon,
      risk_score: riskscore,
    })
    setIsLoading(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000) // hide "Saved!" after 2 seconds
  }

  return (
    <div style={{
      background: 'rgba(255,255,227,0.06)',
      border: '0.5px solid rgba(203,203,203,0.15)',
      borderRadius: '12px',
      padding: '1.25rem',
      marginBottom: '1.5rem',
    }}>
      {/* section label */}
      <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
        Edit Profile
      </p>

      {/* name field */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '12px', color: '#CBCBCB', display: 'block', marginBottom: '6px' }}>Name</label>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          style={{
            width: '100%', boxSizing: 'border-box',
            background: 'rgba(255,255,227,0.05)',
            border: '0.5px solid rgba(203,203,203,0.2)',
            borderRadius: '8px', padding: '8px 12px',
            fontSize: '13px', color: '#FFFFE3', outline: 'none',
          }}
        />
      </div>

      {/* AUM field */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '12px', color: '#CBCBCB', display: 'block', marginBottom: '6px' }}>Assets Under Management (₹)</label>
        <input
          type="number"
          value={totalaum}
          onChange={e => setTotalAum(Number(e.target.value))}
          style={{
            width: '100%', boxSizing: 'border-box',
            background: 'rgba(255,255,227,0.05)',
            border: '0.5px solid rgba(203,203,203,0.2)',
            borderRadius: '8px', padding: '8px 12px',
            fontSize: '13px', color: '#FFFFE3', outline: 'none',
          }}
        />
      </div>

      {/* horizon dropdown */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ fontSize: '12px', color: '#CBCBCB', display: 'block', marginBottom: '6px' }}>Investment Horizon</label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {HORIZONS.map(h => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              style={{
                padding: '6px 14px', borderRadius: '20px', border: '0.5px solid rgba(203,203,203,0.25)',
                fontSize: '12px', fontWeight: 500, cursor: 'pointer', textTransform: 'capitalize',
                // highlight selected
                background: horizon === h ? '#6D8196' : 'rgba(109,129,150,0.15)',
                color: horizon === h ? '#FFFFE3' : '#CBCBCB',
              }}
            >
              {h.replace('_', ' ')} {/* very_long → very long */}
            </button>
          ))}
        </div>
      </div>

      {/* risk score dropdown */}
      <div style={{ marginBottom: '1.25rem' }}>
        <label style={{ fontSize: '12px', color: '#CBCBCB', display: 'block', marginBottom: '6px' }}>Risk Profile</label>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {RISK_PROFILES.map(r => (
            <button
              key={r}
              onClick={() => setRiskScore(r)}
              style={{
                padding: '6px 14px', borderRadius: '20px', border: '0.5px solid rgba(203,203,203,0.25)',
                fontSize: '12px', fontWeight: 500, cursor: 'pointer', textTransform: 'capitalize',
                background: riskscore === r ? '#6D8196' : 'rgba(109,129,150,0.15)',
                color: riskscore === r ? '#FFFFE3' : '#CBCBCB',
              }}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* save button */}
      <button
        onClick={handleSubmit}
        disabled={isLoading || !name}
        style={{
          padding: '8px 20px', borderRadius: '8px', border: 'none',
          fontSize: '13px', fontWeight: 500,
          cursor: isLoading ? 'not-allowed' : 'pointer',
          background: saved ? '#97C459' : isLoading ? 'rgba(109,129,150,0.3)' : '#6D8196',
          color: '#FFFFE3',
          transition: 'background 0.2s',
        }}
      >
        {saved ? 'Saved ✓' : isLoading ? 'Saving...' : 'Save changes'}
      </button>
    </div>
  )
}