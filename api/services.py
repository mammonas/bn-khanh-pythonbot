import _thread
import time

from web3 import Web3
from eth_utils.units import units, decimal
from apscheduler.schedulers.background import BackgroundScheduler

import constants
import sys
from datetime import datetime

pre_json = open('token_abi.json', 'r').read().replace('\n', '')
pre_json_router = open('router_abi.json', 'r').read().replace('\n', '')
pre_json_avax_router = open('router_avax_abi.json', 'r').read().replace('\n', '')
pre_json_factory = open('factory_abi.json', 'r').read().replace('\n', '')
pre_json_pair = open('pair_abi.json', 'r').read().replace('\n', '')
web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
spender_address = ''
spender_address_contract = ''
scan_endpoint = 'https://bscscan.com/tx/'
factory_address = ''
factory_address_contract = ''
selected_network = 'BSC'
selected_chain_id = 56
DEC = 10 ** 18

print(sys.getrecursionlimit())
sys.setrecursionlimit(10**9)
print(sys.getrecursionlimit())

IS_CONTINUE_SELLING = False
sell_scheduler = BackgroundScheduler(daemon=True)


def set_up_chain(chain):
    global web3
    global spender_address
    global spender_address_contract
    global scan_endpoint
    global factory_address
    global factory_address_contract
    global selected_network
    global selected_chain_id
    if chain == 'POLYGON':
        selected_network = 'POLYGON'
        web3 = Web3(Web3.HTTPProvider(constants.POLYGON_NODE))
        spender_address = web3.toChecksumAddress(constants.QUICKSWAP_ROUTE_ADDRESS)
        factory_address = web3.toChecksumAddress(constants.QUICKSWAP_FACTORY_ADDRESS)
        print("Switched to polygon")
        print(web3.isConnected())
        scan_endpoint = 'https://polygonscan.com/tx/'
        selected_chain_id = 137
    elif chain == 'AVAX':
        selected_network = 'AVAX'
        web3 = Web3(Web3.HTTPProvider(constants.AVAX_NODE))
        spender_address = web3.toChecksumAddress(constants.TRANDERJOE_ROUTE_ADDRESS)
        factory_address = web3.toChecksumAddress(constants.TRANDERJOE_FACTORY_ADDRESS)
        print("Switched to AVAX")
        print(web3.isConnected())
        scan_endpoint = 'https://snowtrace.io/tx/'
        selected_chain_id = 43114
    else:
        selected_network = 'BSC'
        web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
        spender_address = web3.toChecksumAddress(constants.PANCAKE_ROUTE_ADDRESS)
        factory_address = web3.toChecksumAddress(constants.PANCAKE_FACTORY_ADDRESS)
        print("Switched to bsc")
        print(web3.isConnected())
        scan_endpoint = 'https://bscscan.com/tx/'
        selected_chain_id = 56
    spender_address_contract = web3.eth.contract(address=spender_address, abi=pre_json_router)
    if selected_network == 'AVAX':
        spender_address_contract = web3.eth.contract(address=spender_address, abi=pre_json_avax_router)
    factory_address_contract = web3.eth.contract(address=factory_address, abi=pre_json_factory)
    return web3


def is_reserve_good(token, reserve):
    if selected_network == "POLYGON" and (str(token).lower() == '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'.lower() or str(token).lower() == '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'.lower()):
        amount = web3.fromWei(reserve, 'mwei')
    elif selected_network == "AVAX":
        if str(token).lower() in ['0xc7198437980c041c805a1edcba50c1ce5db95118'.lower(), '0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664'.lower(), '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e'.lower()]:
            amount = web3.fromWei(reserve, 'mwei')
        else:
            amount = web3.fromWei(reserve, 'ether')
    else:
        amount = web3.fromWei(reserve, 'ether')
    if str(token).lower() == "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c".lower():  # BNB
        print("Amount BNB %s" % amount)
        return amount >= 5
    elif str(token).lower() == "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270".lower():  # Matic
        print("Amount MATIC %s" % amount)
        return amount >= 2000
    elif str(token).lower() == "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7".lower():  # AVAX
        print("Amount AVAX %s" % amount)
        return amount >= 30
    elif str(token).lower() in constants.STABLE_COIN_LIST:
        print("Amount stable coin %s" % amount)
        return amount >= 5000
    else:  # normal token
        print("Amount %s %s" % (token, amount))
        return amount > 0


