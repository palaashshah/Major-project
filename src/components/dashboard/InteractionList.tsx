// InteractionList.tsx — shows all logged interactions for one investor

type Interaction = {
  id: string
  interaction_type: string
  notes: string
  timestamp?: string
  manager_id?: string
}

type InteractionListProps = {
  interactions: Interaction[]
}

// maps interaction type to an accent color
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

export default function InteractionList({ interactions }: InteractionListProps) {
  return (
    <div style={{
      background: 'rgba(255,255,227,0.06)',
      border: '0.5px solid rgba(203,203,203,0.15)',
      borderRadius: '12px',
      padding: '1.25rem',
    }}>
      <p style={{ fontSize: '12px', color: '#CBCBCB', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '1rem' }}>
        Interaction history
      </p>

      {interactions.length === 0 ? (
        <p style={{ fontSize: '13px', color: '#CBCBCB' }}>No interactions logged yet.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {interactions.map((interaction) => (
            <div key={interaction.id} style={{
              display: 'flex', gap: '12px', alignItems: 'flex-start',
              paddingBottom: '10px',
              borderBottom: '0.5px solid rgba(203,203,203,0.1)',
            }}>
              {/* type dot */}
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: getTypeColor(interaction.interaction_type),
                marginTop: '5px', flexShrink: 0,
              }} />

              <div style={{ flex: 1 }}>
                {/* type + date */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 500, color: '#FFFFE3', textTransform: 'capitalize' }}>
                    {interaction.interaction_type}
                  </span>
                  <span style={{ fontSize: '11px', color: '#CBCBCB' }}>
                    {formatDate(interaction.timestamp)}
                  </span>
                </div>
                {/* notes */}
                <p style={{ fontSize: '13px', color: '#CBCBCB', lineHeight: 1.5 }}>
                  {interaction.notes}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}