import json

from app.schemas.broker import BrokerPortfolio
from app.services.llm import call_openrouter

SYSTEM_PROMPT = (
    "Ты профессиональный инвестиционный консультант. Проанализируй брокерский портфель "
    "пользователя и дай практичный обзор и рекомендации на русском языке. "
    "Используй markdown: заголовки (##), маркированные списки. "
    "Выводи только анализ и рекомендации — без вступлений про то, что ты ИИ. "
    "Опирайся на конкретные цифры из данных (доли, доходность, P&L). "
    "Структурируй ответ блоками: обзор портфеля, диверсификация и риски, что сделано хорошо, "
    "на что обратить внимание, рекомендации по активам (что докупить, сократить или держать, "
    "и почему). В конце добавь короткую оговорку, что это не индивидуальная инвестиционная "
    "рекомендация."
)


class BrokerRecommendationsService:

    async def generate(self, portfolio: BrokerPortfolio) -> str:
        context = self._build_context(portfolio)
        user_msg = f"Данные брокерского портфеля (JSON):\n\n{context}"
        return await call_openrouter(SYSTEM_PROMPT, user_msg)

    def _build_context(self, portfolio: BrokerPortfolio) -> str:
        payload = {
            "account_id": portfolio.account_id,
            "status": portfolio.status,
            "equity": str(portfolio.equity),
            "unrealized_pnl": str(portfolio.unrealized_pnl),
            "daily_pnl": str(portfolio.daily_pnl),
            "cash": [
                {"currency": c.currency, "amount": str(c.amount)} for c in portfolio.cash
            ],
            "allocation": [
                {
                    "asset_class": a.asset_class,
                    "market_value": str(a.market_value),
                    "weight_percent": round(a.weight_percent, 2),
                }
                for a in portfolio.allocation
            ],
            "positions": [
                {
                    "symbol": p.symbol,
                    "name": p.name,
                    "asset_class": p.asset_class,
                    "quantity": str(p.quantity),
                    "average_price": str(p.average_price),
                    "current_price": str(p.current_price),
                    "market_value": str(p.market_value),
                    "unrealized_pnl": str(p.unrealized_pnl),
                    "unrealized_pnl_percent": round(p.unrealized_pnl_percent, 2),
                    "daily_pnl": str(p.daily_pnl),
                    "weight_percent": round(p.weight_percent, 2),
                }
                for p in portfolio.positions
            ],
            "income": {
                "coupon": str(portfolio.income.coupon),
                "dividend": str(portfolio.income.dividend),
                "redemption": str(portfolio.income.redemption),
                "lending": str(portfolio.income.lending),
                "other": str(portfolio.income.other),
                "commission": str(portfolio.income.commission),
                "total_return": str(portfolio.income.total_return),
                "period_from": portfolio.income.period_from.isoformat(),
            },
            "recent_transactions": [
                {
                    "date": t.timestamp.isoformat(),
                    "kind": t.kind,
                    "name": t.name,
                    "symbol": t.symbol,
                    "amount": str(t.amount),
                    "currency": t.currency,
                }
                for t in portfolio.transactions[:30]
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
