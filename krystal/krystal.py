import json
import os

import constants
from app_flask import app
from flask import render_template, request, jsonify
from web3 import Web3
from api import krystal_services

krystal_json_account_list = []
for file in os.listdir('./accounts'):
    if file.endswith('.json'):
        krystal_json_account_list.append(file)
    krystal_json_account_list.sort()
krystal_accounts_list = []
krystal_selected_account_json = krystal_json_account_list[0]
krystal_web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))

krystal_pool_id = ""
krystal_release_retry_number = "0"
krystal_release_time = ""
krystal_release_retry = 0
release_process_results = []
krystal_release_gas = 10
krystal_vest_amount = 0
krystal_token_decimal = 18

web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))


@app.route('/krystal_release', methods=['POST', 'GET'])
def krystal_release():
    global release_process_results
    if request.method == 'POST':
        print('Comes RELEASE POST')
        release_process_results.clear()
        data = request.json
        print(data)
        global web3
        web3 = krystal_services.set_up_chain(data['network'])
        global krystal_pool_id
        krystal_pool_ids = str(data['pool_id']).split(",")

        release_pools = []
        for pool_id in krystal_pool_ids:
            release_pools.append(pool_id.strip())

        global krystal_vest_amount
        krystal_vest_amount = float(data['vest_amount'])

        global krystal_token_decimal
        krystal_token_decimal = int(data['token_decimal'])

        global krystal_release_gas
        krystal_release_gas = str(data['gas'])
        print(krystal_release_gas)

        global krystal_release_time
        krystal_release_time = str(data['release_time'])
        print(krystal_release_time)

        global krystal_release_retry_number
        krystal_release_retry_number = str(data['retry_number'])
        print(krystal_release_retry_number)

        krystal_services.stop_schedular()

        for account in krystal_accounts_list:
            for pool_id in release_pools:
                account_data = {
                    'account_contract': account['address'],
                    'state': 'Processing',
                    'tx_id': '',
                    'retry': int(krystal_release_retry_number),
                    'number_of_release': 0,
                    'pool_id': pool_id,
                }
                release_process_results.append(account_data)
                krystal_services.perform_release(pool_id, krystal_vest_amount, krystal_token_decimal, account_data, krystal_release_gas, krystal_release_time, account['secret'], len(krystal_accounts_list))

    return jsonify({'result': release_process_results})


@app.route('/krystal', methods=['GET', 'POST'])
def krystal_load_page():
    if request.method == 'POST':
        data = request.form
        global krystal_selected_account_json
        krystal_selected_account_json = data.get('account')
        f = open('./accounts/' + krystal_selected_account_json, 'r')
        krystal_account_json = json.loads(f.read())
        global krystal_accounts_list
        krystal_accounts_list = krystal_account_json['accounts']
        for account in krystal_accounts_list:
            print(account['address'])
            print(account['sol_address'])
            print('====')
    return render_template('krystal.html',
                           network_list=constants.NETWORK_LIST,
                           json_account_list=krystal_json_account_list,
                           selected_json=krystal_selected_account_json,
                           accounts_list=krystal_accounts_list,
                           krystal_release_gas=krystal_release_gas,
                           krystal_release_retry_number=krystal_release_retry_number,
                           krystal_token_decimal=krystal_token_decimal,
                           )
