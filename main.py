import time
import random
from web3 import Web3

### === НАСТРОЙКИ === ###
RPC_URL = "https://eth.llamarpc.com"  # RPC URL для Ethereum
CONTRACT_ADDRESS = "0xd19d4B5d358258f05D7B411E21A1460D11B0876F"
PERCENT_RANGE = (1, 1)  # Процент баланса, например от 1% до 3%
DELAY_RANGE = (5, 15)   # Задержка между транзакциями в секундах

KEYS_FILE = "keys.txt"
CHAIN_ID = 1  # Ethereum mainnet

# ABI только с sendMessage
contract_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "_to", "type": "address"},
            {"internalType": "uint256", "name": "_fee", "type": "uint256"},
            {"internalType": "bytes", "name": "_calldata", "type": "bytes"},
        ],
        "name": "sendMessage",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]

# Подключение к RPC
web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise ConnectionError("Не удалось подключиться к RPC")

# Загрузка приватных ключей
def load_keys(file_path):
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Получение текущих gas параметров по EIP-1559
def get_gas_fees():
    base_fee = web3.eth.fee_history(1, "latest")["baseFeePerGas"][-1]
    priority_fee = web3.to_wei(2, "gwei")
    max_fee = base_fee + 2 * priority_fee
    return {
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee
    }

# Отправка транзакции
def send_bridge_transaction(private_key):
    acct = web3.eth.account.from_key(private_key)
    address = acct.address
    balance = web3.eth.get_balance(address)

    if balance == 0:
        print(f"[{address}] Баланс 0 — пропуск")
        return

    percent = random.randint(*PERCENT_RANGE)
    value = balance * percent // 100
    if value == 0:
        print(f"[{address}] Слишком маленький баланс для {percent}% — пропуск")
        return

    print(f"[{address}] Баланс: {web3.from_wei(balance, 'ether')} ETH, отправляем {percent}% → {web3.from_wei(value, 'ether')} ETH")

    contract = web3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=contract_abi
    )

    nonce = web3.eth.get_transaction_count(address)
    gas_estimate = contract.functions.sendMessage(address, 0, b'').estimate_gas({
        "from": address,
        "value": value
    })

    gas_fees = get_gas_fees()

    txn = contract.functions.sendMessage(address, 0, b'').build_transaction({
        "from": address,
        "value": value,
        "nonce": nonce,
        "chainId": CHAIN_ID,
        "gas": int(gas_estimate * 1.2),
        "maxFeePerGas": gas_fees["maxFeePerGas"],
        "maxPriorityFeePerGas": gas_fees["maxPriorityFeePerGas"]
    })

    signed = web3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"[{address}] Транзакция отправлена: {web3.to_hex(tx_hash)}")

# Главный цикл
def main():
    keys = load_keys(KEYS_FILE)
    for key in keys:
        try:
            send_bridge_transaction(key)
        except Exception as e:
            print(f"[ОШИБКА] {str(e)}")
        delay = random.randint(*DELAY_RANGE)
        print(f"⏳ Ждём {delay} сек...\n")
        time.sleep(delay)

if __name__ == "__main__":
    main()
