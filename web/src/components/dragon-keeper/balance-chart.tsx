import { useState } from 'react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { useBalanceHistory } from '../../hooks/dragon-keeper/use-charts'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatShortDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const CHART_COLORS = {
  checking: '#10b981',
  credit: '#ef4444',
  net: '#6366f1',
}

interface BalanceChartProps {
  onBack?: () => void
}

export default function BalanceChart({ onBack }: BalanceChartProps) {
  const [days, setDays] = useState(90)
  const { data, isLoading } = useBalanceHistory(days)
  const [series, setSeries] = useState<'net' | 'stacked'>('net')

  const points = data?.points ?? []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {onBack && (
        <button
          onClick={onBack}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--accent)', fontSize: '13px', fontWeight: 500,
            padding: 0, alignSelf: 'flex-start',
          }}
        >
          <span style={{ fontSize: '16px', lineHeight: 1 }}>&larr;</span>
          Dashboard
        </button>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Balance Over Time
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={series}
            onChange={e => setSeries(e.target.value as any)}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            <option value="net">Net Worth</option>
            <option value="stacked">By Account Type</option>
          </select>
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            {[30, 60, 90, 180, 365].map(d => (
              <option key={d} value={d}>{d} days</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px',
      }}>
        {isLoading ? (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginRight: '8px' }} />
            Loading chart data...
          </div>
        ) : points.length < 2 ? (
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center' }}>
            Not enough data yet. Balance snapshots are taken on each sync.<br />
            Sync a few more times to see your trend.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            {series === 'net' ? (
              <AreaChart data={points} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                <defs>
                  <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.net} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.net} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                <XAxis dataKey="snapshot_date" tickFormatter={formatShortDate} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                <YAxis tickFormatter={v => formatCurrency(v)} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} width={80} />
                <Tooltip
                  formatter={(v: number) => formatCurrency(v)}
                  labelFormatter={formatShortDate}
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="net_worth" stroke={CHART_COLORS.net} fill="url(#netGrad)" strokeWidth={2} name="Net Worth" />
              </AreaChart>
            ) : (
              <AreaChart data={points} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                <defs>
                  <linearGradient id="checkGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.checking} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.checking} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="creditGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.credit} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.credit} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                <XAxis dataKey="snapshot_date" tickFormatter={formatShortDate} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
                <YAxis tickFormatter={v => formatCurrency(v)} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} width={80} />
                <Tooltip
                  formatter={(v: number) => formatCurrency(v)}
                  labelFormatter={formatShortDate}
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="checking_total" stroke={CHART_COLORS.checking} fill="url(#checkGrad)" strokeWidth={2} name="Checking" />
                <Area type="monotone" dataKey="credit_total" stroke={CHART_COLORS.credit} fill="url(#creditGrad)" strokeWidth={2} name="Credit Cards" />
              </AreaChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
