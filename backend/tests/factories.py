from decimal import Decimal

import factory

from app.models.account import Account, AccountType
from app.models.user import User


class UserFactory(factory.Factory):

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    hashed_password = "$2b$12$placeholder"
    is_active = True
    is_verified = False


class AccountFactory(factory.Factory):

    class Meta:
        model = Account

    name = "Test Account"
    type = AccountType.CASH
    initial_balance = Decimal("0")
