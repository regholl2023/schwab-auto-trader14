# tokens.py 
# Schwab Token file contains authentication info for schwab api.
# Author: Calvin Seamons
# Last Updated: 24 October, 2024

# Imports
# ------------------ #
import base64
import logging
import os
import requests
import sys
import time
import webbrowser
import yaml

# From Imports
# ------------------ #
from pathlib import Path

# Local File Imports
# ------------------ #
from encryption import decrypt_file_with_password

logging.basicConfig(
    level=logging.ERROR,
    format="\033[91m[ Error ] %(message)s\033[0m"
)

def global_error(message):
    logging.error(message)
    sys.exit(1)


class Tokens:
    

    def __init__(self, args):
        self.base_url =  "https://api.schwabapi.com/trader/v1"
        self.base_install = args.install_path
        self.tokenfile = os.path.join(self.base_install, 'tokens.yaml')
        self.credfile = os.path.join(self.base_install, 'schwab-credentials.yaml')


        time_experation = self.check_time()
        if time_experation == True or args.startup == True:
            cred = self.get_app_creds()
            self.app_key = cred['app_key']
            self.app_secret = cred['app_secret']
            self.build_cred()

        token_cred = self.get_token_creds()
        self.refresh_token = token_cred['refresh_token']
        self.access_token = token_cred['access_token']
        print(self.access_token)


    def get_app_creds(self):
        if os.path.isfile(self.credfile):
            schwab_cred = decrypt_file_with_password(self.credfile)
            if 'app_key' in schwab_cred and schwab_cred['app_key'] is not None and \
                schwab_cred['app_key'] != "" and 'app_secret' in schwab_cred and \
                schwab_cred['app_secret'] is not None and schwab_cred['app_secret'] != "":
                return schwab_cred
            else:
                global_error("Missing app_key or app_secret in schwab_credentials.yaml. run --startup.")
        else:
            global_error("schwab-credentials.yaml doesn't exist in ~/.schwab_auto_trader. run --startup.")

    def get_token_creds(self):
        if os.path.isfile(self.tokenfile):
            return decrypt_file_with_password(self.tokenfile)
        else:
            global_error("tokens.yaml doesn't exist in ~/.schwab_auto_trader. run --startup.")

    def check_time(self): # Checks the experation time of the tokenfile. 
        exp = os.path.getmtime(self.tokenfile)
        current_time = time.time()
        token_age = current_time-exp
        if token_age > 604800: # Your token is most likely expired, refresh needed.
            return True
        elif token_age > 475200: # If token file hasn't been updated in 5days12hr it is expiring soon.
            logging.warning("Your refresh may expire soon. Please run --startup")
            return False
        else:
            # Everything is fine.
            return False

    def construct_init_auth_url(self) -> tuple[str, str, str]:
        try:
            data       = decrypt_file_with_password(self.credfile)
            app_key    = data['app_key']
            app_secret = data['app_secret']
        except Exception as e:
            global_error(e)
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri=https://127.0.0.1"

        logging.info("Click to authenticate:")
        logging.info(auth_url)

        return app_key, app_secret, auth_url

    def construct_headers_and_payload(self,returned_url, app_key, app_secret):
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
    
    def retrieve_tokens(self,headers, payload) -> dict:
        init_token_response = requests.post(
            url="https://api.schwabapi.com/v1/oauth/token",
            headers=headers,
            data=payload,
        )

        init_tokens_dict = init_token_response.json()

        return init_tokens_dict

    def build_cred(self):
        app_key, app_secret, cs_auth_url = self.construct_init_auth_url()
        webbrowser.open(cs_auth_url)
        logging.info("Paste Returned URL:")
        returned_url = input()
        init_token_headers, init_token_payload = self.construct_headers_and_payload(returned_url, app_key, app_secret)
        init_tokens_dict = self.retrieve_tokens(headers=init_token_headers, payload=init_token_payload)
        if os.path.isfile(self.tokensfile): #We are resetting tokens so delete if present. 
            os.remove(self.tokensfile)
        with open(self.tokensfile, 'w') as yaml_file:
            yaml.dump(init_tokens_dict, yaml_file, default_flow_style=False)

