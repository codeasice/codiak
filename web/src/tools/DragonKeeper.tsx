import { useState, useEffect, useRef, useCallback } from 'react'
import { useSync } from '../hooks/dragon-keeper/use-sync'
import { useRecordVisit } from '../hooks/dragon-keeper/use-engagement'
import { useWriteBackStatus, useProcessWriteBack } from '../hooks/dragon-keeper/use-write-back'
import { useToast } from '../components/dragon-keeper/toast'
import SafeToSpendHero from '../components/dragon-keeper/safe-to-spend-hero'
import FinancialSummaryCards from '../components/dragon-keeper/financial-summary-cards'
import SyncHealthCollapsible from '../components/dragon-keeper/sync-health-collapsible'
import CategorizationQueue from '../components/dragon-keeper/categorization-queue'
import SpendingTrends from '../components/dragon-keeper/trend-row'
import ActivitySquares from '../components/dragon-keeper/activity-squares'
import DragonStateIndicator from '../components/dragon-keeper/dragon-state-indicator'
import KeeperGreetingStrip from '../components/dragon-keeper/keeper-greeting-strip'
import CategoryDetail from '../components/dragon-keeper/category-detail'
import TransactionExplorer from '../components/dragon-keeper/transaction-explorer'
import RecurringItems from '../components/dragon-keeper/recurring-items'
import DkSettingsPage from '../components/dragon-keeper/dk-settings-page'
import PaycheckTracer from '../components/dragon-keeper/paycheck-tracer'
import BalanceChart from '../components/dragon-keeper/balance-chart'
import SpendingFlow from '../components/dragon-keeper/spending-flow'
import AccountsPage from '../components/dragon-keeper/accounts-page'
import KeeperChatDrawer from '../components/dragon-keeper/keeper-chat-drawer'
import { ToastProvider } from '../components/dragon-keeper/toast'
import { useRecurring } from '../hooks/dragon-keeper/use-recurring'
import { Settings, LayoutDashboard, ArrowLeftRight, RefreshCw, Wallet, CreditCard, TrendingUp } from 'lucide-react'

type DkView = 'dashboard' | 'transactions' | 'recurring' | 'settings' | 'paycheck' | 'flow' | 'accounts'

const VIEW_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  transactions: 'Transactions',
  recurring: 'Subscriptions',
  settings: 'Settings',
  paycheck: 'Paycheck',
  flow: 'Flow',
  accounts: 'Accounts',
  category: 'Category',
}

export default function DragonKeeper() {
  return (
    <ToastProvider>
      <DragonKeeperInner />
    </ToastProvider>
  )
}

DragonKeeper.HeaderExtra = DragonStateIndicator

