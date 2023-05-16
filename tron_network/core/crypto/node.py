import decimal
from typing import Optional

from tronpy.tron import TAddress
from tronpy.exceptions import AddressNotFound
from tronpy.async_tron import AsyncTron, AsyncHTTPProvider

import settings
from core import meta
from core.crypto import models
from core.crypto.contract import Contract
from core.crypto.calculator import FeeCalculator
from core.crypto.utils import from_sun, is_native


class Node(metaclass=meta.Singleton):
    class ContractNotFound(Exception):
        pass

    def __init__(self):
        self.provider = AsyncHTTPProvider(endpoint_uri=settings.NODE_URL)
        self.client = AsyncTron(
            provider=self.provider
        )

        self.contracts: dict[str, Contract] = {}
        self.pointers_to_contracts: dict[TAddress, str] = {}

        self.fee_calculator = FeeCalculator(self)

    @property
    def calculator(self) -> FeeCalculator:
        return self.fee_calculator

    async def update_contracts(self):
        contracts = await models.Contract.all()
        for contract in contracts:
            self.contracts.update({
                contract.symbol: Contract(
                    contract=await self.client.get_contract(contract.address),
                    client=self.client,
                    name=contract.name,
                    symbol=contract.symbol,
                    decimal_place=contract.decimal_place,
                )
            })
            self.pointers_to_contracts.update({
                contract.address: contract.symbol,
            })

    def get_contract_by_symbol(self, symbol: str) -> Contract:
        contract = self.contracts.get(symbol)
        if not contract:
            raise self.ContractNotFound()
        return contract

    def get_contract_by_contract_address(self, contract_address: TAddress) -> Contract:
        pointer = self.pointers_to_contracts.get(contract_address)
        if not pointer:
            raise self.ContractNotFound()
        return self.contracts[pointer]

    def has_currency(self, currency: str) -> bool:
        return self.contracts.get(currency) is not None

    def has_contract_address(self, contract_address: TAddress) -> bool:
        return self.pointers_to_contracts.get(contract_address) is not None

    async def is_active_address(self, address: TAddress) -> bool:
        try:
            await self.client.get_account_balance(address)
        except AddressNotFound:
            return False
        else:
            return True

    async def get_account_balance(self, address: TAddress, currency: str) -> decimal.Decimal:
        if is_native(currency):
            return await self.client.get_account_balance(address)
        contract = self.get_contract_by_symbol(currency)
        return await contract.balance_of(address)

    async def get_bandwidth_balance(self, address: TAddress) -> int:
        resource = await self.client.get_account_resource(address)
        return (
                resource["freeNetLimit"] - resource.get("freeNetUsed", 0) +
                resource.get("NetLimit", 0) - resource.get("NetUsed", 0)
        )

    async def get_energy_balance(self, address: TAddress) -> int:
        resource = await self.client.get_account_resource(address)
        return resource.get('EnergyLimit', 0) - resource.get('EnergyUsed', 0)

    async def get_delegated_resource(self, owner_address: TAddress, recipient_address: TAddress,
                                     resource: Optional[str] = None) -> dict[str, decimal.Decimal] | decimal.Decimal:
        response = await self.client.get_delegated_resource_v2(owner_address, recipient_address)
        if response == 'ENERGY':
            return from_sun(response.get('frozen_balance_for_energy', 0))
        elif response == 'BANDWIDTH':
            return from_sun(response.get('frozen_balance_for_bandwidth', 0))
        else:
            return dict(
                energy=from_sun(response.get('frozen_balance_for_energy', 0)),
                bandwidth=from_sun(response.get('frozen_balance_for_bandwidth', 0)),
            )

    async def has_delegate_resource(self, owner_address: TAddress, recipient_address: TAddress, resource: str) -> bool:
        delegated_balance = await self.get_delegated_resource(owner_address, recipient_address, resource)
        return delegated_balance > 0
