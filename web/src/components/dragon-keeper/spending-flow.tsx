import { useState, useMemo } from 'react'
import { useSpendingFlow, type SankeyNode, type SankeyLink } from '../../hooks/dragon-keeper/use-charts'

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatMonthLabel(ym: string): string {
  const [y, m] = ym.split('-')
  const d = new Date(Number(y), Number(m) - 1)
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

const COLUMN_COLORS = [
  ['#6366f1', '#818cf8'],  // Groups: indigo
  ['#ec4899', '#f472b6'],  // Categories: pink
  ['#f59e0b', '#fbbf24'],  // Payees: amber
]

/* ---- Sankey layout engine ---- */

interface LayoutNode {
  id: string
  name: string
  column: number
  x: number
  y: number
  width: number
  height: number
  total: number
  color: string
}

interface LayoutLink {
  source: LayoutNode
  target: LayoutNode
  value: number
  sy0: number
  sy1: number
  ty0: number
  ty1: number
}

function computeLayout(
  nodes: SankeyNode[], links: SankeyLink[],
  width: number, height: number, nodePad: number = 8, nodeWidth: number = 18,
): { layoutNodes: LayoutNode[]; layoutLinks: LayoutLink[] } {
  const columns: SankeyNode[][] = [[], [], []]
  for (const n of nodes) {
    if (n.column >= 0 && n.column <= 2) columns[n.column].push(n)
  }

  // Sort each column by total descending
  for (const col of columns) col.sort((a, b) => b.total - a.total)

  const colX = [0, width * 0.4 - nodeWidth / 2, width - nodeWidth]

  const layoutNodes: LayoutNode[] = []
  const nodeMap = new Map<number, LayoutNode>()

  for (let ci = 0; ci < 3; ci++) {
    const col = columns[ci]
    const totalValue = col.reduce((s, n) => s + n.total, 0)
    const availableHeight = height - (col.length - 1) * nodePad
    let yOffset = 0

    for (const n of col) {
      const nodeHeight = Math.max(3, (n.total / totalValue) * availableHeight)
      const ln: LayoutNode = {
        id: n.id,
        name: n.name,
        column: ci,
        x: colX[ci],
        y: yOffset,
        width: nodeWidth,
        height: nodeHeight,
        total: n.total,
        color: COLUMN_COLORS[ci][0],
      }
      layoutNodes.push(ln)
      const origIdx = nodes.indexOf(n)
      nodeMap.set(origIdx, ln)
      yOffset += nodeHeight + nodePad
    }
  }

  // Track vertical offsets for link stacking
  const sourceOffsets = new Map<string, number>()
  const targetOffsets = new Map<string, number>()
  for (const ln of layoutNodes) {
    sourceOffsets.set(ln.id, ln.y)
    targetOffsets.set(ln.id, ln.y)
  }

  // Sort links by value descending for better visual stacking
  const sortedLinks = [...links].sort((a, b) => b.value - a.value)

  const layoutLinks: LayoutLink[] = []
  for (const link of sortedLinks) {
    const sn = nodeMap.get(link.source)
    const tn = nodeMap.get(link.target)
    if (!sn || !tn) continue

    const sTotal = sn.total
    const tTotal = tn.total

    const sHeight = (link.value / sTotal) * sn.height
    const tHeight = (link.value / tTotal) * tn.height

    const sy0 = sourceOffsets.get(sn.id)!
    const ty0 = targetOffsets.get(tn.id)!

    layoutLinks.push({
      source: sn,
      target: tn,
      value: link.value,
      sy0, sy1: sy0 + sHeight,
      ty0, ty1: ty0 + tHeight,
    })

    sourceOffsets.set(sn.id, sy0 + sHeight)
    targetOffsets.set(tn.id, ty0 + tHeight)
  }

  return { layoutNodes, layoutLinks }
}

function SankeyPath({ link, opacity }: { link: LayoutLink; opacity: number }) {
  const sx = link.source.x + link.source.width
  const tx = link.target.x
  const midX = (sx + tx) / 2

  const d = [
    `M ${sx} ${link.sy0}`,
    `C ${midX} ${link.sy0}, ${midX} ${link.ty0}, ${tx} ${link.ty0}`,
    `L ${tx} ${link.ty1}`,
    `C ${midX} ${link.ty1}, ${midX} ${link.sy1}, ${sx} ${link.sy1}`,
    'Z',
  ].join(' ')

  return (
    <path d={d} fill={link.source.color} opacity={opacity} />
  )
}

/* ---- Sankey SVG Component ---- */

function SankeyDiagram({ nodes, links, onPayeeNavigate }: {
  nodes: SankeyNode[]
  links: SankeyLink[]
  onPayeeNavigate?: (payee: string) => void
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const svgWidth = 800
  const svgHeight = Math.max(500, nodes.filter(n => n.column === 2).length * 20)

  const { layoutNodes, layoutLinks } = useMemo(
    () => computeLayout(nodes, links, svgWidth, svgHeight),
    [nodes, links, svgWidth, svgHeight],
  )

  const connectedToHover = useMemo(() => {
    if (!hovered) return new Set<string>()
    const ids = new Set<string>([hovered])
    for (const l of layoutLinks) {
      if (l.source.id === hovered || l.target.id === hovered) {
        ids.add(l.source.id)
        ids.add(l.target.id)
      }
    }
    return ids
  }, [hovered, layoutLinks])

  const labelOffset = 24

  return (
    <svg
      viewBox={`-120 -10 ${svgWidth + 240} ${svgHeight + 20}`}
      width="100%"
      style={{ maxHeight: '600px' }}
    >
      {/* Column headers */}
      {['Category Group', 'Category', 'Payee'].map((label, i) => {
        const x = i === 0 ? 0 : i === 1 ? svgWidth * 0.4 : svgWidth
        return (
          <text
            key={label} x={x} y={-2}
            textAnchor={i === 2 ? 'end' : i === 1 ? 'middle' : 'start'}
            style={{ fontSize: '11px', fontWeight: 700, fill: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}
          >
            {label}
          </text>
        )
      })}

      {/* Links */}
      {layoutLinks.map((l, i) => {
        const isHighlighted = hovered ? connectedToHover.has(l.source.id) && connectedToHover.has(l.target.id) : false
        return (
          <SankeyPath
            key={i}
            link={l}
            opacity={hovered ? (isHighlighted ? 0.4 : 0.05) : 0.2}
          />
        )
      })}

      {/* Nodes */}
      {layoutNodes.map(n => {
        const isHighlighted = hovered ? connectedToHover.has(n.id) : true
        const isPayee = n.column === 2

        return (
          <g
            key={n.id}
            onMouseEnter={() => setHovered(n.id)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => {
              if (isPayee && onPayeeNavigate) onPayeeNavigate(n.name)
            }}
            style={{ cursor: isPayee && onPayeeNavigate ? 'pointer' : 'default' }}
          >
            <rect
              x={n.x} y={n.y} width={n.width} height={n.height}
              fill={n.color}
              opacity={isHighlighted ? 0.85 : 0.2}
              rx={3}
            />
            {n.height > 10 && (
              <text
                x={n.column === 2 ? n.x + n.width + 6 : n.x - 6}
                y={n.y + n.height / 2}
                dominantBaseline="central"
                textAnchor={n.column === 2 ? 'start' : 'end'}
                style={{
                  fontSize: Math.min(11, Math.max(8, n.height * 0.6)) + 'px',
                  fill: isHighlighted ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontWeight: isHighlighted && hovered === n.id ? 700 : 400,
                }}
              >
                {n.name.length > 25 ? n.name.slice(0, 23) + '...' : n.name}
                {' '}{formatCurrency(n.total)}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

/* ---- Main Component ---- */

interface SpendingFlowProps {
  onPayeeNavigate?: (payee: string) => void
}

export default function SpendingFlow({ onPayeeNavigate }: SpendingFlowProps) {
  const [month, setMonth] = useState<string | undefined>(undefined)
  const [minAmount, setMinAmount] = useState(10)
  const [maxPayees, setMaxPayees] = useState(30)
  const { data, isLoading } = useSpendingFlow(month, minAmount, maxPayees)

  const availableMonths = data?.available_months ?? []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Spending Flow
          {data && (
            <span style={{ marginLeft: '10px', fontSize: '13px', fontWeight: 400, color: 'var(--text-muted)' }}>
              {formatMonthLabel(data.month)} &mdash; {formatCurrency(data.total_spending)} across {data.transaction_count} transactions
            </span>
          )}
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select
            value={month ?? ''}
            onChange={e => setMonth(e.target.value || undefined)}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            <option value="">Current Month</option>
            {availableMonths.map(m => (
              <option key={m} value={m}>{formatMonthLabel(m)}</option>
            ))}
          </select>
          <select
            value={minAmount}
            onChange={e => setMinAmount(Number(e.target.value))}
            style={{
              padding: '6px 10px', fontSize: '12px',
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', color: 'var(--text-primary)',
            }}
          >
            <option value={0}>All amounts</option>
            <option value={10}>Min $10</option>
            <option value={25}>Min $25</option>
            <option value={50}>Min $50</option>
            <option value={100}>Min $100</option>
          </select>
        </div>
      </div>

      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '20px', overflowX: 'auto',
      }}>
        {isLoading ? (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ marginRight: '8px' }} />
            Building spending flow...
          </div>
        ) : !data || data.nodes.length === 0 ? (
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No spending data for this month.
          </div>
        ) : (
          <SankeyDiagram
            nodes={data.nodes}
            links={data.links}
            onPayeeNavigate={onPayeeNavigate}
          />
        )}
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
        {[
          { color: COLUMN_COLORS[0][0], label: 'Category Groups' },
          { color: COLUMN_COLORS[1][0], label: 'Categories' },
          { color: COLUMN_COLORS[2][0], label: 'Payees (click to explore)' },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: item.color, opacity: 0.8 }} />
            {item.label}
          </div>
        ))}
      </div>
    </div>
  )
}
