from typing import Union, Optional, Dict

from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import TronMainnet
from tronpy.async_tron import AsyncTron, AsyncHTTPProvider, TAddress
import tronpy.exceptions

from .schemas import BodyCreateWallet, ResponseCreateWallet
from config import Config, decimals


class NodeCore:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(NodeCore, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.node = AsyncTron(
            provider=AsyncHTTPProvider(Config.NODE_URL) if Config.NETWORK.upper() == "MAINNET" else None,
            network=Config.NETWORK.lower()
        )

    # <<<=======================================>>> Tron Station <<<=================================================>>>

    async def get_chain_parameters_by_name(self, name: str) -> int:
        parameters = await self.node.get_chain_parameters()
        for parameter in parameters:
            if parameter["key"] == name:
                return parameter["value"]
        else:
            return 0

    async def calculate_burn_energy(self, amount: Union[float, int]) -> Union[float, int]:
        """
        Returns the amount of energy generated by burning TRX
        :param amount: Amount of TRX in sun
        :return:
        """
        energy_fee = await self.get_chain_parameters_by_name(name="getEnergyFee")
        if float(energy_fee) == 0:
            return decimals.create_decimal(0)
        fee = (amount / energy_fee) * 1_000_000
        return decimals.create_decimal(fee)

    async def get_account_bandwidth(self, address: TAddress) -> Dict:
        """
        Returns bandwidth data from account.
        :param address: Address of account
        """
        account_resources = await self.node.get_account_resource(address)
        free_bandwidth = account_resources["freeNetLimit"] if "freeNetLimit" in account_resources else 0
        free_bandwidth_used = account_resources["freeNetUsed"] if "freeNetUsed" in account_resources else 0
        total_bandwidth = free_bandwidth - free_bandwidth_used
        return {
            "freeBandwidth": free_bandwidth,
            "freeBandwidthUsed": free_bandwidth_used,
            "totalBandwidth": total_bandwidth
        }

    async def get_account_energy(self, address: TAddress) -> Dict:
        """
        Returns energy data from account.
        :param address: Address of account
        """
        account_resources = await self.node.get_account_resource(address)
        energy = account_resources["EnergyLimit"] if "EnergyLimit" in account_resources else 0
        energy_used = account_resources["EnergyUsed"] if "EnergyUsed" in account_resources else 0
        total_energy = energy - energy_used if energy > 0 and energy_used > 0 else 0
        return {
            "energy": energy,
            "energyUsed": energy_used,
            "totalEnergy": total_energy
        }

    async def get_energy(self, address: TAddress, energy: int) -> int:
        """If the user has enough energy."""
        total_energy = (await self.get_account_energy(address=address))["totalEnergy"]
        if int(total_energy) <= 0:
            return energy
        elif energy - int(total_energy) <= 0:
            return 0
        else:
            return energy - int(total_energy)

    @staticmethod
    def create_wallet(body: BodyCreateWallet) -> ResponseCreateWallet:
        hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=TronMainnet)
        hdwallet.from_mnemonic(mnemonic=body.mnemonicWords, language="english")
        return ResponseCreateWallet(
            mnemonicWords=body.mnemonicWords,
            privateKey=hdwallet.private_key(),
            publicKey=hdwallet.public_key(),
            address=hdwallet.address()
        )


core = NodeCore()