function DragonKeeperInner() {
  const sync = useSync()
  const recordVisit = useRecordVisit()
  const writeBackStatus = useWriteBackStatus()
  const processWriteBack = useProcessWriteBack()
  const { data: recurringData } = useRecurring()
  const recurringCount = recurringData?.total_count ?? 0
  const unconfirmedCount = recurringData?.unconfirmed_count ?? 0
  const { toast } = useToast()
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null)
  const [view, setView] = useState<DkView>('dashboard')
  const [chatOpen, setChatOpen] = useState(false)
  const [txnPayeeFilter, setTxnPayeeFilter] = useState<string | undefined>(undefined)
  const [txnInitialFilters, setTxnInitialFilters] = useState<Record<string, any> | undefined>(undefined)
  const syncStartRef = useRef<number>(0)
  const [syncElapsed, setSyncElapsed] = useState<string | null>(null)
  const pushStartRef = useRef<number>(0)

  const navigate = useCallback((newView: DkView) => {
    setView(newView)
    setSelectedCategoryId(null)
    if (newView !== 'transactions') {
      setTxnPayeeFilter(undefined)
      setTxnInitialFilters(undefined)
    }
  }, [])

  const navigateToPayee = useCallback((payee: string) => {
    setTxnPayeeFilter(payee)
    setTxnInitialFilters(undefined)
    setSelectedCategoryId(null)
    setView('transactions')
  }, [])

  const navigateToCategoryPeriod = useCallback((categoryId: string, dateFrom: string, dateTo: string) => {
    setTxnPayeeFilter(undefined)
    setTxnInitialFilters({ category_id: categoryId, date_from: dateFrom, date_to: dateTo })
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

  const isDashboard = view === 'dashboard' && !selectedCategoryId
  const currentViewKey = selectedCategoryId ? 'category' : view

  const renderContent = () => {
    if (selectedCategoryId) {
      return (
        <CategoryDetail
          categoryId={selectedCategoryId}
          onBack={() => setSelectedCategoryId(null)}
          onPayeeNavigate={navigateToPayee}
        />
      )
    }
    switch (view) {
      case 'transactions':
        return <TransactionExplorer initialPayee={txnPayeeFilter} initialFilters={txnInitialFilters} />
      case 'recurring':
        return <RecurringItems onPayeeNavigate={navigateToPayee} />
      case 'settings':
        return <DkSettingsPage />
      case 'paycheck':
        return (
          <PaycheckTracer
            onPayeeNavigate={navigateToPayee}
            onNavigateToExplorer={({ category_id, date_from, date_to }) =>
              navigateToCategoryPeriod(category_id ?? '', date_from ?? '', date_to ?? '')
            }
          />
        )
      case 'flow':
        return <SpendingFlow onPayeeNavigate={navigateToPayee} />
      case 'accounts':
        return <AccountsPage />
      default:
        return (
          <>
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
              <SpendingTrends
                onCategoryClick={(id) => setSelectedCategoryId(id)}
                onBarClick={navigateToCategoryPeriod}
              />
              <BalanceChart />
              <CategorizationQueue onPayeeNavigate={navigateToPayee} />
              <ActivitySquares />
              <SyncHealthCollapsible />
            </div>
          </>
        )
    }
  }

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

  return (
    <div className="dk-dashboard">
      <nav className="dk-nav">
        <div className="dk-nav__tabs">
          <button
            className={`btn btn-ghost${isDashboard ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('dashboard')}
          >
            <LayoutDashboard size={14} />
            Dashboard
          </button>
          <button
            className={`btn btn-ghost${view === 'transactions' && !selectedCategoryId ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('transactions')}
          >
            <ArrowLeftRight size={14} />
            Transactions
          </button>
          <button
            className={`btn btn-ghost${view === 'recurring' ? ' dk-nav-active' : ''}${unconfirmedCount > 0 ? ' btn-warn' : ''}`}
            onClick={() => navigate('recurring')}
          >
            <RefreshCw size={14} />
            Subscriptions{recurringCount > 0 ? ` (${recurringCount})` : ''}{unconfirmedCount > 0 ? ' •' : ''}
          </button>
          <button
            className={`btn btn-ghost${view === 'paycheck' ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('paycheck')}
          >
            <Wallet size={14} />
            Paycheck
          </button>
          <button
            className={`btn btn-ghost${view === 'accounts' ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('accounts')}
          >
            <CreditCard size={14} />
            Accounts
          </button>
          <button
            className={`btn btn-ghost${view === 'flow' ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('flow')}
          >
            <TrendingUp size={14} />
            Flow
          </button>
        </div>

        <div className="dk-nav__actions">
          <button
            className={`btn btn-ghost${view === 'settings' ? ' dk-nav-active' : ''}`}
            onClick={() => navigate('settings')}
            title="Settings"
            style={{ padding: '8px' }}
          >
            <Settings size={16} />
          </button>
          <button
            className={`btn btn-push${hasPending ? ' btn-push--active' : ''}`}
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
            style={{ opacity: processWriteBack.isPending ? 0.6 : 1 }}
          >
            {processWriteBack.isPending ? 'Pushing...' : `Push${hasPending ? ` (${pendingWriteBack})` : ''}`}
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
            {sync.isPending ? 'Importing...' : 'Sync'}
          </button>
        </div>
      </nav>

      {!isDashboard && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          fontSize: '12px', marginBottom: '16px',
        }}>
          <button
            onClick={() => navigate('dashboard')}
            style={{
              background: 'none', border: 'none', padding: 0,
              color: 'var(--accent)', fontSize: '12px', cursor: 'pointer', fontWeight: 500,
            }}
          >
            Dashboard
          </button>
          <span style={{ color: 'var(--text-muted)' }}>›</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {VIEW_LABELS[currentViewKey]}
          </span>
        </div>
      )}

      {renderContent()}

      {!chatOpen && chatButton}
      <KeeperChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  )
}
