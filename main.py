import json
import os
from flask import render_template, request, jsonify
import constants
from api import services
from web3 import Web3
import gc

from app_flask import app

gc.set_threshold(0)

json_account_list = []
for file in os.listdir('./accounts'):
    if file.endswith('.json'):
        json_account_list.append(file)
    json_account_list.sort()

selected_network = 'bsc'
selected_account_json = json_account_list[0]
accounts_list = []
currency_list = constants.SELL_BSC_LIST
approve_process_results = []
transfer_process_results = []
sell_process_results = []
web3 = Web3(Web3.HTTPProvider(constants.BSC_NODE))
prefill_approve_gas = "5"
prefill_sell_gas = "10"
prefill_transfer_gas = "5"

from enjin import enjin
from starter import starter
from krystal import krystal


@app.route('/', methods=['POST'])
def load_account():
    print("POST here")
    data = request.form

    global selected_network
    selected_network = data.get('network')
    global web3
    web3 = services.set_up_chain(selected_network)
    global prefill_approve_gas
    global prefill_sell_gas
    global prefill_transfer_gas
    if selected_network == 'POLYGON':
        prefill_approve_gas = "30"
        prefill_sell_gas = "50"
        prefill_transfer_gas = "30"
    elif selected_network == 'AVAX':
        prefill_approve_gas = "25"
        prefill_sell_gas = "50"
        prefill_transfer_gas = "25"
    else:
        prefill_approve_gas = "5"
        prefill_sell_gas = "10"
        prefill_transfer_gas = "5"
    global selected_account_json
    selected_account_json = data.get('account')
    global currency_list
    currency_list = constants.SELL_BSC_LIST
    if selected_network == 'POLYGON':
        currency_list = constants.SELL_POLYGON_LIST
    elif selected_network == 'AVAX':
        currency_list = constants.SELL_AVAX_LIST
    new_currenc_list = currency_list.copy()
    new_currenc_list.insert(0, {
        'contract': 'AUTO',
        'name': 'AUTO'
    })
    f = open('./accounts/' + selected_account_json, 'r')
    account_json = json.loads(f.read())
    global accounts_list
    accounts_list = account_json['accounts']
    for account in accounts_list:
        print(account['address'])
        print(account['secret'])
        print(account['api_key_bsc'])
        print(account['api_key_polygon'])
        print('====')

    return render_template('main.html',
                           network_list=constants.NETWORK_LIST,
                           json_account_list=json_account_list,
                           selected_network=selected_network,
                           selected_json=selected_account_json,
                           accounts_list=accounts_list,
                           currency_list=new_currenc_list,
                           prefill_approve_gas=prefill_approve_gas,
                           prefill_sell_gas=prefill_sell_gas,
                           prefill_transfer_gas=prefill_transfer_gas)


@app.route('/', methods=['GET'])
def hello_world():
    print(json_account_list)
    return render_template('main.html',
                           network_list=constants.NETWORK_LIST,
                           json_account_list=json_account_list,
                           selected_network=selected_network,
                           selected_json=selected_account_json,
                           accounts_list=accounts_list,
                           currency_list=currency_list)


count = 0
approve_contract = ''
approve_gas = ''
des_token = ''


def is_finished_approving():
    for account in approve_process_results:
        if account['state'] == 'Processing':
            return False
    return True


@app.route('/approve', methods=['POST', 'GET'])
def approve():
    global approve_process_results
    global count
    if request.method == 'GET':
        approve_result = is_finished_approving
        while not approve_result:
            approve_result = is_finished_approving
    elif request.method == 'POST':
        print('Comes Approve POST')
        approve_process_results.clear()
        data = request.json
        print(data)
        global approve_contract
        approve_contract = str(data['contract'])
        global approve_gas
        approve_gas = str(data['gas'])
        # print(accounts_list)
        print(approve_contract)
        print(approve_gas)
        token = web3.toChecksumAddress(approve_contract)
        for account in accounts_list:
            account_data = {
                'account_contract': account['address'],
                'state': 'Processing',
                'tx_id': ''
            }
            approve_process_results.append(account_data)
            services.perform_approve(token, account_data, approve_gas, account['secret'])

    return jsonify({'result': approve_process_results})


@app.route('/sell', methods=['POST', 'GET'])
def sell():
    global sell_process_results
    if request.method == 'POST':
        print('Comes SELL POST')
        sell_process_results.clear()
        data = request.json
        print(data)
        global approve_contract
        approve_contract = str(data['contract'])
        global approve_gas
        approve_gas = str(data['gas'])
        token = web3.toChecksumAddress(approve_contract)
        global des_token
        des_token = str(data['sell_currency'])
        print(des_token)

        sell_time = str(data['sell_time'])
        services.stop_schedular()
        for account in accounts_list:
            account_data = {
                'account_contract': account['address'],
                'state': 'Processing',
                'tx_id': ''
            }
            sell_process_results.append(account_data)
            is_auto_currency = data['sell_currency'] == 'AUTO'
            services.perform_sell(token, des_token, sell_time, account_data, approve_gas, account['secret'], len(accounts_list), auto_find=is_auto_currency, check_good_pair=True)

    return jsonify({'result': sell_process_results})


@app.route('/retry', methods=['POST'])
def retry():
    global sell_process_results
    if request.method == 'POST':
        print('Comes Retry')
        data = request.json
        print(data)
        global approve_contract
        approve_contract = str(data['contract'])
        global approve_gas
        approve_gas = str(data['gas'])
        token = web3.toChecksumAddress(approve_contract)
        global des_token
        des_token = str(data['sell_currency'])
        print(des_token)
        account_retry = data['address_contract']
        print('account_retry')
        print(account_retry)
        is_auto_currency = data['sell_currency'] == 'AUTO'
        for account in sell_process_results:
            print('Finding')
            if account_retry == account['account_contract']:
                print("Matched")
                secret = ''
                for acc in accounts_list:
                    if acc['address'] == account_retry:
                        secret = acc['secret']
                account.update({'state': 'Processing', 'tx_id': ''})
                services.perform_sell(token, des_token, "", account, approve_gas, secret, len(sell_process_results), is_auto_currency)
                break
    return jsonify({'result': sell_process_results})


transfer_contract = ''
transfer_gas = ''
to_address = ''
transfer_time = ''


@app.route('/transfer', methods=['POST', 'GET'])
def transfer():
    global transfer_process_results
    if request.method == 'POST':
        print('vComes Transfer POST')
        transfer_process_results.clear()
        data = request.json
        print(data)
        global transfer_contract
        transfer_contract = str(data['contract'])
        global transfer_gas
        transfer_gas = str(data['gas'])
        global to_address
        to_address = str(data['to_address'])
        global transfer_time
        transfer_time = str(data['transfer_time'])
        # print(accounts_list)
        print(transfer_contract)
        print(transfer_gas)
        print(to_address)
        token = web3.toChecksumAddress(transfer_contract)
        services.stop_schedular()
        for account in accounts_list:
            account_data = {
                'account_contract': account['address'],
                'state': 'Processing',
                'tx_id': ''
            }
            transfer_process_results.append(account_data)
            services.perform_transfer(token, to_address, transfer_time, account_data, transfer_gas, account['secret'], len(accounts_list))

    return jsonify({'result': transfer_process_results})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4500, debug=False)
