# Trader.py is where the simplified trade class is. 
# Imports
import datetime
import os
import requests
import urllib.parse
import json

from tokens import Tokens
from log_obj import Log

class Trader:

    def __init__(self, args):
        self.tokens = Tokens(args)
        self.log = Log()
        self.timeout = 5

    def _params_parser(self, params: dict):
        for key in list(params.keys()):
            if params[key] is None: del params[key]
        return params

    def get_account_balance(self, fields: str = None):
        data = requests.get(f'{self.tokens.base_url}/trader/v1/accounts/',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params={'fields': fields},
                            timeout=self.timeout)
        data = data.json()
        print(data)
    

    def quote(self, symbol_id: str, fields: str = None) -> requests.Response:
        
        data =  requests.get(f'{self.tokens.base_url}/marketdata/v1/{urllib.parse.quote(symbol_id,safe="")}/quotes',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)
        print(data)

        
    def test(self):
        ticker = 'APPL'
        url = f"https://api.schwab.com/marketdata/v1/{urllib.parse.quote({ticker},safe="")}/quotes"
        headers = {
            "Authorization": f"Bearer {self.tokens.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        market_price = data.get("marketPrice")
        print("APPLE PRICE IS: " + str(market_price))

    def test2(self):
        data = requests.get(f'{self.tokens.base_url}/marketdata/v1/pricehistory',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=({'symbol': 'AAPL'}))
        
        data = data.json()
        print(data)

        