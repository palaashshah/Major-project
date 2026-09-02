'use client'
import { useState } from "react"
import { createInteraction } from '@/lib/api'

type LogInteractionFormProps = {
  investorId: string
}

export default function LogInteractionForm({ investorId }: LogInteractionFormProps) {
    const [interactiontype, setInteractiontype] = useState('')
    const [notes, setNotes] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    async function handleSubmit() {
        if (!interactiontype || !notes) return  // don't submit if fields are empty
        setIsLoading(true)
        await createInteraction({
            investor_id: investorId,
            interaction_type: interactiontype,
            notes,
            manager_id: 'manager-001',
        })
        setIsLoading(false)
        setInteractiontype('')
        setNotes('')
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
                Log Interaction
            </p>

            {/* type selector buttons */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem' }}>
                {['call', 'email', 'meeting'].map(type => (
                    <button
                        key={type}
                        onClick={() => setInteractiontype(type)}
                        style={{
                            padding: '6px 16px',
                            borderRadius: '20px',
                            border: '0.5px solid rgba(203,203,203,0.25)',
                            fontSize: '12px',
                            fontWeight: 500,
                            cursor: 'pointer',
                            textTransform: 'capitalize',
                            // highlight the selected type
                            background: interactiontype === type ? '#6D8196' : 'rgba(109,129,150,0.15)',
                            color: interactiontype === type ? '#FFFFE3' : '#CBCBCB',
                        }}
                    >
                        {type}
                    </button>
                ))}
            </div>

            {/* notes textarea */}
            <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Add notes..."
                rows={3}
                style={{
                    width: '100%',
                    background: 'rgba(255,255,227,0.05)',
                    border: '0.5px solid rgba(203,203,203,0.2)',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    fontSize: '13px',
                    color: '#FFFFE3',
                    resize: 'vertical',
                    outline: 'none',
                    marginBottom: '1rem',
                    boxSizing: 'border-box',  // prevents textarea from overflowing its container
                }}
            />

            {/* submit button */}
            <button
                onClick={handleSubmit}
                disabled={isLoading || !interactiontype || !notes}
                style={{
                    padding: '8px 20px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    background: isLoading ? 'rgba(109,129,150,0.3)' : '#6D8196',
                    color: '#FFFFE3',
                }}
            >
                {isLoading ? 'Submitting...' : 'Log Interaction'}
            </button>
        </div>
    )
}