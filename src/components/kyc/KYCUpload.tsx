'use client'
import { useRef, useState } from 'react'

type DocKey = 'pan' | 'aadhaar' | 'address' | 'photo'
type DocStatus = 'idle' | 'uploading' | 'verifying' | 'verified' | 'rejected'

type DocState = {
  key: DocKey
  label: string
  required: boolean
  hint: string
  file: File | null
  status: DocStatus
  progress: number
  reason?: string
}

const INITIAL_DOCS: DocState[] = [
  { key: 'pan', label: 'PAN Card', required: true, hint: 'Clear scan of both sides (JPG/PNG/PDF, ≤5 MB)', file: null, status: 'idle', progress: 0 },
  { key: 'aadhaar', label: 'Aadhaar', required: true, hint: 'Front + back, mask first 8 digits if desired', file: null, status: 'idle', progress: 0 },
  { key: 'address', label: 'Address Proof', required: true, hint: 'Utility bill / bank statement (last 90 days)', file: null, status: 'idle', progress: 0 },
  { key: 'photo', label: 'Live Selfie', required: false, hint: 'For face-match verification', file: null, status: 'idle', progress: 0 },
]

function statusColor(s: DocStatus) {
  if (s === 'verified') return '#97C459'
  if (s === 'rejected') return '#F09595'
  if (s === 'verifying' || s === 'uploading') return '#EF9F27'
  return '#CBCBCB'
}

function statusLabel(s: DocStatus) {
  if (s === 'idle') return 'Not uploaded'
  if (s === 'uploading') return 'Uploading…'
  if (s === 'verifying') return 'Verifying…'
  if (s === 'verified') return 'Verified'
  if (s === 'rejected') return 'Rejected'
  return s
}

export default function KYCUpload() {
  const [docs, setDocs] = useState<DocState[]>(INITIAL_DOCS)
  const [submitted, setSubmitted] = useState(false)
  const inputRefs = useRef<Record<DocKey, HTMLInputElement | null>>({ pan: null, aadhaar: null, address: null, photo: null })

  function update(key: DocKey, patch: Partial<DocState>) {
    setDocs(prev => prev.map(d => (d.key === key ? { ...d, ...patch } : d)))
  }

  function pick(key: DocKey) {
    inputRefs.current[key]?.click()
  }

  function onFile(key: DocKey, file: File | null) {
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      update(key, { status: 'rejected', reason: 'File exceeds 5 MB', file: null, progress: 0 })
      return
    }
    update(key, { file, status: 'uploading', progress: 0, reason: undefined })

    let p = 0
    const uploadTick = setInterval(() => {
      p += 12
      if (p >= 100) {
        clearInterval(uploadTick)
        update(key, { status: 'verifying', progress: 100 })
        setTimeout(() => {
          const nameLower = file.name.toLowerCase()
          const looksSuspicious = nameLower.includes('fake') || nameLower.includes('test-reject')
          if (looksSuspicious) {
            update(key, { status: 'rejected', reason: 'Automated check flagged this document. Please re-upload a clearer copy.' })
          } else {
            update(key, { status: 'verified' })
          }
        }, 1200)
      } else {
        update(key, { progress: p })
      }
    }, 120)
  }

  const requiredDone = docs.filter(d => d.required).every(d => d.status === 'verified')
  const anyRejected = docs.some(d => d.status === 'rejected')

  if (submitted) {
    return (
      <div style={{ padding: '2rem', maxWidth: 720 }}>
        <div style={{
          width: 60, height: 60, borderRadius: '50%', border: '2px solid #97C459',
          color: '#97C459', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 26, marginBottom: 16,
        }}>✓</div>
        <h1 style={{ fontSize: 26, color: '#FFFFE3', marginBottom: 8 }}>KYC submitted for review</h1>
        <p style={{ fontSize: 14, color: '#CBCBCB', lineHeight: 1.6 }}>
          Your documents passed the automated checks. A compliance officer will complete the manual review within 1–2 business days.
        </p>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 860 }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, color: '#FFFFE3', marginBottom: 6 }}>KYC Verification</h1>
        <p style={{ fontSize: 13, color: '#CBCBCB' }}>Upload the following documents. Files are scanned automatically before manual review.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {docs.map(d => (
          <div key={d.key} style={{
            background: 'rgba(255,255,227,0.06)',
            border: '0.5px solid rgba(203,203,203,0.15)',
            borderRadius: 10,
            padding: '1rem 1.25rem',
            display: 'flex', gap: 16, alignItems: 'center',
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: 8,
              background: 'rgba(109,129,150,0.25)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#a0b4c4', fontSize: 18, flexShrink: 0,
            }}>📄</div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 14, color: '#FFFFE3', fontWeight: 500 }}>{d.label}</span>
                {d.required && (
                  <span style={{ fontSize: 10, color: '#F09595', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Required</span>
                )}
              </div>
              <p style={{ fontSize: 12, color: '#CBCBCB', marginTop: 2 }}>{d.hint}</p>

              {d.file && (
                <p style={{ fontSize: 11, color: '#a0b4c4', marginTop: 6, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {d.file.name} · {(d.file.size / 1024).toFixed(0)} KB
                </p>
              )}

              {(d.status === 'uploading' || d.status === 'verifying') && (
                <div style={{ marginTop: 8, height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: (d.status === 'verifying' ? 100 : d.progress) + '%',
                    background: statusColor(d.status),
                    transition: 'width 120ms linear',
                  }} />
                </div>
              )}

              {d.reason && (
                <p style={{ fontSize: 12, color: '#F09595', marginTop: 6 }}>{d.reason}</p>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end', minWidth: 130 }}>
              <span style={{
                fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em',
                color: statusColor(d.status),
              }}>
                {statusLabel(d.status)}
              </span>

              <input
                ref={el => { inputRefs.current[d.key] = el }}
                type="file"
                accept="image/*,application/pdf"
                style={{ display: 'none' }}
                onChange={e => onFile(d.key, e.target.files?.[0] ?? null)}
              />
              <button
                onClick={() => pick(d.key)}
                disabled={d.status === 'uploading' || d.status === 'verifying'}
                style={{
                  padding: '7px 14px',
                  fontSize: 12,
                  borderRadius: 6,
                  border: '1px solid rgba(203,203,203,0.3)',
                  background: 'transparent',
                  color: '#FFFFE3',
                  cursor: d.status === 'uploading' || d.status === 'verifying' ? 'not-allowed' : 'pointer',
                }}
              >
                {d.file ? 'Replace' : 'Upload'}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 12, color: anyRejected ? '#F09595' : '#CBCBCB' }}>
          {anyRejected ? 'Fix rejected documents before submitting.' : requiredDone ? 'All required documents verified.' : 'Upload all required documents to continue.'}
        </div>
        <button
          onClick={() => setSubmitted(true)}
          disabled={!requiredDone || anyRejected}
          style={{
            padding: '11px 22px',
            borderRadius: 8,
            border: 'none',
            background: !requiredDone || anyRejected ? 'rgba(255,255,255,0.1)' : '#FFFFE3',
            color: !requiredDone || anyRejected ? 'rgba(255,255,255,0.3)' : '#4A4A4A',
            fontSize: 13, fontWeight: 600,
            cursor: !requiredDone || anyRejected ? 'not-allowed' : 'pointer',
          }}
        >
          Submit for review
        </button>
      </div>

      <p style={{ marginTop: 20, fontSize: 11, color: '#6D8196', lineHeight: 1.6 }}>
        Try filenames containing &quot;fake&quot; or &quot;test-reject&quot; to trigger the rejection path.
      </p>
    </div>
  )
}
