import json
import os

import constants
from app_flask import app
from flask import render_template, request, jsonify
from web3 import Web3
from api import enjin_services

enjin_json_account_list = []
for file in os.listdir('./accounts'):
    if file.endswith('.json'):
        enjin_json_account_list.append(file)
    enjin_json_account_list.sort()
enjin_accounts_list = []
enjin_selected_account_json = enjin_json_account_list[0]
enjin_web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
enjin_prefill_approve_gas = "5"
enjin_buy_gas = "10"
enjin_approve_process_results = []
enjin_approve_contract = ""
enjin_approve_amount = ""
enjin_retry_number = "0"
enjin_buy_time = ""
enjin_retry = 0
buy_process_results = []

enjin_release_contracts = ""
enjin_release_retry_number = "0"
enjin_release_time = ""
enjin_release_retry = 0
release_process_results = []
enjin_release_gas = 10

web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))


def is_finished_approving():
    for account in enjin_approve_process_results:
        if account['state'] == 'Processing':
            return False
    return True


@app.route('/enjin_approve', methods=['POST', 'GET'])
def enjin_approve():
    if request.method == 'GET':
        approve_result = is_finished_approving
        while not approve_result:
            approve_result = is_finished_approving
    elif request.method == 'POST':
        print('Comes Approve POST')
        global enjin_approve_process_results
        enjin_approve_process_results.clear()
        data = request.json
        print(data)
        global enjin_approve_contract
        enjin_approve_contract = str(data['presell_contract'])
        print(enjin_approve_contract)

        global enjin_prefill_approve_gas
        enjin_prefill_approve_gas = str(data['gas'])
        print(enjin_prefill_approve_gas)

        global enjin_approve_amount
        enjin_approve_amount = str(data['approve_amount'])

        prefill_ct = web3.toChecksumAddress(enjin_approve_contract)
        for account in enjin_accounts_list:
            account_data = {
                'account_contract': account['address'],
                'state': 'Processing',
                'tx_id': ''
            }
            enjin_approve_process_results.append(account_data)
            enjin_services.perform_approve(prefill_ct, account_data, enjin_prefill_approve_gas, enjin_approve_amount, account['secret'])

    return jsonify({'result': enjin_approve_process_results})


@app.route('/enjin_buy', methods=['POST', 'GET'])
def enjin_buy():
    global buy_process_results
    if request.method == 'POST':
        print('Comes BUY POST')
        buy_process_results.clear()
        data = request.json
        print(data)
        global enjin_approve_contract
        enjin_approve_contract = str(data['presell_contract'])
        prefill_ct = web3.toChecksumAddress(enjin_approve_contract)
        print(enjin_approve_contract)

        global enjin_buy_gas
        enjin_buy_gas = str(data['gas'])
        print(enjin_buy_gas)

        global enjin_buy_time
        enjin_buy_time = str(data['buy_time'])
        print(enjin_buy_time)

        global enjin_retry
        enjin_retry = str(data['retry_number'])
        print(enjin_retry)

        enjin_services.stop_schedular()

        for account in enjin_accounts_list:
            account_data = {
                'account_contract': account['address'],
                'sol_address': account['sol_address'],
                'state': 'Processing',
                'tx_id': '',
                'retry': int(enjin_retry),
                'number_of_buy': 0,
            }
            buy_process_results.append(account_data)
            enjin_services.perform_buy(prefill_ct, account_data, enjin_buy_gas, enjin_buy_time, account['secret'], len(enjin_accounts_list), bool(data['is_sol']))

    return jsonify({'result': buy_process_results})


@app.route('/enjin_buy_retry', methods=['POST'])
def enjin_buy_retry():
    global buy_process_results
    if request.method == 'POST':
        print('Comes BUY POST')
        data = request.json
        print(data)
        global enjin_approve_contract
        enjin_approve_contract = str(data['presell_contract'])
        prefill_ct = web3.toChecksumAddress(enjin_approve_contract)
        print(enjin_approve_contract)

        global enjin_buy_gas
        enjin_buy_gas = str(data['gas'])
        print(enjin_buy_gas)

        global enjin_buy_time
        enjin_buy_time = str(data['buy_time'])
        print(enjin_buy_time)

        global enjin_retry
        enjin_retry = str(data['retry_number'])
        print(enjin_retry)

        account_retry = data['address_contract']
        for account in buy_process_results:
            if account_retry == account['account_contract']:
                print("Matched")
                secret = ''
                for acc in enjin_accounts_list:
                    if acc['address'] == account_retry:
                        secret = acc['secret']
                account.update({'state': 'Processing', 'tx_id': '', 'retry': 0, 'number_of_buy': 0})
                enjin_services.perform_buy(prefill_ct, account, enjin_buy_gas, enjin_buy_time, secret)

    return jsonify({'result': buy_process_results})


