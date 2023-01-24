import _thread
import time
from datetime import datetime

from web3 import Web3
from apscheduler.schedulers.background import BackgroundScheduler

import constants
import sys
from time import sleep

pre_json = open('token_abi.json', 'r').read().replace('\n', '')
pre_json_router = open('router_abi.json', 'r').read().replace('\n', '')
pre_json_enjin_contract = open('enjin_presale_abi.json', 'r').read().replace('\n', '')
pre_with_sol_json_enjin_contract = open('enjin_presale_abi_with_sol.json', 'r').read().replace('\n', '')
pre_json_enjin_release_contract = open('enjin_release_abi.json', 'r').read().replace('\n', '')
web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
spender_address = ''
spender_address_contract = ''
scan_endpoint = 'https://bscscan.com/tx/'
BUSD = '0xe9e7cea3dedca5984780bafc599bd69add087d56'

print(sys.getrecursionlimit())
sys.setrecursionlimit(10 ** 9)
print(sys.getrecursionlimit())

scheduler = BackgroundScheduler(daemon=True)


def set_up_chain(chain):
    global web3
    global spender_address
    global spender_address_contract
    global scan_endpoint
    if chain == 'POLYGON':
        web3 = Web3(Web3.HTTPProvider(constants.POLYGON_NODE))
        spender_address = web3.toChecksumAddress(constants.QUICKSWAP_ROUTE_ADDRESS)
        print("Switched to polygon")
        print(web3.isConnected())
        scan_endpoint = 'https://polygonscan.com/tx/'
    else:
        web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
        spender_address = web3.toChecksumAddress(constants.PANCAKE_ROUTE_ADDRESS)
        print("Switched to bsc")
        print(web3.isConnected())
        scan_endpoint = 'https://bscscan.com/tx/'
    spender_address_contract = web3.eth.contract(address=spender_address, abi=pre_json_router)
    return web3


def perform_approve(prefill_ct, account_data, enjin_prefill_approve_gas, enjin_approve_amount, private_key):
    _thread.start_new_thread(approve,
                             (prefill_ct, account_data, enjin_prefill_approve_gas, enjin_approve_amount, private_key))
    print('End of enjin_perform_approve')


def approve(prefill_ct, account_data, gas, busd_amount, private_key):
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    max_amount = web3.toWei(busd_amount, 'ether')
    nonce = web3.eth.getTransactionCount(wallet_address)
    token_contract = web3.eth.contract(address=web3.toChecksumAddress(BUSD), abi=pre_json)
    tx = token_contract.functions.approve(prefill_ct, max_amount).buildTransaction({
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
    wait_for_receipt(web3.toHex(tx_hash), account_data)


def wait_for_receipt(tx_hash, account_data):
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
        wait_for_receipt(tx_hash, account_data)


def wait_for_buy_receipt(tx_hash, account_data, prefill_ct, buy_gas, buy_time, private_key):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=6000)
    if receipt:
        print(receipt)
        if receipt['status'] is not None:
            print(int(receipt['status']))
            if int(receipt['status']) == 1:
                print('Success!!!')
                account_data['state'] = 'Success'
                with open("enjin.txt", "a") as file_object:
                    data = '\nBuy Success: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract'] + '\n' + account_data['tx_id']
                    file_object.write(data)
                    file_object.close()
            else:
                print('Failed!!!')
                if account_data['number_of_buy'] < account_data['retry']:
                    account_data['number_of_buy'] += 1
                    buy(prefill_ct, account_data, buy_gas, buy_time, private_key)
                else:
                    account_data['state'] = 'Failed'
                    with open("enjin.txt", "a") as file_object:
                        data = '\nBuy Failed: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                               account_data['account_contract'] + '\n' + account_data['tx_id']
                        file_object.write(data)
                        file_object.close()
    else:
        print('Still waiting...')
        time.sleep(0.5)
        wait_for_buy_receipt(tx_hash, account_data, prefill_ct, buy_gas, buy_time, private_key)


def stop_schedular():
    if scheduler.state != 0:
        scheduler.shutdown()
        print("Stop Schedular")


def perform_buy(prefill_ct, account_data, enjin_buy_gas, enjin_buy_time, private_key, total_account=0, is_sol=False):
    if enjin_buy_time == "":
        _thread.start_new_thread(buy, (prefill_ct, account_data, enjin_buy_gas, enjin_buy_time, private_key, is_sol))
    else:
        tt = str(enjin_buy_time).split(":")
        h = int(tt[0])
        m = int(tt[1])
        print("Here is")
        print(h)
        print(m)
        scheduler.add_job(buy,
                          args=[prefill_ct, account_data, enjin_buy_gas, "", private_key, is_sol],
                          run_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                            h, m, 3))
        if len(scheduler.get_jobs()) == total_account:
            scheduler.start()
            print("Added to schedular and started")
    print('End of perform_sell')


