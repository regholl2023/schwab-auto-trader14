# Schwab Auto Trader
# To use this app one must have an schwab developer account. 

# Imports
import os
import base64
import requests
import webbrowserp
from loguru import logger
import pandas
from typing import Optional
import asyncio
import json


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
    
    #app_key = "your-app-key"
    app_key = ''
    #app_secret = "your-app-secret"
    app_secret =  ''

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

def refresh_tokens():
    logger.info("Initializing...")

    app_key = "your-app-key"
    app_secret = "your-app-secret"

    # You can pull this from a local file,
    # Google Cloud Firestore/Secret Manager, etc.
    refresh_token_value = "your-current-refresh-token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
    }
    headers = {
        "Authorization": f'Basic {base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()}',
        "Content-Type": "application/x-www-form-urlencoded",
    }

    refresh_token_response = requests.post(
        url="https://api.schwabapi.com/v1/oauth/token",
        headers=headers,
        data=payload,
    )
    if refresh_token_response.status_code == 200:
        logger.info("Retrieved new tokens successfully using refresh token.")
    else:
        logger.error(
            f"Error refreshing access token: {refresh_token_response.text}"
        )
        return None

    refresh_token_dict = refresh_token_response.json()

    logger.debug(refresh_token_dict)

    logger.info("Token dict refreshed.")

    return "Done!"

def main():
    app_key, app_secret, cs_auth_url = construct_init_auth_url()
    webbrowser.open(cs_auth_url)

    logger.info("Paste Returned URL:")
    returned_url = input()

    init_token_headers, init_token_payload = construct_headers_and_payload(
        returned_url, app_key, app_secret
    )

    init_tokens_dict = retrieve_tokens(
        headers=init_token_headers, payload=init_token_payload
    )

    logger.debug(init_tokens_dict)

    return "Done!"

def get_data():

    access_token=''

    url = 'https://api.schwab.com/v1/quotes?symbol=QQQ'

    # Headers for authorization
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Make the request to Schwab API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        last_price = data.get('lastPrice', 'N/A')  # Replace 'lastPrice' with the correct field if needed
        print(f'The current price of QQQ is: ${last_price}')
    else:
        print(f'Error fetching data: {response.status_code}')


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



if __name__ == "__main__":
    get_data()
    main()
