// AUMSplitChart.tsx — donut showing AUM split across the 8-ETF universe.
// When no data is passed, uses the moderator-profile default from lib/etfs.ts.
import { ETFS, defaultWeightsFor } from '@/lib/etfs'

type AUMSplitProps = {
  data?: { label: string; percentage: number; color: string }[]
}

const DEFAULT_DATA = (() => {
  const w = defaultWeightsFor('moderator')
  return ETFS.map(e => ({ label: e.ticker, percentage: w[e.ticker] ?? 0, color: e.color }))
})()

export default function AUMSplitChart({ data = DEFAULT_DATA }: AUMSplitProps) {
  const size = 120
  const radius = 45
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * radius

  return (
    <div style={{
      background: 'rgba(255,255,227,0.06)',
      border: '0.5px solid rgba(203,203,203,0.15)',
      borderRadius: '12px',
      padding: '1.25rem',
    }}>
      <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
        AUM Split <span style={{ color: '#6D8196', fontSize: '10px' }}>· 8-ETF universe</span>
      </p>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>

        {/* donut SVG */}
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ flexShrink: 0 }}>
          {data.map((segment, i) => {
            const dash = (segment.percentage / 100) * circumference
            const gap = circumference - dash

            // calculate this segment's start offset by summing all PREVIOUS segments
            // no variable mutation — derived cleanly from the data array itself
            const currentOffset = data
              .slice(0, i)
              .reduce((acc, s) => acc + (s.percentage / 100) * circumference, 0)

            return (
              <circle
                key={i}
                cx={cx} cy={cy} r={radius}
                fill="none"
                stroke={segment.color}
                strokeWidth="18"
                strokeDasharray={`${dash} ${gap}`}
                strokeDashoffset={-currentOffset}
                style={{ transform: 'rotate(-90deg)', transformOrigin: `${cx}px ${cy}px` }}
              />
            )
          })}
        </svg>

        {/* legend */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
          {data.map((segment, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: segment.color, flexShrink: 0 }} />
                <span style={{ fontSize: '12px', color: '#CBCBCB', fontFamily: 'monospace' }}>{segment.label}</span>
              </div>
              <span style={{ fontSize: '12px', fontWeight: 500, color: '#FFFFE3' }}>{segment.percentage}%</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}