@app.route('/enjin_release', methods=['POST', 'GET'])
def enjin_release():
    global release_process_results
    if request.method == 'POST':
        print('Comes RELEASE POST')
        release_process_results.clear()
        data = request.json
        print(data)
        global web3
        web3 = enjin_services.set_up_chain(data['network'])
        global enjin_release_contracts
        enjin_release_contracts = str(data['release_contract']).split(",")
        # release_ct = web3.toChecksumAddress(enjin_release_contract)
        # print(enjin_approve_contract)

        release_contracts = []
        for contract in enjin_release_contracts:
            release_contracts.append(web3.toChecksumAddress(contract.strip()))

        global enjin_release_gas
        enjin_release_gas = str(data['gas'])
        print(enjin_release_gas)

        global enjin_release_time
        enjin_release_time = str(data['release_time'])
        print(enjin_release_time)

        global enjin_release_retry_number
        enjin_release_retry_number = str(data['retry_number'])
        print(enjin_release_retry_number)

        enjin_services.stop_schedular()

        for account in enjin_accounts_list:
            for release_ct in release_contracts:
                account_data = {
                    'account_contract': account['address'],
                    'state': 'Processing',
                    'tx_id': '',
                    'retry': int(enjin_release_retry_number),
                    'number_of_release': 0,
                    'release_ct': release_ct,
                }
                release_process_results.append(account_data)
                enjin_services.perform_release(release_ct, account_data, enjin_release_gas, enjin_release_time, account['secret'], len(enjin_accounts_list))

    return jsonify({'result': release_process_results})


@app.route('/enjin_release_retry', methods=['POST'])
def enjin_release_retry():
    global release_process_results
    if request.method == 'POST':
        print('Comes RELEASE RETRY')
        release_process_results.clear()
        data = request.json

        release_ct = data['release_ct']
        print(data)
        global web3
        web3 = enjin_services.set_up_chain(data['network'])
        # global enjin_release_contracts
        # enjin_release_contracts = str(data['release_contract']).split(",")
        # release_contracts = []
        # for contract in enjin_release_contracts:
        #     release_contracts.append(web3.toChecksumAddress(contract.strip()))
        # release_ct = web3.toChecksumAddress(enjin_release_contracts)

        global enjin_release_gas
        enjin_release_gas = str(data['gas'])
        print(enjin_release_gas)

        global enjin_release_time
        enjin_release_time = str(data['release_time'])
        print(enjin_release_time)

        global enjin_release_retry_number
        enjin_release_retry_number = str(data['retry_number'])
        print(enjin_release_retry_number)

        account_retry = data['address_contract']
        for account in release_process_results:
            if account_retry == account['account_contract'] and release_ct == account['release_ct']:
                print("Matched")
                secret = ''
                for acc in enjin_accounts_list:
                    if acc['address'] == account_retry:
                        secret = acc['secret']
                account.update({'state': 'Processing', 'tx_id': '', 'retry': 0, 'number_of_release': 0})
                enjin_services.perform_release(release_ct, account, enjin_release_gas, "", secret)

    return jsonify({'result': release_process_results})


@app.route('/enjin', methods=['GET', 'POST'])
def load_page():
    if request.method == 'POST':
        data = request.form
        global enjin_selected_account_json
        enjin_selected_account_json = data.get('account')
        f = open('./accounts/' + enjin_selected_account_json, 'r')
        enjin_account_json = json.loads(f.read())
        global enjin_accounts_list
        enjin_accounts_list = enjin_account_json['accounts']
        for account in enjin_accounts_list:
            print(account['address'])
            print(account['sol_address'])
            print('====')
    return render_template('enjin.html',
                           network_list=constants.NETWORK_LIST,
                           json_account_list=enjin_json_account_list,
                           selected_json=enjin_selected_account_json,
                           accounts_list=enjin_accounts_list,
                           enjin_prefill_approve_gas=enjin_prefill_approve_gas,
                           enjin_buy_gas=enjin_buy_gas,
                           enjin_retry_number=enjin_retry_number,
                           enjin_release_gas=enjin_release_gas,
                           enjin_release_retry_number=enjin_release_retry_number,
                           )
