import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type {
  Account,
  AccountCreate,
  AccountUpdate,
  Budget,
  BudgetCreate,
  BudgetRecommendations,
  BudgetStatus,
  BudgetUpdate,
  Card,
  CardCreate,
  CashbackAccrual,
  CashbackManualSet,
  CashbackRecommendation,
  CashbackRule,
  CashbackRuleCreate,
  CashbackRuleUpdate,
  CashbackRuleUpdateResult,
  CashbackSummary,
  Category,
  CategoryCreate,
  CategoryTreeNode,
  CategoryUpdate,
  CorrectionCreate,
  Dashboard,
  Forecast,
  Goal,
  GoalCreate,
  GoalProgress,
  GoalUpdate,
  Heatmap,
  AIRecommendations,
  AppNotification,
  Merchants,
  Paginated,
  Ratios,
  Recurring,
  RecurringCreate,
  RecurringUpdate,
  Statistics,
  Trends,
  Tag,
  TagCreate,
  TagUpdate,
  Transaction,
  TransactionCreate,
  TransactionUpdate,
} from '@/lib/types'

// === Accounts ===
export const accountsKey = ['accounts'] as const

export function useAccounts() {
  return useQuery({
    queryKey: accountsKey,
    queryFn: () => api.get<Account[]>('/accounts'),
  })
}

export function useCreateAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: AccountCreate) => api.post<Account>('/accounts', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: accountsKey }),
  })
}

export function useUpdateAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountUpdate }) =>
      api.patch<Account>(`/accounts/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: accountsKey }),
  })
}

export function useDeleteAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<null>(`/accounts/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: accountsKey }),
  })
}

// === Categories ===
export const categoriesKey = ['categories'] as const
export const categoriesTreeKey = ['categories', 'tree'] as const

export function useCategories() {
  return useQuery({
    queryKey: categoriesKey,
    queryFn: () => api.get<Category[]>('/categories'),
  })
}

export function useCategoriesTree() {
  return useQuery({
    queryKey: categoriesTreeKey,
    queryFn: () => api.get<CategoryTreeNode[]>('/categories/tree'),
  })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CategoryCreate) => api.post<Category>('/categories', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: categoriesKey })
      qc.invalidateQueries({ queryKey: categoriesTreeKey })
    },
  })
}

export function useUpdateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) =>
      api.patch<Category>(`/categories/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: categoriesKey })
      qc.invalidateQueries({ queryKey: categoriesTreeKey })
    },
  })
}

export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<null>(`/categories/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: categoriesKey })
      qc.invalidateQueries({ queryKey: categoriesTreeKey })
    },
  })
}

// === Tags ===
export const tagsKey = ['tags'] as const

export function useTags() {
  return useQuery({ queryKey: tagsKey, queryFn: () => api.get<Tag[]>('/tags') })
}

export function useCreateTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TagCreate) => api.post<Tag>('/tags', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: tagsKey }),
  })
}

export function useUpdateTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TagUpdate }) =>
      api.patch<Tag>(`/tags/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: tagsKey }),
  })
}

export function useDeleteTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<null>(`/tags/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: tagsKey }),
  })
}

// === Transactions ===
export type TransactionsFilters = {
  page?: number
  page_size?: number
  type?: string
  account_id?: string
  category_id?: string
  tag_id?: string
  date_from?: string
  date_to?: string
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export function useTransactions(filters: TransactionsFilters = {}) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => api.get<Paginated<Transaction>>('/transactions', filters),
  })
}

export function useCreateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TransactionCreate) =>
      api.post<Transaction | Transaction[]>('/transactions', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: accountsKey })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
      qc.invalidateQueries({ queryKey: ['statistics'] })
      qc.invalidateQueries({ queryKey: ['merchants'] })
      qc.invalidateQueries({ queryKey: ['heatmap'] })
      qc.invalidateQueries({ queryKey: ['ratios'] })
      qc.invalidateQueries({ queryKey: ['budgets'] })
      qc.invalidateQueries({ queryKey: ['cashback'] })
    },
  })
}

export function useUpdateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TransactionUpdate }) =>
      api.patch<Transaction>(`/transactions/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transactions'] }),
  })
}

export function useDeleteTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<null>(`/transactions/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: accountsKey })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })
}

