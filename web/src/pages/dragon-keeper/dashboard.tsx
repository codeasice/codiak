export default function DragonKeeperDashboard() {
  return (
    <div className="dk-dashboard">
      <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>
        Dragon Keeper
      </h2>
      <div style={{
        padding: '40px 20px',
        textAlign: 'center',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        color: 'var(--text-muted)',
        fontSize: '14px'
      }}>
        Dashboard widgets will appear here as they are built.
      </div>
    </div>
  )
}
