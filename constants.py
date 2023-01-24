NETWORK_LIST = ['BSC', 'POLYGON', 'AVAX']
BSC_NODE = "https://bsc-dataseed.binance.org/"
# BSC_NODE = "https://bsc-dataseed1.defibit.io/"
POLYGON_NODE = "https://polygon-rpc.com" #"https://rpc-mainnet.maticvigil.com/"
PANCAKE_ROUTE_ADDRESS = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
PANCAKE_ROUTE_ADDRESS_TESTNET = "0xD99D1c33F9fC3444f8101754aBC46c52416550D1"
QUICKSWAP_ROUTE_ADDRESS = "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff"
PANCAKE_FACTORY_ADDRESS = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
QUICKSWAP_FACTORY_ADDRESS = "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"

AVAX_NODE = "https://api.avax.network/ext/bc/C/rpc"
TRANDERJOE_ROUTE_ADDRESS = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
TRANDERJOE_FACTORY_ADDRESS = "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10"

KRYSTAL_MAIN_ADDRESS = "0xabc306ae80595f6c7748b81d6c2efc48b32a9e22"

UNLIMITED_AMOUNT = 2 ** 64 - 1
SELL_BSC_LIST = [
    {
        'contract': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
        'name': 'BNB'
    },
    {
        'contract': '0xe9e7cea3dedca5984780bafc599bd69add087d56',
        'name': 'BUSD'
    },
    {
        'contract': '0x55d398326f99059fF775485246999027B3197955',
        'name': 'USDT'
    }
]

SELL_POLYGON_LIST = [
    {
        'contract': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
        'name': 'MATIC'
    },
    {
        'contract': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f',
        'name': 'USDT'
    },
    {
        'contract': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174',
        'name': 'USDC'
    }
]

SELL_AVAX_LIST = [
    {
        'contract': '0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7',
        'name': 'AVAX'
    },
    {
        'contract': '0xc7198437980c041c805a1edcba50c1ce5db95118',
        'name': 'USDT'
    },
    {
        'contract': '0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664',
        'name': 'USDCe'
    },
    {
        'contract': '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e',
        'name': 'USDC'
    },
    {
        'contract': '0xd586e7f844cea2f87f50152665bcbc2c279d8d70',
        'name': 'DAI'
    },
]

STABLE_COIN_LIST = [
    '0xe9e7cea3dedca5984780bafc599bd69add087d56'.lower(),
    '0x55d398326f99059fF775485246999027B3197955'.lower(),
    '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'.lower(),
    '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'.lower(),
    '0xc7198437980c041c805a1edcba50c1ce5db95118'.lower(),
    '0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664'.lower(),
    '0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e'.lower(),
    '0xd586e7f844cea2f87f50152665bcbc2c279d8d70'.lower()
]