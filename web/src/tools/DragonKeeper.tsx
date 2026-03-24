import { useState, useEffect, useRef, useCallback } from 'react'
import { useSync } from '../hooks/dragon-keeper/use-sync'
import { useRecordVisit } from '../hooks/dragon-keeper/use-engagement'
import { useWriteBackStatus, useProcessWriteBack } from '../hooks/dragon-keeper/use-write-back'
import { useRules } from '../hooks/dragon-keeper/use-rules'
import { useToast } from '../components/dragon-keeper/toast'
import SafeToSpendHero from '../components/dragon-keeper/safe-to-spend-hero'
import FinancialSummaryCards from '../components/dragon-keeper/financial-summary-cards'
import SyncHealthCollapsible from '../components/dragon-keeper/sync-health-collapsible'
import CategorizationQueue from '../components/dragon-keeper/categorization-queue'
import QueueBadge from '../components/dragon-keeper/queue-badge'
import SpendingTrends from '../components/dragon-keeper/trend-row'
import ActivitySquares from '../components/dragon-keeper/activity-squares'
import DragonStateIndicator from '../components/dragon-keeper/dragon-state-indicator'
import KeeperGreetingStrip from '../components/dragon-keeper/keeper-greeting-strip'
import CategoryDetail from '../components/dragon-keeper/category-detail'
import RulesManagement from '../components/dragon-keeper/rules-management'
import TransactionExplorer from '../components/dragon-keeper/transaction-explorer'
import RecurringItems from '../components/dragon-keeper/recurring-items'
import DkSettingsPage from '../components/dragon-keeper/dk-settings-page'
import PaycheckTracer from '../components/dragon-keeper/paycheck-tracer'
import KeeperChatDrawer from '../components/dragon-keeper/keeper-chat-drawer'
import { ToastProvider } from '../components/dragon-keeper/toast'
import { useRecurring } from '../hooks/dragon-keeper/use-recurring'

export default function DragonKeeper() {
  return (
    <ToastProvider>
      <DragonKeeperInner />
    </ToastProvider>
  )
}

