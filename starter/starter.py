import json
import os

import constants
from app_flask import app
from flask import render_template, request, jsonify
from web3 import Web3
from api import starter_services

starter_json_account_list = []
for file in os.listdir('./accounts'):
    if file.endswith('.json'):
        starter_json_account_list.append(file)
    starter_json_account_list.sort()
starter_accounts_list = []
starter_selected_account_json = starter_json_account_list[0]
starter_web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))

starter_release_contracts = ""
starter_release_retry_number = "0"
starter_release_time = ""
starter_release_retry = 0
release_process_results = []
starter_release_gas = 10

web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))


@app.route('/starter_release', methods=['POST', 'GET'])
def starter_release():
    global release_process_results
    if request.method == 'POST':
        print('Comes RELEASE POST')
        release_process_results.clear()
        data = request.json
        print(data)
        global web3
        web3 = starter_services.set_up_chain(data['network'])
        global starter_release_contracts
        starter_release_contracts = str(data['release_contract']).split(",")

        release_contracts = []
        for contract in starter_release_contracts:
            release_contracts.append(web3.toChecksumAddress(contract.strip()))

        global starter_release_gas
        starter_release_gas = str(data['gas'])
        print(starter_release_gas)

        global starter_release_time
        starter_release_time = str(data['release_time'])
        print(starter_release_time)

        global starter_release_retry_number
        starter_release_retry_number = str(data['retry_number'])
        print(starter_release_retry_number)

        starter_services.stop_schedular()

        for account in starter_accounts_list:
            for release_ct in release_contracts:
                account_data = {
                    'account_contract': account['address'],
                    'state': 'Processing',
                    'tx_id': '',
                    'retry': int(starter_release_retry_number),
                    'number_of_release': 0,
                    'release_ct': release_ct,
                }
                release_process_results.append(account_data)
                starter_services.perform_release(release_ct, account_data, starter_release_gas, starter_release_time, account['secret'], len(starter_accounts_list))

    return jsonify({'result': release_process_results})


@app.route('/starter_release_retry', methods=['POST'])
def starter_release_retry():
    global release_process_results
    if request.method == 'POST':
        print('Comes RELEASE RETRY')
        release_process_results.clear()
        data = request.json

        release_ct = data['release_ct']
        print(data)
        global web3
        web3 = starter_services.set_up_chain(data['network'])

        global starter_release_gas
        starter_release_gas = str(data['gas'])
        print(starter_release_gas)

        global starter_release_time
        starter_release_time = str(data['release_time'])
        print(starter_release_time)

        global starter_release_retry_number
        starter_release_retry_number = str(data['retry_number'])
        print(starter_release_retry_number)

        account_retry = data['address_contract']
        for account in release_process_results:
            if account_retry == account['account_contract'] and release_ct == account['release_ct']:
                print("Matched")
                secret = ''
                for acc in starter_accounts_list:
                    if acc['address'] == account_retry:
                        secret = acc['secret']
                account.update({'state': 'Processing', 'tx_id': '', 'retry': 0, 'number_of_release': 0})
                starter_services.perform_release(release_ct, account, starter_release_gas, "", secret)

    return jsonify({'result': release_process_results})


@app.route('/starter', methods=['GET', 'POST'])
def starter_load_page():
    if request.method == 'POST':
        data = request.form
        global starter_selected_account_json
        starter_selected_account_json = data.get('account')
        f = open('./accounts/' + starter_selected_account_json, 'r')
        starter_account_json = json.loads(f.read())
        global starter_accounts_list
        starter_accounts_list = starter_account_json['accounts']
        for account in starter_accounts_list:
            print(account['address'])
            print(account['sol_address'])
            print('====')
    return render_template('starter.html',
                           network_list=constants.NETWORK_LIST,
                           json_account_list=starter_json_account_list,
                           selected_json=starter_selected_account_json,
                           accounts_list=starter_accounts_list,
                           starter_release_gas=starter_release_gas,
                           starter_release_retry_number=starter_release_retry_number,
                           )
