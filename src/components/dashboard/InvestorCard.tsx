// InvestorCard.tsx — one investor card in the grid
// clicking it navigates to that investor's profile page

'use client'
import { useRouter } from 'next/navigation'

type InvestorCardProps = {
  id: string
  name: string
  risk_score?: string
  total_aum?: number
  investment_horizon?: string
}

// maps risk score string to a badge color
function getBadgeStyle(risk?: string) {
  const map: Record<string, { bg: string; color: string }> = {
    guardian:  { bg: 'rgba(109,129,150,0.2)', color: '#a0b4c4' },
    defender:  { bg: 'rgba(29,158,117,0.15)', color: '#5DCAA5' },
    moderator: { bg: 'rgba(109,129,150,0.2)', color: '#a0b4c4' },
    builder:   { bg: 'rgba(99,153,34,0.15)',  color: '#97C459' },
    explorer:  { bg: 'rgba(239,159,39,0.15)', color: '#EF9F27' },
  }
  return map[risk?.toLowerCase() ?? ''] ?? { bg: 'rgba(203,203,203,0.1)', color: '#CBCBCB' }
}

// gets initials from full name — "Palash Shah" → "PS"
function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

// formats AUM number → "₹1,00,00,000"
function formatAUM(aum?: number) {
  if (!aum) return '—'
  return '₹' + aum.toLocaleString('en-IN')
}

export default function InvestorCard({ id, name, risk_score, total_aum, investment_horizon }: InvestorCardProps) {
  const router = useRouter()
  const badge = getBadgeStyle(risk_score)

  return (
    <div
      onClick={() => router.push(`/manager/${id}`)}
      style={{
        background: 'rgba(255,255,227,0.06)',
        border: '0.5px solid rgba(203,203,203,0.15)',
        borderRadius: '12px',
        padding: '1.25rem',
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(109,129,150,0.6)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(203,203,203,0.15)')}
    >
      {/* initials avatar */}
      <div style={{
        width: '36px', height: '36px', borderRadius: '50%',
        background: 'rgba(109,129,150,0.3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '13px', fontWeight: 500, color: '#FFFFE3',
        marginBottom: '12px',
      }}>
        {getInitials(name)}
      </div>

      {/* name */}
      <p style={{ fontSize: '14px', fontWeight: 500, color: '#FFFFE3', marginBottom: '4px' }}>
        {name}
      </p>

      {/* horizon */}
      <p style={{ fontSize: '12px', color: '#CBCBCB', marginBottom: '14px' }}>
        {investment_horizon ? `${investment_horizon} horizon` : '—'}
      </p>

      {/* AUM */}
      <p style={{ fontSize: '18px', fontWeight: 500, color: '#FFFFE3', marginBottom: '2px' }}>
        {formatAUM(total_aum)}
      </p>
      <p style={{ fontSize: '11px', color: '#CBCBCB', marginBottom: '12px' }}>
        Assets under management
      </p>

      {/* risk badge */}
      <span style={{
        display: 'inline-block',
        padding: '3px 10px',
        borderRadius: '20px',
        fontSize: '11px',
        fontWeight: 500,
        background: badge.bg,
        color: badge.color,
      }}>
        {risk_score ?? 'Unassigned'}
      </span>
    </div>
  )
}