def is_pair_good(token, des_token):
    print("Comes check pair")
    pair_address = factory_address_contract.functions.getPair(token, web3.toChecksumAddress(des_token)).call()
    print(pair_address)
    if str(pair_address) == "0x0000000000000000000000000000000000000000":
        print("Pair Not Found")
        return False
    else:
        print("Pair Found")
        pair_contract = web3.eth.contract(address=pair_address, abi=pre_json_pair)
        (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()
        if str(token0).lower() == str(token).lower():
            is_good = is_reserve_good(token, reserve0) and is_reserve_good(des_token, reserve1)
        else:
            is_good = is_reserve_good(token, reserve1) and is_reserve_good(des_token, reserve0)
        return is_good


def auto_find_pair(token):
    currency_list = constants.SELL_BSC_LIST
    if selected_network == 'POLYGON':
        currency_list = constants.SELL_POLYGON_LIST
    elif selected_network == 'AVAX':
        currency_list = constants.SELL_AVAX_LIST
    for currency in currency_list:
        if is_pair_good(token, currency['contract']):
            print("Found good pair: %s-%s" % (token, currency['name']))
            return currency['contract']
        else:
            print("Pair: %s-%s isn't good" % (token, currency['name']))
    return None


def perform_approve(token, account_data, gas, private_key):
    _thread.start_new_thread(approve, (token, account_data, gas, private_key))
    print('End of perform_approve')


def approve(token, account_data, gas, private_key):
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    max_amount = web3.toWei(constants.UNLIMITED_AMOUNT, 'ether')
    nonce = web3.eth.getTransactionCount(wallet_address)
    token_contract = web3.eth.contract(address=token, abi=pre_json)
    # check allowance first
    allowance = token_contract.functions.allowance(wallet_address, spender_address).call()
    print("Allowance: %s" % allowance)
    if allowance == 0:
        tx = token_contract.functions.approve(spender_address, max_amount).buildTransaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 250000,
            'gasPrice': web3.toWei(gas, 'gwei'),
        })
        print('tx')
        print(tx)
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
        print('tx_hash: ' + web3.toHex(tx_hash))
        wait_for_receipt_approve(web3.toHex(tx_hash), account_data)
    else:
        account_data['state'] = 'Already Approved'


def wait_for_receipt_approve(tx_hash, account_data):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=6000)
    if receipt:
        print(receipt)
        if receipt['status'] is not None:
            print(int(receipt['status']))
            if int(receipt['status']) == 1:
                print('Success!!!')
                account_data['state'] = 'Success'
            else:
                print('Failed!!!')
                account_data['state'] = 'Failed'
    else:
        print('Still waiting...')
        time.sleep(0.5)
        wait_for_receipt_approve(tx_hash, account_data)


def wait_for_receipt(tx_hash, account_data, token, des_token, gas, private_key):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=6000)
    if receipt:
        print(receipt)
        if receipt['status'] is not None:
            print(int(receipt['status']))
            if int(receipt['status']) == 1:
                print('Success!!!')
                with open("results.txt", "a") as file_object:
                    data = '\nSuccess: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract'] + '\n' + account_data['tx_id']
                    file_object.write(data)
                    file_object.close()
                if IS_CONTINUE_SELLING:
                    print('Continue Sell Again')
                    sell(token, des_token, account_data, gas, private_key, auto_find=False, check_good_pair=False)
                else:
                    account_data['state'] = 'Success'
            else:
                print('Failed!!!')
                account_data['state'] = 'Failed'
                with open("results.txt", "a") as file_object:
                    data = '\nFailed: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract'] + '\n' + account_data['tx_id']
                    file_object.write(data)
                    file_object.close()
    else:
        print('Still waiting...')
        time.sleep(0.5)
        wait_for_receipt(tx_hash, account_data, token, des_token, gas, private_key)


def decimal_(mdecimal):
    for name, places in units.items():
        if places == (10 ** mdecimal):
            return name
    # not found, must add a new unit
    new_unit = "1" + str("0" * mdecimal)
    units.update({
        "new_unit": decimal.Decimal(new_unit)
    })
    return "new_unit"


def stop_schedular():
    if sell_scheduler.state != 0:
        sell_scheduler.shutdown()
        print("Stop Selling Schedular")


def perform_sell(token, des_token, sell_time, account_data, gas, private_key, total_account, auto_find=False, check_good_pair=True):
    if sell_time == "":
        _thread.start_new_thread(sell, (token, des_token, account_data, gas, private_key, auto_find, check_good_pair))
    else:
        tt = str(sell_time).split(":")
        h = int(tt[0])
        m = int(tt[1])
        print("Here is")
        print(h)
        print(m)
        sell_scheduler.add_job(sell,
                          args=[token, des_token, account_data, gas, private_key, auto_find, check_good_pair],
                          run_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                            h, m, 0))
        if len(sell_scheduler.get_jobs()) == total_account:
            sell_scheduler.start()
            print("Added selling to scheduler and started")
    print('End of perform_sell')