def buy(prefill_ct, account_data, buy_gas, buy_time, private_key, is_sol=False):
    print('Comes buy')
    print(datetime.now())
    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    nonce = web3.eth.getTransactionCount(wallet_address)
    if is_sol:
        token_contract = web3.eth.contract(address=prefill_ct, abi=pre_with_sol_json_enjin_contract)
    else:
        token_contract = web3.eth.contract(address=prefill_ct, abi=pre_json_enjin_contract)
    busd_address = web3.toChecksumAddress(BUSD)
    if buy_time == "":
        if is_sol:
            tx = token_contract.functions.buyTokens(busd_address, Web3.toWei("0.000000000000000001", 'ether'), account_data['sol_address']).buildTransaction({
                'from': wallet_address,
                'gas': 250000,
                'gasPrice': web3.toWei(buy_gas, 'gwei'),
                'nonce': nonce,
            })
        else:
            tx = token_contract.functions.buyTokens(busd_address, Web3.toWei("0.000000000000000001", 'ether')).buildTransaction({
                'from': wallet_address,
                'gas': 250000,
                'gasPrice': web3.toWei(buy_gas, 'gwei'),
                'nonce': nonce,
            })
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        try:
            tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        except ValueError as e:
            # Error when sending raw: {'code': -32000, 'message': 'tx fee (2000000.00 ether) exceeds the configured cap (1.00 ether)'}
            # 'tx fee (25000000000000000000.00 ether) exceeds the configured cap (1.00 ether)'}
            print("Error when sending raw: " + str(e))
            with open("enjin.txt", "a") as file_object:
                data = '\nError when buying: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                       account_data['account_contract'] + '\n' + str(e)
                file_object.write(data)
                file_object.close()
            time.sleep(0.5)
            buy(prefill_ct, account_data, buy_gas, buy_time, private_key)

        account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
        print('tx_hash: ' + web3.toHex(tx_hash))
        wait_for_buy_receipt(web3.toHex(tx_hash), account_data, prefill_ct, buy_gas, buy_time, private_key)


def wait_for_release_receipt(tx_hash, account_data, prefill_ct, release_gas, release_time, private_key):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=6000)
    if receipt:
        print(receipt)
        if receipt['status'] is not None:
            print(int(receipt['status']))
            if int(receipt['status']) == 1:
                print('Success!!!')
                account_data['state'] = 'Success'
                with open("enjin.txt", "a") as file_object:
                    data = '\nRelease Success: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + account_data['account_contract'] + '\n' + account_data['tx_id']
                    file_object.write(data)
                    file_object.close()
            else:
                print('Failed!!!')
                if account_data['number_of_release'] < account_data['retry']:
                    account_data['number_of_release'] += 1
                    release(prefill_ct, account_data, release_gas, release_time, private_key)
                else:
                    account_data['state'] = 'Failed'
                    with open("enjin.txt", "a") as file_object:
                        data = '\nRelease Failed: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                               account_data['account_contract'] + '\n' + account_data['tx_id']
                        file_object.write(data)
                        file_object.close()
    else:
        print('Still waiting...')
        time.sleep(0.5)
        wait_for_release_receipt(tx_hash, account_data, prefill_ct, release_gas, release_time, private_key)


def perform_release(release_ct, account_data, enjin_release_gas, enjin_release_time, private_key, total_account):
    if enjin_release_time == "":
        _thread.start_new_thread(release, (release_ct, account_data, enjin_release_gas, enjin_release_time, private_key))
    else:
        tt = str(enjin_release_time).split(":")
        h = int(tt[0])
        m = int(tt[1])
        print("Here is")
        print(h)
        print(m)
        scheduler.add_job(release,
                          args=[release_ct, account_data, enjin_release_gas, "", private_key],
                          run_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                            h, m, 2))
        if len(scheduler.get_jobs()) == total_account:
            scheduler.start()
            print("Added to schedulrr and started release")
    print('End of perform_release')


def release(release_ct, account_data, enjin_release_gas, enjin_release_time, private_key):
    print('Comes release')

    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    nonce = web3.eth.getTransactionCount(wallet_address)
    token_contract = web3.eth.contract(address=release_ct, abi=pre_json_enjin_release_contract)
    if enjin_release_time == "":
        tx = token_contract.functions.release().buildTransaction({
            'from': wallet_address,
            'gas': 250000,
            'gasPrice': web3.toWei(enjin_release_gas, 'gwei'),
            'nonce': nonce,
        })
        signed_tx = web3.eth.account.signTransaction(tx, private_key)
        try:
            tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        except ValueError as e:
            # Error when sending raw: {'code': -32000, 'message': 'tx fee (2000000.00 ether) exceeds the configured cap (1.00 ether)'}
            # 'tx fee (25000000000000000000.00 ether) exceeds the configured cap (1.00 ether)'}
            print("Error when sending raw: " + str(e))
            time.sleep(0.5)
            with open("enjin.txt", "a") as file_object:
                data = '\nError when releasing: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                       account_data['account_contract'] + '\n' + str(e)
                file_object.write(data)
                file_object.close()
            release(release_ct, account_data, enjin_release_gas, enjin_release_time, private_key)

        account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
        print('tx_hash: ' + web3.toHex(tx_hash))
        wait_for_release_receipt(web3.toHex(tx_hash), account_data, release_ct, enjin_release_gas, enjin_release_time,
                                 private_key)
