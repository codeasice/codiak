/**
 * Clickable payee name that navigates to Transaction Explorer filtered to that payee.
 * Used throughout Dragon Keeper to make payee names universally explorable.
 */

interface PayeeLinkProps {
  payee: string
  onNavigate: (payee: string) => void
  style?: React.CSSProperties
}

export default function PayeeLink({ payee, onNavigate, style }: PayeeLinkProps) {
  return (
    <span
      onClick={(e) => { e.stopPropagation(); onNavigate(payee) }}
      style={{
        cursor: 'pointer',
        borderBottom: '1px dashed var(--text-muted)',
        fontWeight: 500,
        color: 'var(--text-primary)',
        ...style,
      }}
      onMouseEnter={e => {
        e.currentTarget.style.color = 'var(--accent)'
        e.currentTarget.style.borderColor = 'var(--accent)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.color = style?.color ?? 'var(--text-primary)'
        e.currentTarget.style.borderColor = 'var(--text-muted)'
      }}
      title={`View all transactions for ${payee}`}
    >
      {payee}
    </span>
  )
}