export function useSetTransactionCashback() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      transactionId,
      data,
    }: {
      transactionId: string
      data: CashbackManualSet
    }) => api.put<CashbackAccrual | null>(`/transactions/${transactionId}/cashback`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['cashback'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useDeleteTransactionCashback() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (transactionId: string) =>
      api.delete<null>(`/transactions/${transactionId}/cashback`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['cashback'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useCorrectTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CorrectionCreate }) =>
      api.post<Transaction>(`/transactions/${id}/correct`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: accountsKey })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['goals'] })
    },
  })
}

// === Budgets ===
export const budgetsKey = ['budgets'] as const

export function useBudgets() {
  return useQuery({ queryKey: budgetsKey, queryFn: () => api.get<Budget[]>('/budgets') })
}

export const budgetRecommendationsKey = ['budgets', 'recommendations'] as const

export function useBudgetRecommendations() {
  return useQuery({
    queryKey: budgetRecommendationsKey,
    queryFn: () => api.get<BudgetRecommendations>('/budgets/recommendations'),
  })
}

export function useBudgetStatus(id: string | undefined) {
  return useQuery({
    queryKey: ['budgets', id, 'status'],
    queryFn: () => api.get<BudgetStatus>(`/budgets/${id}/status`),
    enabled: !!id,
  })
}

export function useCreateBudget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: BudgetCreate) => api.post<Budget>('/budgets', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: budgetsKey })
      qc.invalidateQueries({ queryKey: budgetRecommendationsKey })
    },
  })
}

export function useUpdateBudget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BudgetUpdate }) =>
      api.patch<Budget>(`/budgets/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: budgetsKey })
      qc.invalidateQueries({ queryKey: budgetRecommendationsKey })
    },
  })
}

export function useDeleteBudget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete<null>(`/budgets/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: budgetsKey })
      qc.invalidateQueries({ queryKey: budgetRecommendationsKey })
    },
  })
}

// === Recurring ===
export const recurringKey = ['recurring'] as const

export function useRecurring() {
  return useQuery({ queryKey: recurringKey, queryFn: () => api.get<Recurring[]>('/recurring') })
}

export function useCreateRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: RecurringCreate) => api.post<Recurring>('/recurring', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: recurringKey }),
  })
}

export function useUpdateRecurring() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RecurringUpdate }) =>
      api.patch<Recurring>(`/recurring/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: recurringKey }),
  })
}

// === Cashback ===
export const cardsKey = ['cashback', 'cards'] as const

export function useCards() {
  return useQuery({ queryKey: cardsKey, queryFn: () => api.get<Card[]>('/cashback/cards') })
}

export function useCreateCard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CardCreate) => api.post<Card>('/cashback/cards', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: cardsKey }),
  })
}

export function useCardRules(cardId: string | undefined) {
  return useQuery({
    queryKey: ['cashback', 'rules', cardId],
    queryFn: () => api.get<CashbackRule[]>(`/cashback/cards/${cardId}/rules`),
    enabled: !!cardId,
  })
}

export function useCreateCashbackRule(cardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CashbackRuleCreate) =>
      api.post<CashbackRule>(`/cashback/cards/${cardId}/rules`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cashback', 'rules', cardId] })
      qc.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}

export function useUpdateCashbackRule(cardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: string; data: CashbackRuleUpdate }) =>
      api.patch<CashbackRuleUpdateResult>(
        `/cashback/cards/${cardId}/rules/${ruleId}`,
        data,
      ),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ['cashback', 'rules', cardId] })
      qc.invalidateQueries({ queryKey: ['cashback', 'summary'] })
      qc.invalidateQueries({ queryKey: ['cashback', 'missed'] })
      qc.invalidateQueries({ queryKey: ['transactions'] })
      if (result.recalculated_transactions > 0) {
        qc.invalidateQueries({ queryKey: ['dashboard'] })
      }
    },
  })
}

export function useCashbackSummary(periodMonth?: string) {
  return useQuery({
    queryKey: ['cashback', 'summary', periodMonth],
    queryFn: () =>
      api.get<CashbackSummary>('/cashback/summary', periodMonth ? { period_month: periodMonth } : undefined),
  })
}

export function useMissedCashback() {
  return useQuery({
    queryKey: ['cashback', 'missed'],
    queryFn: () => api.get<CashbackAccrual[]>('/cashback/missed'),
  })
}

export function useCashbackRecommendations(categoryId: string | undefined) {
  return useQuery({
    queryKey: ['cashback', 'recommendations', categoryId],
    queryFn: () =>
      api.get<CashbackRecommendation[]>('/cashback/recommendations', { category_id: categoryId }),
    enabled: !!categoryId,
  })
}

// === Goals ===
export const goalsKey = ['goals'] as const

export function useGoals() {
  return useQuery({ queryKey: goalsKey, queryFn: () => api.get<Goal[]>('/goals') })
}

export function useGoalProgress(id: string | undefined) {
  return useQuery({
    queryKey: ['goals', id, 'progress'],
    queryFn: () => api.get<GoalProgress>(`/goals/${id}/progress`),
    enabled: !!id,
  })
}

export function useCreateGoal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: GoalCreate) => api.post<Goal>('/goals', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: goalsKey }),
  })
}

export function useUpdateGoal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: GoalUpdate }) =>
      api.patch<Goal>(`/goals/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: goalsKey }),
  })
}

