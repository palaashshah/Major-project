// PerformanceChart.tsx — line + bar chart showing portfolio performance
// PLACEHOLDER — uses dummy data until optimizer is wired in

const MONTHS = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']

// dummy monthly return % values
const BAR_DATA = [2.1, -0.8, 3.4, 1.2, -1.5, 4.1, 2.8]

// dummy cumulative performance line
const LINE_DATA = [100, 102.1, 101.3, 104.7, 105.9, 104.4, 108.5, 111.3]

export default function PerformanceChart() {
  const W = 420
  const H = 140
  const PAD = { top: 10, right: 10, bottom: 24, left: 32 }
  const chartW = W - PAD.left - PAD.right
  const chartH = H - PAD.top - PAD.bottom

  // bar chart helpers
  const barMax = Math.max(...BAR_DATA.map(Math.abs))
  const barW = chartW / BAR_DATA.length - 4
  const zeroY = PAD.top + chartH / 2

  // line chart helpers — maps LINE_DATA to SVG points
  const linePoints = LINE_DATA.map((v, i) => {
    const x = PAD.left + (i / (LINE_DATA.length - 1)) * chartW
    const y = PAD.top + chartH - ((v - 98) / 16) * chartH
    return `${x},${y}`
  }).join(' ')

  return (
    <div style={{
      background: 'rgba(255,255,227,0.06)',
      border: '0.5px solid rgba(203,203,203,0.15)',
      borderRadius: '12px',
      padding: '1.25rem',
    }}>
      <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
        Performance <span style={{ color: '#6D8196', fontSize: '10px' }}>· placeholder</span>
      </p>

      <svg width="100%" viewBox={`0 0 ${W} ${H * 2 + 20}`}>

        {/* ── LINE CHART (cumulative) ── */}
        <text x={PAD.left} y={8} fontSize="10" fill="#CBCBCB">Cumulative return</text>

        {/* zero baseline */}
        <line x1={PAD.left} y1={zeroY} x2={W - PAD.right} y2={zeroY}
          stroke="rgba(203,203,203,0.15)" strokeWidth="0.5" />

        {/* line */}
        <polyline
          points={linePoints}
          fill="none"
          stroke="#6D8196"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />

        {/* dots on line */}
        {LINE_DATA.map((v, i) => {
          const x = PAD.left + (i / (LINE_DATA.length - 1)) * chartW
          const y = PAD.top + chartH - ((v - 98) / 16) * chartH
          return <circle key={i} cx={x} cy={y} r="2.5" fill="#6D8196" />
        })}

        {/* ── BAR CHART (monthly returns) ── */}
        <text x={PAD.left} y={H + 16} fontSize="10" fill="#CBCBCB">Monthly returns (%)</text>

        {BAR_DATA.map((v, i) => {
          const barH = (Math.abs(v) / barMax) * (chartH / 2 - 4)
          const x = PAD.left + i * (chartW / BAR_DATA.length) + 2
          const y = v >= 0
            ? H + PAD.top + 20 + chartH / 2 - barH
            : H + PAD.top + 20 + chartH / 2

          return (
            <g key={i}>
              <rect
                x={x} y={y}
                width={barW} height={barH}
                fill={v >= 0 ? '#97C459' : '#F09595'}
                rx="2"
                opacity="0.8"
              />
              <text
                x={x + barW / 2} y={H + PAD.top + 20 + chartH + 12}
                fontSize="9" fill="#CBCBCB" textAnchor="middle"
              >
                {MONTHS[i]}
              </text>
            </g>
          )
        })}

        {/* zero line for bar chart */}
        <line
          x1={PAD.left}
          y1={H + PAD.top + 20 + chartH / 2}
          x2={W - PAD.right}
          y2={H + PAD.top + 20 + chartH / 2}
          stroke="rgba(203,203,203,0.25)" strokeWidth="0.5"
        />
      </svg>
    </div>
  )
}