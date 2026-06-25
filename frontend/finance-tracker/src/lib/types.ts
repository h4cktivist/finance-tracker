export type ApiResponse<T> = {
  success: boolean
  data: T | null
  message?: string
}

export type ApiError = {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown> | null
  }
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type User = {
  id: string
  email: string
  is_active: boolean
  is_verified: boolean
}

export type AccountType = 'debit' | 'credit' | 'cash' | 'savings'

export type Account = {
  id: string
  user_id: string
  name: string
  type: AccountType
  initial_balance: string
  balance: string | null
  created_at: string
  updated_at: string
}

export type AccountCreate = {
  name: string
  type: AccountType
  initial_balance?: string | number
}

export type AccountUpdate = {
  name?: string
  type?: AccountType
}

export type CategoryType = 'expense' | 'income'

export type Category = {
  id: string
  user_id: string
  name: string
  type: CategoryType
  parent_category_id: string | null
  color: string | null
  icon: string | null
  is_essential: boolean
  created_at: string
  updated_at: string
}

export type CategoryTreeNode = Category & { children: CategoryTreeNode[] }

export type CategoryCreate = {
  name: string
  type: CategoryType
  parent_category_id?: string | null
  color?: string | null
  icon?: string | null
  is_essential?: boolean
}

export type CategoryUpdate = {
  name?: string
  color?: string | null
  icon?: string | null
  is_essential?: boolean
  parent_category_id?: string | null
}

export type Tag = {
  id: string
  user_id: string
  name: string
  color: string | null
  created_at: string
  updated_at: string
}

export type TagCreate = { name: string; color?: string | null }
export type TagUpdate = { name?: string; color?: string | null }

export type TransactionType = 'expense' | 'income' | 'transfer'

export type Transaction = {
  id: string
  user_id: string
  account_id: string
  category_id: string | null
  type: TransactionType
  amount: string
  description: string | null
  merchant_name: string | null
  transaction_date: string
  notes: string | null
  transfer_group_id: string | null
  correction_of_id: string | null
  card_id: string | null
  tag_ids: string[]
  cashback_amount: string | null
  cashback_is_manual: boolean | null
  created_at: string
  updated_at: string
}

export type TransactionCreate = {
  account_id: string
  category_id?: string | null
  type: TransactionType
  amount: string | number
  description?: string | null
  merchant_name?: string | null
  transaction_date: string
  notes?: string | null
  tag_ids?: string[]
  target_account_id?: string | null
  card_id?: string | null
}

export type TransactionUpdate = {
  description?: string | null
  merchant_name?: string | null
  notes?: string | null
  tag_ids?: string[]
}

export type CorrectionCreate = {
  reason: string
  new_amount?: string | number
  new_account_id?: string | null
  new_category_id?: string | null
}

export type Paginated<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type BudgetPeriodType = 'weekly' | 'monthly' | 'yearly'

export type Budget = {
  id: string
  user_id: string
  category_id: string
  amount_limit: string
  period_type: BudgetPeriodType
  start_date: string
  end_date: string | null
  rollover_enabled: boolean
  created_at: string
  updated_at: string
}

export type BudgetCreate = {
  category_id: string
  amount_limit: string | number
  period_type: BudgetPeriodType
  start_date: string
  end_date?: string | null
  rollover_enabled?: boolean
}

export type BudgetUpdate = {
  amount_limit?: string | number
  end_date?: string | null
  rollover_enabled?: boolean
}

export type BudgetStatus = {
  budget_id: string
  spent: string
  remaining: string
  percent_used: number
  days_until_exceed: number | null
  is_exceeded: boolean
}

export type BudgetRecommendationType = 'create' | 'increase' | 'decrease'

export type BudgetRecommendation = {
  category_id: string
  category_name: string
  recommendation_type: BudgetRecommendationType
  suggested_amount_limit: string
  suggested_period_type: BudgetPeriodType
  avg_monthly_spent: string
  max_monthly_spent: string
  transaction_count: number
  months_with_activity: number
  existing_budget_id: string | null
  current_amount_limit: string | null
  reason: string
}

export type BudgetRecommendations = {
  items: BudgetRecommendation[]
  period_from: string
  period_to: string
  months_analyzed: number
}

export type RecurringFrequency = 'daily' | 'weekly' | 'monthly' | 'yearly'

export type Recurring = {
  id: string
  user_id: string
  frequency: RecurringFrequency
  interval: number
  start_date: string
  end_date: string | null
  next_execution_date: string
  is_active: boolean
  account_id: string
  category_id: string | null
  type: TransactionType
  amount: string
  description: string | null
  created_at: string
}

export type RecurringCreate = {
  frequency: RecurringFrequency
  interval?: number
  start_date: string
  end_date?: string | null
  account_id: string
  category_id?: string | null
  type: TransactionType
  amount: string | number
  description?: string | null
  merchant_name?: string | null
  notes?: string | null
}

export type RecurringUpdate = {
  is_active?: boolean
  end_date?: string | null
  amount?: string | number
}

export type Card = {
  id: string
  user_id: string
  account_id: string
  name: string
  bank_name: string | null
  last_digits: string | null
}

export type CardCreate = {
  account_id: string
  name: string
  bank_name?: string | null
  last_digits?: string | null
}

