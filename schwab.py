# Schwab Auto Trader
# To use this app one must have an schwab developer account, see README.md for details.
# Author: Calvin Seamons
# Last Updated: 15 October, 2024

# Library Imports
import argparse
import asyncio
import base64
import json
import os
import pandas
import requests
import threading
import time
import webbrowser
import yaml 

# Library From Imports 
from getpass import getpass
from loguru import logger
from typing import Optional
from pathlib import Path

# Local File Imports
from encryption import set_encryption, retrieve_encrypted_data, encrypt_file_with_password, decrypt_file_with_password
from refresh import refresh_tokens
from trader import run_trade
#from refresh.py as refresh

from dotenv import load_dotenv


# Global Variables :(
VERSION = '0.0.1' # Script is very much unreleased and in development. 
TOKEN_TIME = -1 # Global time decay of auth_token for schwab, if this hits zero trading will halt.

class AccountsTrading:
    def __init__(self):
        # Initialize access token during class instantiation
        self.access_token = None
        self.account_hash_value = None
        self.refresh_access_token()
        self.base_url = "https://api.schwabapi.com/trader/v1"
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        self.get_account_number_hash_value()

    def get_account_number_hash_value(self):
        response = requests.get(
            self.base_url + f"/accounts/accountNumbers", headers=self.headers
        )
        response_frame = pandas.json_normalize(response.json())
        self.account_hash_value = response_frame["hashValue"].iloc[0]


def construct_init_auth_url(install_path) -> tuple[str, str, str]:
    file_path=install_path
    file_path = os.path.join(install_path, 'schwab-credentials.yaml')
    try:
        data = decrypt_file_with_password(file_path)
        app_key = data['app_key']
        app_secret = data['app_secret']
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

def params_parser(params):
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

def sanity_check(install_path):
    token_path = os.path.join(install_path, "tokens.yaml")
    token_data = decrypt_file_with_password(token_path)
    access_token = token_data['access_token']


    hash= requests.get(f'https://api.schwabapi.com/trader/v1/accounts/accountNumbers',
                            headers={'Authorization': f'Bearer {access_token}'},
                            timeout=5)
    hash = hash.json()
    print(hash)
    



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

    token = os.getenv('secret_access_token')
    

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
    
    json_info = data.json()
    print(json_info)

