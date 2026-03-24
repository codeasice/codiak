import { useAccountSummary } from '../../hooks/dragon-keeper/use-account-summary'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function CardSkeleton() {
  return (
    <div style={{
      padding: '20px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
    }}>
      <div style={{
        width: '100px', height: '12px', background: 'var(--bg-hover)',
        borderRadius: '4px', marginBottom: '12px',
      }} />
      <div style={{
        width: '140px', height: '28px', background: 'var(--bg-hover)',
        borderRadius: '6px', marginBottom: '8px',
      }} />
      <div style={{
        width: '80px', height: '10px', background: 'var(--bg-hover)',
        borderRadius: '4px',
      }} />
    </div>
  )
}

interface SummaryCardProps {
  label: string
  amount: number
  subtitle?: string
  color?: string
}

function SummaryCard({ label, amount, subtitle, color = 'var(--text-primary)' }: SummaryCardProps) {
  return (
    <div style={{
      padding: '20px',
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
    }}>
      <div style={{
        fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '8px',
      }}>
        {label}
      </div>
      <div style={{
        fontSize: '24px', fontWeight: 700, color, lineHeight: 1.2,
        marginBottom: subtitle ? '4px' : '0',
      }}>
        {formatCurrency(amount)}
      </div>
      {subtitle && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {subtitle}
        </div>
      )}
    </div>
  )
}

export default function FinancialSummaryCards() {
  const { data, isLoading, isError } = useAccountSummary()

  if (isLoading) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div style={{
        padding: '16px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '13px',
      }}>
        Unable to load account data.
      </div>
    )
  }

  if (!data.has_data) return null

  const checkingSubtitle = data.checking.accounts.length === 1
    ? data.checking.accounts[0].name
    : `${data.checking.accounts.length} accounts`

  const ccSubtitle = data.credit_cards.accounts.length === 1
    ? data.credit_cards.accounts[0].name
    : `${data.credit_cards.accounts.length} cards`

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
      <SummaryCard
        label="Checking Balance"
        amount={data.checking.total}
        subtitle={checkingSubtitle}
      />
      <SummaryCard
        label="Credit Card Debt"
        amount={data.credit_cards.total}
        subtitle={ccSubtitle}
        color="var(--danger)"
      />
      <SummaryCard
        label="Pending Bills"
        amount={data.pending_bills.total}
        subtitle={`${data.pending_bills.count} transactions · ${data.pending_bills.timeframe}`}
        color="var(--warning)"
      />
    </div>
  )
}
