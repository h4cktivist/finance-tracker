const TOKEN_KEY = 'ft.broker_token'
const ACCOUNT_ID_KEY = 'ft.broker_account_id'

export type BrokerSettings = {
  token: string
  accountId: string
}

export const brokerSettings = {
  get(): BrokerSettings | null {
    const token = localStorage.getItem(TOKEN_KEY)
    const accountId = localStorage.getItem(ACCOUNT_ID_KEY)
    if (!token || !accountId) return null
    return { token, accountId }
  },
  set(token: string, accountId: string) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(ACCOUNT_ID_KEY, accountId)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ACCOUNT_ID_KEY)
  },
}
