import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { useCategoryTimeline } from '../../hooks/dragon-keeper/use-charts'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatMonth(ym: string): string {
  const [y, m] = ym.split('-')
  const d = new Date(Number(y), Number(m) - 1)
  return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
}

interface CategoryChartProps {
  categoryId: string
}

export default function CategoryChart({ categoryId }: CategoryChartProps) {
  const { data, isLoading } = useCategoryTimeline(categoryId)
  const points = data?.points ?? []

  if (isLoading) {
    return (
      <div style={{
        height: '180px', background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center',
        justifyContent: 'center', color: 'var(--text-muted)', fontSize: '12px',
      }}>
        <div className="spinner" style={{ marginRight: '8px' }} />
        Loading chart...
      </div>
    )
  }

  if (points.length < 2) return null

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)', padding: '16px 20px',
    }}>
      <div style={{
        fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
        letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '12px',
      }}>
        Monthly Spending
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={points} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} vertical={false} />
          <XAxis dataKey="month" tickFormatter={formatMonth} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
          <YAxis tickFormatter={v => formatCurrency(v)} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={60} />
          <Tooltip
            formatter={(v: number) => formatCurrency(v)}
            labelFormatter={formatMonth}
            contentStyle={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: '8px', fontSize: '12px',
            }}
          />
          <Bar dataKey="total" fill="var(--accent)" radius={[4, 4, 0, 0]} name="Spending" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
