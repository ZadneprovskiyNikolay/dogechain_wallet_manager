from contract import Contract
import json

DOGECHAIN_NODE_URL = 'https://rpc.dogechain.dog'

contracts = {
    'grimace': Contract('grimace', '0x2f90907fD1DC1B7a484b6f31Ddf012328c2baB28', 18, 41515),
}

GAS_DOGE = 21000
GAS_PRICE = 250

with open('grimace_abi.json', 'r') as f:
    GRIMACE_ABI = json.load(f)