def sell(token, des_token, account_data, gas, private_key, auto_find=False, check_good_pair=True):
    try:
        print('Come check candidate destination token')
        if auto_find:
            des_token = auto_find_pair(token)
            while not des_token:
                des_token = auto_find_pair(token)
            print("Candidate Token is %s" % des_token)
        else:
            # Check is pair good or not
            if check_good_pair:
                is_good = is_pair_good(token, web3.toChecksumAddress(des_token))
                while not is_good:
                    is_good = is_pair_good(token, web3.toChecksumAddress(des_token))

        print("After checking, now perform check wallet balance and sell!!!")
        token_contract = web3.eth.contract(address=token, abi=pre_json)
        wallet_address = web3.toChecksumAddress(account_data['account_contract'])
        token_balance = token_contract.functions.balanceOf(wallet_address).call()

        # sorry, sometimes I mess things up LOL, no need to do this to save time
        # token_decimal = token_contract.functions.decimals().call()
        # token_wei_unit_name = decimal_(token_decimal)
        # token_balance_human = "{:.5f}".format(web3.fromWei(token_balance, token_wei_unit_name))

        print('Balance ' + account_data['account_contract'])
        print(token_balance)
        with open("sell.txt", "a") as file_object:
            data = '\nNow is in sell and still in waiting balance: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract']
            file_object.write(data)
            file_object.close()
        if float(token_balance) >= 1.0:
            execute_sell(token, des_token, account_data, gas, token_balance, private_key)
        else:
            time.sleep(0.5)
            sell(token, des_token, account_data, gas, private_key, False, False)
    except:
        time.sleep(0.5)
        sell(token, des_token, account_data, gas, private_key, False, False)


def execute_sell(token, des_token, account_data, gas, amount, private_key):
    print('NOW SELLLL')
    des_contract = web3.toChecksumAddress(des_token)
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    nonce = web3.eth.getTransactionCount(wallet_address)
    print(token)
    print(des_contract)
    if des_contract == '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c' or des_contract == '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270':
        print("Go swapExactTokensForETH")
        tx = spender_address_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
          amount, 0,
          [token, des_contract],
          wallet_address,
          (int(time.time()) + 1000000)
        )
    else:
        print('Comes check here')
        print(selected_network)
        print(des_contract)
        print(selected_network == 'AVAX')
        print(des_contract.lower() == '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7'.lower())
        if selected_network == 'AVAX' and des_contract.lower() == '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7'.lower():
            print("Go swapExactTokensForAVAXSupportingFeeOnTransferTokens")
            tx = spender_address_contract.functions.swapExactTokensForAVAXSupportingFeeOnTransferTokens(
                amount, 0,
                [token, des_contract],
                wallet_address,
                (int(time.time()) + 1000000)
            )
        else:
            print("Go swapExactTokensForTokens")
            tx = spender_address_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                amount, 0,
                [token, des_contract],
                wallet_address,
                (int(time.time()) + 1000000)
            )
    tx = tx.buildTransaction({
      'from': wallet_address,
      'gas': 250000,
      'gasPrice': web3.toWei(gas, 'gwei'),
      'nonce': nonce,
    })
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
    print('tx_hash: ' + web3.toHex(tx_hash))
    wait_for_receipt(web3.toHex(tx_hash), account_data, token, des_token, gas, private_key)


def perform_transfer(token, to_address, transfer_time, account_data, gas, private_key, total_account):
    if transfer_time == "":
        _thread.start_new_thread(transfer, (token, to_address, account_data, gas, private_key))
    else:
        tt = str(transfer_time).split(":")
        h = int(tt[0])
        m = int(tt[1])
        print("Here is")
        print(h)
        print(m)
        sell_scheduler.add_job(transfer,
                          args=[token, to_address, account_data, gas, private_key],
                          run_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                            h, m, 0))
        if len(sell_scheduler.get_jobs()) == total_account:
            sell_scheduler.start()
            print("Added transfer to scheduler and started")
    print('End of perform_transfer')


def transfer(token, to_address, account_data, gas, private_key):
    token_contract = web3.eth.contract(address=token, abi=pre_json)
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    token_balance = token_contract.functions.balanceOf(wallet_address).call()
    print('Balance ' + account_data['account_contract'])
    print(token_balance)
    with open("transfer.txt", "a") as file_object:
        data = '\nNow is in transfer and still in waiting balance: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract']
        file_object.write(data)
        file_object.close()
    if float(token_balance) >= 1.0:
        execute_transfer(token_contract, to_address, account_data, gas, token_balance, private_key)
    else:
        time.sleep(0.5)
        transfer(token, to_address, account_data, gas, private_key)


def execute_transfer(token_contract, to_address, account_data, gas, amount, private_key):
    print('NOW Transfer')
    to_contract = web3.toChecksumAddress(to_address)
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    nonce = web3.eth.getTransactionCount(wallet_address)
    print(token_contract)
    print(to_contract)

    tx = token_contract.functions.transfer(to_contract, amount).buildTransaction({
        'chainId': selected_chain_id,
        'from': wallet_address,
        'gas': 250000,
        'gasPrice': web3.toWei(gas, 'gwei'),
        'nonce': nonce,
    })
    signed_tx = web3.eth.account.signTransaction(tx, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
    print('tx_hash: ' + web3.toHex(tx_hash))
    wait_for_receipt_approve(web3.toHex(tx_hash), account_data)
