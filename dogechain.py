from web3 import Web3
import click
import os
import json
from datetime import datetime

from config import DOGECHAIN_NODE_URL, GAS_DOGE, GAS_PRICE, contracts

@click.command()
@click.option('--currency')
@click.option('--senders_file')
@click.option('--receiver')
def sendManyToOne(currency, senders_file, receiver):
    contract = contracts.get(currency, None)
    if currency != 'doge' and currency is None:
        print('unknown currency')
        return

    with open(senders_file, 'r') as f:
        sender_private_keys = f.read().split('\n')
        if not sender_private_keys:
            print('no senders read')
            return
        
    tx_hashes = []
        
    w3 = Web3(Web3.HTTPProvider(DOGECHAIN_NODE_URL))
    gas_price_wei = w3.to_wei(GAS_PRICE, 'gwei')
    if currency == 'doge':            
        for private_key in sender_private_keys:
            sender = w3.eth.account.from_key(private_key).address
            balance = w3.eth.get_balance(sender)

            sender_checksum = Web3.to_checksum_address(sender)
            receiver_checksum = Web3.to_checksum_address(receiver)

            nonce = w3.eth.get_transaction_count(sender_checksum)
            
            amount_gwei = balance-(GAS_DOGE*gas_price_wei)
            if amount_gwei <= 0:
                print(f'no funds on {sender}')
                continue
            tx = {
                'nonce': nonce,
                'to': receiver_checksum,
                'value': amount_gwei,
                'gas': GAS_DOGE,
                'gasPrice': gas_price_wei,
            }

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hashes.append(tx_hash)

    elif currency == 'grimace':        
            
        with open('grimace_abi.json', 'r') as f:
            token_contract_abi = json.load(f)

        w3_contract = w3.eth.contract(address=contract.address, abi=token_contract_abi)

        for private_key in sender_private_keys:
            account = w3.eth.account.from_key(private_key)
            sender_token_balance = w3_contract.functions.balanceOf(account.address).call()

            tx = w3_contract.functions.transfer(receiver, sender_token_balance).build_transaction({
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': contract.gas,
                'gasPrice': gas_price_wei,
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hashes.append(tx_hash)

    if tx_hashes:
        output_file = f'{currency}_{datetime.now().strftime("%m_%d_%Y_%H:%M:%S")}'
        with open(output_file, 'w+') as f:
            f.write('\n'.join([x.hex() for x in tx_hashes]))
        print(f'output_file: {output_file}')
    
    print(f'sent {len(tx_hashes)} transactions')

if __name__ == '__main__':
    sendManyToOne()



