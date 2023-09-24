from web3 import Web3
import click
import os
import json
from datetime import datetime

from config import DOGECHAIN_NODE_URL, GAS_DOGE, GAS_PRICE, GRIMACE_ABI, contracts

@click.command()
@click.option('--currency')
@click.option('--senders_file')
@click.option('--receiver')
def sendManyToOne(currency, senders_file, receiver):
    contract = contracts.get(currency, None)
    if currency != 'doge' and contract is None:
        print('unknown currency')
        return

    with open(senders_file, 'r') as f:
        sender_private_keys = f.read().split('\n')
        if not sender_private_keys:
            print('no senders read')
            return
        
        
    w3 = Web3(Web3.HTTPProvider(DOGECHAIN_NODE_URL))
    gas_price_wei = w3.to_wei(GAS_PRICE, 'gwei')
    tx_hashes = []
    errors = []
    for private_key in sender_private_keys:
        sender = w3.eth.account.from_key(private_key).address
        try:
            if currency == 'doge':            
                tx_hash = send_doge(w3, private_key, receiver, gas_price_wei)
            elif currency == 'grimace':        
                tx_hash = send_grimace(w3, private_key, receiver, gas_price_wei, contract)        
            tx_hashes.append(tx_hash)
        except Exception as e:
            errors.append(f'Error {sender}: {e}')
    
    if tx_hashes:
        output_file = f'{currency}_{datetime.now().strftime("%m.%d.%Y_%H.%M.%S")}'
        with open(output_file, 'w+') as f:
            f.write('\n'.join([x.hex() for x in tx_hashes]))
        print(f'output_file: {output_file}')
    
    print(f'sent {len(tx_hashes)} transactions')
    if errors:
        for err in errors:
            print(err)

def send_doge(w3, private_key, receiver, gas_price_wei) -> list[str]:
    sender = w3.eth.account.from_key(private_key).address
    balance = w3.eth.get_balance(sender)
    comission = GAS_DOGE*gas_price_wei
    sender_checksum = Web3.to_checksum_address(sender)
    receiver_checksum = Web3.to_checksum_address(receiver)
    nonce = w3.eth.get_transaction_count(sender_checksum)
    amount_gwei = balance-comission
    if amount_gwei <= 0:
        print(f'no funds on {sender}')

    tx = {
        'nonce': nonce,
        'to': receiver_checksum,
        'value': amount_gwei,
        'gas': GAS_DOGE,
        'gasPrice': gas_price_wei,
    }

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash

def send_grimace(w3, private_key, receiver, gas_price_wei, contract) -> list[str]:
    w3_contract = w3.eth.contract(address=contract.address, abi=GRIMACE_ABI)

    account = w3.eth.account.from_key(private_key)
    doge_balance = w3.eth.get_balance(account.address)
    comission = GAS_DOGE*gas_price_wei
    if doge_balance >= comission:
        raise Exception("not enough doge")

    grimace_balance = w3_contract.functions.balanceOf(account.address).call()

    tx = w3_contract.functions.transfer(receiver, grimace_balance).build_transaction({
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': contract.gas,
        'gasPrice': gas_price_wei,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return tx_hash

if __name__ == '__main__':
    sendManyToOne()