def main(args):
    # Main's function is to address all flags thrown in the argparser, once finished launch the acutal trade commands listed in the trade.py 

    # Address path definition and install. 
    # Getting this all organized is fucking stupid. 
    # ------------------------------------------- #
    # 0.5 Check and see if encryption key is set, if not have them make a new one or use the one they set.
    # 1) Check if the .schwab_auto_trader/ dir exists
    # 2) If not (-s) check if the token_file is still valid, then run trade code, if not prompt for startup.
    # 3) is (-s) check credentials, if empty fill in, then run code for token, then commence trade code.
    # ------------------------------------------- #  

    password = getpass("Enter encryption password to secure schwab-credentials and schwab-tokens.\n"
                       "If you have already entered this, please submit the password you set. ")
    os.environ['super_secret_sauce'] = password
    install_path = Path(args.path)
    sanity_check(install_path)

    if args.refresh_token == True:
        token_path = os.path.join(install_path, "tokens.yaml")
        cred_path = os.path.join(install_path, "schwab-credentials.yaml")

        token_data = decrypt_file_with_password(token_path)
        cred_data = decrypt_file_with_password(cred_path)

        os.environ['secret_refresh_token'] = token_data['refresh_token']
        os.environ['secret_app_id']        = cred_data['app_key']
        os.environ['secret_app_secret']    = cred_data['app_secret']

        thing= os.getenv('secret_refresh_token')
        print(thing)
        data=refresh_tokens()
        with open(token_path, 'w') as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=False)
        encrypt_file_with_password(token_path)



    if args.get_cred == True:
        if install_path.exists(): # Check that ".schwab_auto_trade" exists in ~
            token_path = os.path.join(install_path, "tokens.yaml")
            if os.path.isfile(token_path):
                data = decrypt_file_with_password(token_path)
                os.environ['secret_access_token'] = data['access_token']
                os.environ['secret_refresh_token'] = data['refresh_token']
                print(data)

    if args.startup == False:
        if install_path.exists(): # Check that ".schwab_auto_trade" exists in ~
            token_path = os.path.join(install_path, "tokens.yaml")
            if os.path.isfile(token_path): # Check if tokens.yaml is there and how old it is, if > 1800 it's expired. 
                exp = os.path.getmtime(token_path)
                current_time = time.time()
                token_age = current_time - exp # Age of tokens is current time minus the last modified time of tokens.yaml. 
                if token_age > 1700:
                    print("Uh oh, looks like your token is expired you fucking RETARD!")
                    print("Try running --startup or -s, you'll be prompted to sign into schwab again.")
                    exit()
                else:
                    print("Ready to execute trade scripts!")
                    #run_trade()
                    #get_data_test()
                    #execute_trade() # Doesn't exist yet. 
                    exit()
            else:
                print("Tokens.yaml is missing, run python3 schwab.py (-s or --startup)")
                exit()
                

            pass # We have the path that's all we care about.
        else: 
            os.makedirs(install_path, exist_ok=True) 
            schwab_file = Path.joinpath(install_path, 'schwab-credentials.yaml') # If schwab app info missing we gotta ask for it and save the file.
            if os.path.getsize(schwab_file) == 0: # schwab-credentials appears empty 
                print("We've detected an Empty Schwab Credential file! This will be saved in an encryped file at "+str(schwab_file))
                app_key = input("Please provide your APP_KEY (found on developer.schwab.com): ")
                app_secret = input("Please provide your APP_SECRET (found on developer.schwab.com): ")
                data = {'app_key': app_key, 'app_secret': app_secret}
                with open(schwab_file, 'w') as yaml_file:
                    yaml.dump(data, yaml_file, default_flow_style=False)
                encrypt_file_with_password(schwab_file)


    if args.startup == True: # If startup we kicked schwab authentication. 
        app_key, app_secret, cs_auth_url = construct_init_auth_url(install_path)
        webbrowser.open(cs_auth_url)

        logger.info("Paste Returned URL:")
        returned_url = input()

        init_token_headers, init_token_payload = construct_headers_and_payload(returned_url, app_key, app_secret)
        init_tokens_dict = retrieve_tokens(headers=init_token_headers, payload=init_token_payload)
        #logger.debug(init_tokens_dict)
        
        tokens_file = Path.joinpath(install_path, 'tokens.yaml')
        if os.path.exists(install_path) and os.path.isfile(tokens_file): #We are resetting tokens so delete if present. 
            os.remove(tokens_file)

        with open(tokens_file, 'w') as yaml_file:
            yaml.dump(init_tokens_dict, yaml_file, default_flow_style=False)

        encrypt_file_with_password(tokens_file)
    
    if args.encryption == True: # Encrypt all schwab files.
        set_encryption(install_path)
    #retrieve_encrypted_data(install_path)
        

if __name__ == "__main__":
    # Arguemnts that you can pass in with "python3 schwab.py --startup etc etc", self explanitory.
    parser = argparse.ArgumentParser(description="Args for schwab-auto-trader")
    parser.add_argument("--encryption", "-e", action='store_true', default=False, help="Create keyfile for app secret/id storage. Only need to run once.")
    parser.add_argument("--startup","-s", action='store_true', default=False, help="Kickoff flag to authenticate with schwab, run when first launching script.")
    parser.add_argument("--get-token-time","-gtt", action='store_true', default=False, help="Returns remaining authentication time with schwab token.")
    parser.add_argument("--refresh-token","-rt", action='store_true', default=False, help="Manually reset Authentication Token expiration timer.")
    parser.add_argument("--auto-refresh-token", type=bool, default=True, help="Set to false will result in one 30min authentication session.")
    parser.add_argument("--path", type=str, default=os.path.expanduser('~/.schwab_auto_trader'), help="Default directory where files will be installed.")
    parser.add_argument("--get-cred", action='store_true', default=False, help="Display token credentials if present.")
    args = parser.parse_args()

    main(args)