// === Analytics ===
function analyticsParams(
  excludeInvestments: boolean,
  extra?: Record<string, unknown>,
): Record<string, unknown> {
  const params: Record<string, unknown> = { ...extra }
  if (excludeInvestments) params.exclude_investments = true
  return params
}

export function useDashboard(excludeInvestments = false) {
  return useQuery({
    queryKey: ['dashboard', excludeInvestments],
    queryFn: () => api.get<Dashboard>('/analytics/dashboard', analyticsParams(excludeInvestments)),
  })
}

export function useStatistics(
  dateFrom?: string,
  dateTo?: string,
  excludeInvestments = false,
) {
  return useQuery({
    queryKey: ['statistics', dateFrom, dateTo, excludeInvestments],
    queryFn: () => {
      const params: Record<string, unknown> = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      return api.get<Statistics>(
        '/analytics/statistics',
        analyticsParams(excludeInvestments, params),
      )
    },
  })
}

export function useMerchants(dateFrom?: string, dateTo?: string, excludeInvestments = false) {
  return useQuery({
    queryKey: ['merchants', dateFrom, dateTo, excludeInvestments],
    queryFn: () => {
      const params: Record<string, unknown> = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      return api.get<Merchants>('/analytics/merchants', analyticsParams(excludeInvestments, params))
    },
  })
}

export function useHeatmap(dateFrom?: string, dateTo?: string, excludeInvestments = false) {
  return useQuery({
    queryKey: ['heatmap', dateFrom, dateTo, excludeInvestments],
    queryFn: () => {
      const params: Record<string, unknown> = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      return api.get<Heatmap>('/analytics/heatmap', analyticsParams(excludeInvestments, params))
    },
  })
}

export function useTrends(dateFrom?: string, dateTo?: string, excludeInvestments = false) {
  return useQuery({
    queryKey: ['trends', dateFrom, dateTo, excludeInvestments],
    queryFn: () => {
      const params: Record<string, unknown> = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      return api.get<Trends>('/analytics/trends', analyticsParams(excludeInvestments, params))
    },
  })
}

export function useRatios(excludeInvestments = false) {
  return useQuery({
    queryKey: ['ratios', excludeInvestments],
    queryFn: () => api.get<Ratios>('/analytics/ratios', analyticsParams(excludeInvestments)),
  })
}

export function useForecast(excludeInvestments = false) {
  return useQuery({
    queryKey: ['forecast', excludeInvestments],
    queryFn: () => api.get<Forecast>('/analytics/forecast', analyticsParams(excludeInvestments)),
  })
}

// === AI recommendations ===
export function useAiRecommendations() {
  return useMutation({
    mutationFn: (month: string) =>
      api.post<AIRecommendations>(
        `/ai/recommendations?month=${encodeURIComponent(month)}`,
        {},
      ),
  })
}

// === Notifications ===
export function useNotifications(unreadOnly = false, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['notifications', unreadOnly, page, pageSize],
    queryFn: () =>
      api.get<Paginated<AppNotification>>('/notifications', {
        page,
        page_size: pageSize,
        unread_only: unreadOnly,
      }),
    refetchInterval: 60_000,
  })
}

export function useMarkNotificationRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.patch<AppNotification>(`/notifications/${id}/read`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ marked_read: number }>('/notifications/read-all', {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })
}
