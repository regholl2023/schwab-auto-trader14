# Schwab Auto Trader
# To use this app one must have an schwab developer account, see README.md for details.
# Author: Calvin Seamons
# Last Updated: 8 October, 2024

# Library Imports
import argparse
import asyncio
import base64
import json
import os
import pandas
import requests
import webbrowser
import yaml 

# Library From Imports 
from loguru import logger
from typing import Optional
from pathlib import Path

# File Imports
from encryption import set_encryption, retrieve_encrypted_data
#from refresh.py as refresh

VERSION = '0.0.1' # Script is very much unreleased and in development. 

class AccountsTrading:
    def __init__(self):
        # Initialize access token during class instantiation
        self.access_token = None
        self.account_hash_value = None
        self.refresh_access_token()
        self.base_url = "https://api.schwabapi.com/trader/v1"
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        self.get_account_number_hash_value()

    def refresh_access_token(self):
        # Custom function to retrieve access token from Firestore
        self.access_token = retrieve_firestore_value(
            collection_id="your-collection-id",
            document_id="your-doc-id",
            key="your-access-token",
        )

    def get_account_number_hash_value(self):
        response = requests.get(
            self.base_url + f"/accounts/accountNumbers", headers=self.headers
        )
        response_frame = pandas.json_normalize(response.json())
        self.account_hash_value = response_frame["hashValue"].iloc[0]


def construct_init_auth_url() -> tuple[str, str, str]:
    file_path='/Users/cal/desktop/stinky-schwab.yaml'
    try:
        app_key, app_secret = read_yaml(file_path)
    except Exception as e:
        print(f"Error: {e}")
    
    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri=https://127.0.0.1"

    logger.info("Click to authenticate:")
    logger.info(auth_url)

    return app_key, app_secret, auth_url

def construct_headers_and_payload(returned_url, app_key, app_secret):
    response_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

    credentials = f"{app_key}:{app_secret}"
    base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
        "utf-8"
    )

    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "grant_type": "authorization_code",
        "code": response_code,
        "redirect_uri": "https://127.0.0.1",
    }

    return headers, payload

def retrieve_tokens(headers, payload) -> dict:
    init_token_response = requests.post(
        url="https://api.schwabapi.com/v1/oauth/token",
        headers=headers,
        data=payload,
    )

    init_tokens_dict = init_token_response.json()

    return init_tokens_dict

def read_yaml(file_path):
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    
    # Open and load the YAML file
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    # Check if two specific variables exist in the file
    if 'app_key' not in data or 'app_secret' not in data:
        raise KeyError("Required variables 'variable1' and 'variable2' are missing from the file.")
    
    # Retrieve the variables
    app_key = data['app_key']
    app_secret = data['app_secret']

    return app_key, app_secret

def design_order(
    symbol,
    order_type,
    instruction,
    quantity,
    leg_id,
    order_leg_type,
    asset_type,
    price: Optional[str] = None,
    session="NORMAL",
    duration="DAY",
    complex_order_strategy_type="NONE",
    tax_lot_method="FIFO",
    position_effect="OPENING",
    # special_instruction="ALL_OR_NONE",
    order_strategy_type="SINGLE",
):

    post_order_payload = {
        "price": price,
        "session": session,
        "duration": duration,
        "orderType": order_type,
        "complexOrderStrategyType": complex_order_strategy_type,
        "quantity": quantity,
        "taxLotMethod": tax_lot_method,
        "orderLegCollection": [
            {
                "orderLegType": order_leg_type,
                "legId": leg_id,
                "instrument": {
                    "symbol": symbol,
                    "assetType": asset_type,
                },
                "instruction": instruction,
                "positionEffect": position_effect,
                "quantity": quantity,
            }
        ],
        "orderStrategyType": order_strategy_type,
    }

    return post_order_payload

def stream_data():
    client = client_from_token_file(
        token_path='/path/to/token.json',
        api_key='YOUR_API_KEY',
        app_secret='YOUR_APP_SECRET')
    stream_client = StreamClient(client, account_id=1234567890)

    async def read_stream():
        await stream_client.login()

        def print_message(message):
            print(json.dumps(message, indent=4))

        # Always add handlers before subscribing because many streams start sending
        # data immediately after success, and messages with no handlers are dropped.
        stream_client.add_nasdaq_book_handler(print_message)
        await stream_client.nasdaq_book_subs(['GOOG'])

        while True:
            await stream_client.handle_message()

    asyncio.run(read_stream())

def _params_parser(params):
        """
        Removes None (null) values
        :param params: params to remove None values from
        :type params: dict
        :return: params without None values
        :rtype: dict
        """
        for key in list(params.keys()):
            if params[key] is None: del params[key]
        return params


