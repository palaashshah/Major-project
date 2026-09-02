// AUMSplitChart.tsx — donut chart showing AUM split across asset classes
// PLACEHOLDER — uses dummy data until optimizer is wired in

type AUMSplitProps = {
  // optional real data — if not passed, shows placeholder
  data?: { label: string; percentage: number; color: string }[]
}

const PLACEHOLDER_DATA = [
  { label: 'Stocks',      percentage: 35, color: '#6D8196' },
  { label: 'Bonds',       percentage: 25, color: '#97C459' },
  { label: 'Real Estate', percentage: 15, color: '#5DCAA5' },
  { label: 'Commodities', percentage: 10, color: '#EF9F27' },
  { label: 'Crypto',      percentage: 10, color: '#a0b4c4' },
  { label: 'Currency',    percentage: 5,  color: '#F09595' },
]

export default function AUMSplitChart({ data = PLACEHOLDER_DATA }: AUMSplitProps) {
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
        AUM Split <span style={{ color: '#6D8196', fontSize: '10px' }}>· placeholder</span>
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
                <span style={{ fontSize: '12px', color: '#CBCBCB' }}>{segment.label}</span>
              </div>
              <span style={{ fontSize: '12px', fontWeight: 500, color: '#FFFFE3' }}>{segment.percentage}%</span>
            </div>
          ))}
        </div>

      </div>
    </div>
  )
}