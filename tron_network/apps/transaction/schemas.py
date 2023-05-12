import json
import decimal
from typing import Optional

from tronpy.tron import TAddress, PrivateKey
from tronpy.async_tron import AsyncTransaction
from pydantic import BaseModel, Field, validator

import settings
from core.crypto import node
from core.crypto.utils import to_sun
from apps.common import utils
from apps.common.schemas import CurrencyMixin


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


class BodyCreateApprove(CurrencyMixin, BaseModel):
    owner_address: TAddress
    spender_address: TAddress
    amount: decimal.Decimal

    currency: str

    fee_limit: int = Field(default=settings.DEFAULT_FEE_LIMIT)


class BodyCreateTransferFrom(CurrencyMixin, BaseModel):
    owner_address: TAddress
    from_address: TAddress
    to_address: TAddress
    amount: decimal.Decimal

    currency: str

    fee_limit: int = Field(default=settings.DEFAULT_FEE_LIMIT)


class ResponseCommission(BaseModel):
    fee: decimal.Decimal = Field(default=0)
    energy: int = Field(default=0)
    bandwidth: int = Field(default=0)


class ResponseCreateTransaction(BaseModel):
    payload: str
    commission: ResponseCommission

    @property
    def payload_dict(self) -> dict:
        return json.loads(self.payload)


class BodySendTransaction(BaseModel):
    payload: str
    private_key: str

    @property
    def payload_dict(self) -> dict:
        return json.loads(self.payload)

    async def create_transaction_obj(self) -> AsyncTransaction:
        data = self.payload_dict.get('data')
        return await AsyncTransaction.from_json(data, client=node.client)

    @property
    def private_key_obj(self):
        return PrivateKey(private_key_bytes=bytes.fromhex(self.private_key))

    @property
    def extra(self) -> dict:
        return self.payload_dict.get('extra')


class ResponseSendTransactionExtra(BaseModel):
    type: str
    owner_address: Optional[TAddress] = None


class ResponseSendTransaction(BaseModel):
    transaction_id: str
    timestamp: int
    amount: decimal.Decimal
    fee: decimal.Decimal
    from_address: TAddress
    to_address: TAddress
    currency: str = Field(default='TRX')
    extra: ResponseSendTransactionExtra


class BodyCommission(BaseModel):
    """
    Parameter schemas:
        Transfer:
            from_address
            to_address
            amount
            currency
        Approve:
            owner_address
            spender_address
            amount
            currency
    """

    parameter: dict