def time_convert(self, dt=None, form="8601"):
        """
        Convert time to the correct format, passthrough if a string, preserve None if None for params parser
        :param dt: datetime.pyi object to convert
        :type dt: datetime.pyi
        :param form: what to convert input to
        :type form: str
        :return: converted time or passthrough
        :rtype: str | None
        """
        if dt is None or isinstance(dt, str):
            return dt
        elif form == "8601":  # assume datetime object from here on
            return f'{dt.isoformat()[:-9]}Z'
        elif form == "epoch":
            return int(dt.timestamp())
        elif form == "epoch_ms":
            return int(dt.timestamp() * 1000)
        elif form == "YYYY-MM-DD":
            return dt.strftime("%Y-%m-%d")
        else:
            return dt


def get_data_test():
    _base_api_url = "https://api.schwabapi.com"
    symbol = "AAPL"
    periodType = "year"
    frequencyType = 'daily'
    period = "10"
    periodType = 'period'
    frequency = 10
    startDate = "09|20|24"
    endDate = "09|23|24"
    needExtendedHoursData = False
    needPreviousClose = False

    periodType = None
    frequencyType = None
    period = None
    periodType = None
    frequency = None
    startDate = None
    endDate = None
    needExtendedHoursData = None
    needPreviousClose = None

    token = ''

    #resp = requests.get('https://api.schwabapi.com/marketdata/v1/pricehistory?symbol=AAPL&periodType=year&period=1&frequencyType=daily&frequency=1&startDate=1722367119&endDate=1723490319&needExtendedHoursData=false&needPreviousClose=false',


    data = requests.get(f'{_base_api_url}/marketdata/v1/pricehistory',
                            headers={'Authorization': f'Bearer {token}'},
                            params=({'symbol': 'AAPL'}))
                            #params=_params_parser({'symbol': symbol, 'periodType': periodType, 'period': period,
                            #                            'frequencyType': frequencyType, 'frequency': frequency,
                            #                            'startDate': time_convert(startDate, 'epoch_ms'),
                            #                            'endDate': time_convert(endDate, 'epoch_ms'),
                            #                            'needExtendedHoursData': needExtendedHoursData,
                            #                            'needPreviousClose': needPreviousClose}),timeout=5)
    
    print(data)

def main(args):
    # Main's function is to address all flags thrown in the argparser, once finished launch the acutal trade commands listed in the trade.py 

    # Address path definition and install. 
    install_path = Path(args.path)
    if install_path.exists():
        pass # We have the path that's all we care about.
    else: 
        os.makedirs(install_path, exist_ok=True) 
        schwab_file = Path.joinpath(install_path, 'schwab-credentials.yaml')
        print("We've detected an Empty Schwab Credential file! This will be saved in an encryped file at "+str(schwab_file))
        app_key = input("Please provide your APP_KEY (found on developer.schwab.com): ")
        app_secret = input("Please provide your APP_SECRET (found on developer.schwab.com): ")
        data = {'app_key': app_key, 'app_secret': app_secret}

        with open(schwab_file, 'w') as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=False)

        


    if args.startup == True: # If startup we kicked schwab authentication. 
        app_key, app_secret, cs_auth_url = construct_init_auth_url()
        webbrowser.open(cs_auth_url)

        logger.info("Paste Returned URL:")
        returned_url = input()

        init_token_headers, init_token_payload = construct_headers_and_payload(returned_url, app_key, app_secret)
        init_tokens_dict = retrieve_tokens(headers=init_token_headers, payload=init_token_payload)
        #logger.debug(init_tokens_dict)

        tokens_file = Path.joinpath(install_path, 'tokens.yaml')
        with open(tokens_file, 'w') as yaml_file:
            yaml.dump(init_tokens_dict, yaml_file, default_flow_style=False)
    
    
    #if args.encryption == True: # Encrypt all schwab files.
    #    set_encryption(install_path)
    retrieve_encrypted_data(install_path)
        

if __name__ == "__main__":
    # Arguemnts that you can pass in with "python3 schwab.py --startup etc etc", self explanitory.
    parser = argparse.ArgumentParser(description="Args for schwab-auto-trader")
    parser.add_argument("--encryption", "-e", action='store_true', default=True, help="Create keyfile for app secret/id storage. Only need to run once.")
    parser.add_argument("--startup","-s", action='store_true', default=False, help="Kickoff flag to authenticate with schwab, run when first launching script.")
    parser.add_argument("--get-token-time","-gtt", action='store_true', default=False, help="Returns remaining authentication time with schwab token.")
    parser.add_argument("--refresh-token","-rt", action='store_true', default=False, help="Manually reset Authentication Token expiration timer.")
    parser.add_argument("--auto-refresh-token", type=bool, default=True, help="Set to false will result in one 30min authentication session.")
    parser.add_argument("--path", type=str, default=os.path.expanduser('~/.schwab_auto_trader'), help="Default directory where files will be installed.")
    args = parser.parse_args()

    main(args)
