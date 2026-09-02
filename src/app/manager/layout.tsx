'use client'
import { usePathname } from 'next/navigation';
import Link from 'next/link'

const navItems = [
  { name: 'Dashboard', href: '/manager' },
  { name: 'Investors', href: '/manager/investors' },
  { name: 'Interactions', href: '/manager/interactions' },
  { name: 'Reports', href: '/manager/reports' },
];

export default function ManagerLayout({ children }: { children: React.ReactNode }) {

    const pathname = usePathname()
    return (
        //   outer div with display:flex
        //   sidebar div (copy from page.tsx, but replace the hardcoded nav with navItems.map)
        //   <main> tag wrapping {children}
      <div style={{ display: 'flex', minHeight: '100vh' }}>
         
        <div style={{
          width: '220px', minWidth: '220px',
          background: '#3a3a3a',
          minHeight: '100vh',
          height: '100vh',        
          position: 'sticky',     
          top: 0,                
          padding: '2rem 1.25rem',
          borderRight: '0.5px solid rgba(203,203,203,0.15)',
          display: 'flex', flexDirection: 'column', gap: '2rem',
          overflowY: 'auto',
          }}>
          <p style={{ fontSize: '15px', fontWeight: 500, color: '#FFFFE3', letterSpacing: '0.04em' }}>
            Open<span style={{ color: '#6D8196' }}>Glass</span>
          </p>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {navItems.map(item => {
              const isActive = pathname === item.href
              return (
                <Link key={item.name} href={item.href} style={{ textDecoration: 'none' }}>
                  <div style={{
                    padding: '8px 12px', borderRadius: '6px', fontSize: '13px',
                    color: isActive ? '#FFFFE3' : '#CBCBCB',
                    background: isActive ? 'rgba(109,129,150,0.25)' : 'transparent',
                    cursor: 'pointer',
                  }}>
                    {item.name}
                  </div>
                </Link>
              )
            })}
          </nav>
        </div>
        <main style={{ flex: 1 }}>
          {children}
        </main>
      </div>
      
      )
}