// StatCard.tsx — a single metric tile (AUM, gain%, client count, etc.)
// accepts a label, value, and optional trend indicator

type StatCardProps = {
  label: string        // e.g. "Total AUM"
  value: string        // e.g. "₹4.2Cr" — already formatted before passing in
  trend?: string       // e.g. "+12.4%" — optional, shown in green/red
  positive?: boolean   // true = green trend, false = red trend
}

export default function StatCard({ label, value, trend, positive }: StatCardProps) {
  return (
    <div style={{
      background: 'rgba(255,255,227,0.06)',
      border: '0.5px solid rgba(203,203,203,0.15)',
      borderRadius: '8px',
      padding: '1rem',
    }}>
      {/* label — small muted text above */}
      <p style={{
        fontSize: '12px',
        color: '#CBCBCB',
        marginBottom: '6px',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}>
        {label}
      </p>

      {/* value — large number */}
      <p style={{
        fontSize: '22px',
        fontWeight: 500,
        color: '#FFFFE3',
        marginBottom: trend ? '4px' : '0',
      }}>
        {value}
      </p>

      {/* trend — optional gain/loss indicator */}
      {trend && (
        <p style={{
          fontSize: '12px',
          color: positive ? '#97C459' : '#F09595',  // green if positive, red if negative
          fontWeight: 500,
        }}>
          {trend}
        </p>
      )}
    </div>
  )
}