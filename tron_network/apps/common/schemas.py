import decimal
from typing import Optional

from tronpy.tron import TAddress
from pydantic import BaseModel, Field, ValidationError, Json
from pydantic.class_validators import validator

import settings
from core.crypto import node
from core.crypto.utils import to_sun
from core.crypto.contract import Contract
from apps.common import utils


class CurrencyMixin:
    currency: str

    @property
    def is_native(self) -> bool:
        return self.currency == 'TRX'

    @property
    def contract(self) -> Contract:
        if not self.is_native:
            return node.get_contract_by_symbol(self.currency)


class BodyCreateWallet(BaseModel):
    mnemonic: Optional[str] = Field(default=utils.generate_mnemonic())
    passphrase: Optional[str] = Field(default=utils.generate_passphrase())


class ResponseCreateWallet(BodyCreateWallet):
    private_key: str
    public_key: str
    address: TAddress


class BodyWalletBalance(CurrencyMixin, BaseModel):
    address: TAddress
    currency: Optional[str] = Field(default='TRX')

    @validator('currency')
    def correct_currency(cls, currency: str):
        currency = currency.upper()
        if currency != 'TRX' and not node.has_currency(currency):
            raise ValidationError(f'Currency: {currency} not found')
        return currency

    @validator('address')
    def correct_address(cls, address: TAddress):
        return utils.correct_address(address)


class ResponseWalletBalance(BaseModel):
    balance: decimal.Decimal = Field(default=0)


class BodyAllowance(CurrencyMixin, BaseModel):
    owner_address: TAddress
    spender_address: TAddress
    currency: str

    @validator('currency')
    def correct_currency(cls, currency: str):
        currency = currency.upper()
        if not node.has_currency(currency):
            raise ValidationError(f'Currency: {currency} not found')
        return currency

    @validator('owner_address', 'spender_address')
    def correct_address(cls, address: TAddress):
        return utils.correct_address(address)


class ResponseAllowance(BaseModel):
    amount: decimal.Decimal = Field(default=0)


class BodyCreateTransfer(CurrencyMixin, BaseModel):
    from_address: TAddress
    to_address: TAddress
    amount: decimal.Decimal

    currency: str = Field(default='TRX')

    fee_limit: int = Field(default=settings.DEFAULT_FEE_LIMIT)

    @property
    def sun_amount(self) -> int:
        # Amount to Sun amount
        return to_sun(self.amount)

    @validator('from_address', 'to_address')
    def correct_address(cls, address: TAddress):
        return utils.correct_address(address)


class BodyCommission(BaseModel):
    fee: decimal.Decimal = Field(default=0)
    energy: int = Field(default=0)
    bandwidth: int = Field(default=0)


class ResponseCreateTransfer(BaseModel):
    payload: Json
    commission: BodyCommission
    extra: dict = Field(default_factory=dict)
