import _thread
import time
from datetime import datetime

from web3 import Web3
from apscheduler.schedulers.background import BackgroundScheduler

import constants
import sys
from time import sleep

pre_json_starter_release_contract = open('starter_presale_abi.json', 'r').read().replace('\n', '')
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
    return web3


def stop_schedular():
    if scheduler.state != 0:
        scheduler.shutdown()
        print("Stop Schedular")


def wait_for_release_receipt(tx_hash, account_data, prefill_ct, release_gas, release_time, private_key):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=6000)
    if receipt:
        print(receipt)
        if receipt['status'] is not None:
            print(int(receipt['status']))
            if int(receipt['status']) == 1:
                print('Success!!!')
                account_data['state'] = 'Success'
                with open("starter.txt", "a") as file_object:
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
                    with open("starter.txt", "a") as file_object:
                        data = '\nRelease Failed: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                               account_data['account_contract'] + '\n' + account_data['tx_id']
                        file_object.write(data)
                        file_object.close()
    else:
        print('Still waiting...')
        time.sleep(0.5)
        wait_for_release_receipt(tx_hash, account_data, prefill_ct, release_gas, release_time, private_key)


def perform_release(release_ct, account_data, starter_release_gas, starter_release_time, private_key, total_account):
    if starter_release_time == "":
        _thread.start_new_thread(release, (release_ct, account_data, starter_release_gas, starter_release_time, private_key))
    else:
        tt = str(starter_release_time).split(":")
        h = int(tt[0])
        m = int(tt[1])
        print("Here is")
        print(h)
        print(m)
        scheduler.add_job(release,
                          args=[release_ct, account_data, starter_release_gas, "", private_key],
                          run_date=datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                            h, m, 2))
        if len(scheduler.get_jobs()) == total_account:
            scheduler.start()
            print("Added to schedulrr and started release")
    print('End of perform_release')


def release(release_ct, account_data, starter_release_gas, starter_release_time, private_key):
    print('Comes release')

    wallet_address = web3.toChecksumAddress(account_data['account_contract'])
    nonce = web3.eth.getTransactionCount(wallet_address)
    token_contract = web3.eth.contract(address=release_ct, abi=pre_json_starter_release_contract)
    if starter_release_time == "":
        tx = token_contract.functions.claimTokens().buildTransaction({
            'from': wallet_address,
            'gas': 250000,
            'gasPrice': web3.toWei(starter_release_gas, 'gwei'),
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
            with open("starter.txt", "a") as file_object:
                data = '\nError when releasing: ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + \
                       account_data['account_contract'] + '\n' + str(e)
                file_object.write(data)
                file_object.close()
            release(release_ct, account_data, starter_release_gas, starter_release_time, private_key)

        account_data['tx_id'] = scan_endpoint + web3.toHex(tx_hash)
        print('tx_hash: ' + web3.toHex(tx_hash))
        wait_for_release_receipt(web3.toHex(tx_hash), account_data, release_ct, starter_release_gas, starter_release_time,
                                 private_key)
