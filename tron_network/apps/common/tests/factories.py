from typing import Optional

import faker
from tronpy.tron import TAddress

from apps.common.tests.utils import TronProvider


fake = faker.Faker()
fake.add_provider(TronProvider)


def fake_address():
    return fake.unique.tron_address()


def fake_private_key():
    return fake.unique.tron_private_key()


async def create_fake_contract(address: Optional[TAddress] = None, symbol: Optional[str] = None,
                               name: Optional[str] = None, decimal_place: Optional[int] = None):
    from tortoise.exceptions import IntegrityError
    from core.crypto import node
    from core.crypto.models import Contract
    a, s, n, dp = fake.unique.tron_contract()

    try:
        contract = Contract(
            address=address or a,
            symbol=symbol or s,
            name=name or n,
            decimal_place=decimal_place or dp,
        )
        await contract.save()
        await node.update_contracts()
    except IntegrityError:
        pass