export type CashbackRule = {
  id: string
  card_id: string
  category_id: string
  cashback_percent: string
  monthly_limit: string | null
  min_purchase_amount: string | null
  start_date: string
  end_date: string | null
}

export type CashbackRuleCreate = {
  category_id: string
  cashback_percent: string | number
  monthly_limit?: string | number | null
  min_purchase_amount?: string | number | null
  start_date: string
  end_date?: string | null
}

export type CashbackRuleUpdate = {
  cashback_percent?: string | number
  monthly_limit?: string | number | null
  min_purchase_amount?: string | number | null
  start_date?: string
  end_date?: string | null
  recalculate_existing?: boolean
}

export type CashbackRuleUpdateResult = {
  rule: CashbackRule
  recalculated_transactions: number
}

export type CashbackSummary = {
  total_earned: string
  period_month: string | null
}

export type CashbackRecommendation = {
  category_id: string
  best_card_id: string
  best_card_name: string
  cashback_percent: string
  min_purchase_amount?: string | null
}

export type CashbackAccrual = {
  id: string
  transaction_id: string
  card_id: string
  amount: string
  period_month: string
  status: 'accrued' | 'missed'
  is_manual: boolean
}

export type CashbackManualSet = {
  amount: string | number
  card_id?: string | null
}

export type GoalStatus = 'active' | 'completed' | 'cancelled'

export type Goal = {
  id: string
  user_id: string
  name: string
  target_amount: string
  current_amount: string
  deadline: string | null
  linked_account_id: string | null
  status: GoalStatus
  created_at: string
  updated_at: string
}

export type GoalCreate = {
  name: string
  target_amount: string | number
  deadline?: string | null
  linked_account_id?: string | null
}

export type GoalUpdate = {
  name?: string
  target_amount?: string | number
  deadline?: string | null
  status?: GoalStatus
}

export type GoalProgress = {
  goal_id: string
  current_amount: string
  target_amount: string
  progress_percent: number
  remaining: string
  status: GoalStatus
}

export type Dashboard = {
  total_balance: string
  total_income: string
  total_expenses: string
  savings_rate: number
  cashback_earned: string
  goals_progress: Array<{
    id: string
    name: string
    current_amount: string
    target_amount: string
    progress_percent: number
  }>
}

export type CategoryStat = {
  category_id: string
  category_name: string
  color: string | null
  total: string
}

export type Statistics = {
  top_expense_categories: CategoryStat[]
  top_income_categories: CategoryStat[]
  cashflow: string
  average_daily_spending: string
  average_monthly_income: string
}

export type MerchantStat = {
  merchant_name: string
  total: string
  count: number
}

export type CategoryMerchants = {
  category_id: string
  category_name: string
  color: string | null
  total: string
  merchants: MerchantStat[]
}

export type Merchants = {
  categories: CategoryMerchants[]
}

export type HeatmapDay = {
  date: string
  count: number
  intensity: number
  total_amount: string
}

export type Heatmap = {
  days: HeatmapDay[]
}

export type Ratios = {
  savings_rate: number
  expense_to_income_ratio: number
  discretionary_spending_ratio: number
}

export type TrendPoint = {
  date: string
  income: string
  expenses: string
}

export type Trends = {
  points: TrendPoint[]
}

export type ForecastBreakdown = {
  recurring: string
  trend: string
}

export type ForecastConfidence = 'low' | 'medium' | 'high'

export type Forecast = {
  target_month: string
  income: string
  expenses: string
  cashflow: string
  income_breakdown: ForecastBreakdown
  expenses_breakdown: ForecastBreakdown
  confidence: ForecastConfidence
  months_used: number
}

export type NotificationType =
  | 'budget_warning'
  | 'budget_exceeded'
  | 'recurring_created'
  | 'goal_deadline'
  | 'cashback_available'

export type AppNotification = {
  id: string
  type: NotificationType
  title: string
  body: string
  payload: Record<string, unknown> | null
  read_at: string | null
  created_at: string
}

export type AIRecommendations = {
  month: string
  content: string
}

export type BrokerCashBalance = {
  currency: string
  amount: string
}

export type BrokerPosition = {
  symbol: string
  name: string | null
  asset_class: string | null
  quantity: string
  average_price: string
  current_price: string
  market_value: string
  unrealized_pnl: string
  unrealized_pnl_percent: number
  daily_pnl: string
  weight_percent: number
}

export type BrokerAllocationItem = {
  asset_class: string
  market_value: string
  weight_percent: number
}

export type BrokerTransactionKind =
  | 'deposit'
  | 'withdrawal'
  | 'commission'
  | 'coupon'
  | 'dividend'
  | 'redemption'
  | 'lending'
  | 'income_other'
  | 'other'

export type BrokerIncomeBreakdown = {
  coupon: string
  dividend: string
  redemption: string
  lending: string
  other: string
  commission: string
  total_return: string
  period_from: string
}

export type BrokerTransaction = {
  id: string
  timestamp: string
  kind: BrokerTransactionKind
  name: string
  symbol: string | null
  amount: string
  currency: string
}

export type BrokerPortfolio = {
  account_id: string
  status: string
  equity: string
  unrealized_pnl: string
  daily_pnl: string
  cash: BrokerCashBalance[]
  positions: BrokerPosition[]
  allocation: BrokerAllocationItem[]
  income: BrokerIncomeBreakdown
  transactions: BrokerTransaction[]
  updated_at: string
}