function DragonKeeperInner() {
  const sync = useSync()
  const recordVisit = useRecordVisit()
  const writeBackStatus = useWriteBackStatus()
  const processWriteBack = useProcessWriteBack()
  const { data: rulesData } = useRules()
  const rulesCount = rulesData?.rules?.length ?? 0
  const { data: recurringData } = useRecurring()
  const recurringCount = recurringData?.total_count ?? 0
  const unconfirmedCount = recurringData?.unconfirmed_count ?? 0
  const { toast } = useToast()
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null)
  const [view, setView] = useState<'dashboard' | 'rules' | 'transactions' | 'recurring' | 'settings' | 'paycheck'>('dashboard')
  const [chatOpen, setChatOpen] = useState(false)
  const [txnPayeeFilter, setTxnPayeeFilter] = useState<string | undefined>(undefined)
  const syncStartRef = useRef<number>(0)
  const [syncElapsed, setSyncElapsed] = useState<string | null>(null)
  const pushStartRef = useRef<number>(0)

  const navigateToPayee = useCallback((payee: string) => {
    setTxnPayeeFilter(payee)
    setSelectedCategoryId(null)
    setView('transactions')
  }, [])

  const pendingWriteBack = (writeBackStatus.data?.pending ?? 0) + (writeBackStatus.data?.failed_retryable ?? 0)
  const hasPending = pendingWriteBack > 0

  useEffect(() => {
    recordVisit.mutate()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setChatOpen(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const chatButton = (
    <button
      onClick={() => setChatOpen(true)}
      title="Chat with Keeper (Ctrl+K)"
      style={{
        position: 'fixed', bottom: '24px', right: '24px', zIndex: 90,
        width: '48px', height: '48px', borderRadius: '50%',
        background: 'var(--accent)', border: 'none', cursor: 'pointer',
        fontSize: '22px', display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
        transition: 'transform 0.15s, box-shadow 0.15s',
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.5)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.4)' }}
    >
      🐉
    </button>
  )

  if (view === 'rules') {
    return (
      <div className="dk-dashboard">
        <RulesManagement onBack={() => setView('dashboard')} />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  if (view === 'transactions') {
    return (
      <div className="dk-dashboard">
        <TransactionExplorer
          onBack={() => { setView('dashboard'); setTxnPayeeFilter(undefined) }}
          initialPayee={txnPayeeFilter}
        />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  if (view === 'recurring') {
    return (
      <div className="dk-dashboard">
        <RecurringItems
          onBack={() => setView('dashboard')}
          onPayeeNavigate={navigateToPayee}
        />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  if (view === 'settings') {
    return (
      <div className="dk-dashboard">
        <DkSettingsPage onBack={() => setView('dashboard')} />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  if (view === 'paycheck') {
    return (
      <div className="dk-dashboard">
        <PaycheckTracer
          onBack={() => setView('dashboard')}
          onPayeeNavigate={navigateToPayee}
        />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  if (selectedCategoryId) {
    return (
      <div className="dk-dashboard">
        <CategoryDetail
          categoryId={selectedCategoryId}
          onBack={() => setSelectedCategoryId(null)}
          onPayeeNavigate={navigateToPayee}
        />
        {!chatOpen && chatButton}
        <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
    )
  }

  return (
    <div className="dk-dashboard">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <DragonStateIndicator />
          <QueueBadge />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setView('transactions')}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
          >
            Transactions
          </button>
          <button
            onClick={() => setView('recurring')}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent',
              color: unconfirmedCount > 0 ? 'var(--warning, #f59e0b)' : 'var(--text-muted)',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
            onMouseLeave={e => { e.currentTarget.style.color = unconfirmedCount > 0 ? 'var(--warning, #f59e0b)' : 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
          >
            Subscriptions{recurringCount > 0 ? ` (${recurringCount})` : ''}{unconfirmedCount > 0 ? ` \u2022` : ''}
          </button>
          <button
            onClick={() => setView('paycheck')}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
          >
            Paycheck
          </button>
          <button
            onClick={() => setView('rules')}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
          >
            Rules{rulesCount > 0 ? ` (${rulesCount})` : ''}
          </button>
          <button
            onClick={() => setView('settings')}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: '1px solid var(--border)',
              cursor: 'pointer', background: 'transparent', color: 'var(--text-muted)',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--bg-hover)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
          >
            Settings
          </button>
          <button
            onClick={() => {
              pushStartRef.current = Date.now()
              processWriteBack.mutate(undefined, {
                onSuccess: (res) => {
                  const secs = ((Date.now() - pushStartRef.current) / 1000).toFixed(1)
                  if (res.error) {
                    toast(`Push failed: ${res.error}`, 'error')
                  } else if (res.succeeded > 0) {
                    toast(`Pushed ${res.succeeded} to YNAB${res.failed ? `, ${res.failed} failed` : ''} (${secs}s)`, 'success')
                  } else {
                    toast(`Nothing pushed (${secs}s)`, 'info')
                  }
                },
                onError: () => toast('Push to YNAB failed', 'error'),
              })
            }}
            disabled={!hasPending || processWriteBack.isPending}
            title={hasPending ? `Push ${pendingWriteBack} categorization(s) to YNAB` : 'Nothing to push'}
            style={{
              padding: '7px 14px', fontSize: '12px', fontWeight: 600,
              borderRadius: 'var(--radius)', border: 'none', cursor: hasPending ? 'pointer' : 'default',
              background: hasPending
                ? 'color-mix(in srgb, var(--accent) 15%, transparent)'
                : 'var(--bg-hover)',
              color: hasPending ? 'var(--accent)' : 'var(--text-muted)',
              opacity: processWriteBack.isPending ? 0.6 : 1,
            }}
          >
            {processWriteBack.isPending
              ? 'Pushing...'
              : `Push to YNAB${hasPending ? ` (${pendingWriteBack})` : ''}`}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => {
              syncStartRef.current = Date.now()
              setSyncElapsed(null)
              sync.mutate(undefined, {
                onSuccess: (data) => {
                  const secs = ((Date.now() - syncStartRef.current) / 1000).toFixed(1)
                  setSyncElapsed(secs)
                  const type = data.sync_type === 'delta' ? 'Delta' : 'Full'
                  toast(`${type} sync complete — ${data.transactions_synced} transactions (${secs}s)`, 'success')
                },
                onError: (err) => {
                  const secs = ((Date.now() - syncStartRef.current) / 1000).toFixed(1)
                  toast(`Sync failed after ${secs}s: ${err.message}`, 'error')
                },
              })
            }}
            disabled={sync.isPending}
          >
            {sync.isPending ? 'Importing...' : 'Import YNAB Data'}
          </button>
        </div>
      </div>

      <KeeperGreetingStrip />

      {sync.isPending && (
        <div className="info-box" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '12px' }}>
          <div className="spinner" />
          <span>Syncing data from YNAB... This may take a moment.</span>
        </div>
      )}

      {sync.isError && (
        <div className="error-box" style={{ marginTop: '12px' }}>
          <strong>Sync failed:</strong> {sync.error.message}
        </div>
      )}

      {sync.isSuccess && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(16,185,129,0.08)',
          border: '1px solid rgba(16,185,129,0.3)',
          borderRadius: 'var(--radius)',
          color: 'var(--success)',
          fontSize: '13px',
          marginTop: '12px',
        }}>
          <strong>Sync complete!</strong>{' '}
          {sync.data.sync_type === 'delta' ? 'Delta' : 'Full'} sync &mdash;{' '}
          {sync.data.accounts_synced} accounts, {sync.data.transactions_synced} transactions,{' '}
          {sync.data.categories_synced} categories, {sync.data.payees_synced} payees
          {syncElapsed && ` (${syncElapsed}s)`}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
        <SafeToSpendHero />
        <FinancialSummaryCards />
        <SpendingTrends onCategoryClick={(id) => setSelectedCategoryId(id)} />
        <CategorizationQueue onPayeeNavigate={navigateToPayee} />
        <ActivitySquares />
        <SyncHealthCollapsible />
      </div>

      {!chatOpen && chatButton}
      <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  )
}
