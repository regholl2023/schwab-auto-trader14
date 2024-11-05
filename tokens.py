# tokens.py 
# Schwab Token file contains authentication info for schwab api.
# Author: Calvin Seamons
# Last Updated: 05 November, 2024

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
from log_obj import Log
from pathlib import Path

# Local File Imports
# ------------------ #
from encryption import decrypt_file_with_password, encrypt_file_with_password

class Tokens:
    
    def __init__(self, args):
        self.base_url =  "https://api.schwabapi.com"
        self.base_install = args.install_path
        self.tokenfile = os.path.join(self.base_install, 'tokens.yaml')
        self.credfile = os.path.join(self.base_install, 'schwab-credentials.yaml')
        self.timefile = os.path.join(self.base_install, 'timer.yaml')
        self.log = Log()

        time_experation = self.check_time()
        if time_experation == True or args.startup == True:
            cred = self.get_app_creds()
            self.app_key = cred['app_key']
            self.app_secret = cred['app_secret']
            self.build_cred()

        if args.refresh_token == True:
            self._refresh_token()
            
        token_cred = self.get_token_creds()
        self.refresh_token = token_cred['refresh_token']
        self.access_token = token_cred['access_token']
        self.account_hash = self.get_account_hash()


    def get_account_hash(self):
        try:
            hash = requests.get(f'https://api.schwabapi.com/trader/v1/accounts/accountNumbers',
                           headers={'Authorization': f'Bearer {self.access_token}'},
                            timeout=5)
            hash = hash.json()
            return hash
        except Exception as e:
            self.log.error("Unable to get AccountHash. Account Trades cannot be conducted.",True)


    def get_app_creds(self):
        if os.path.isfile(self.credfile):
            schwab_cred = decrypt_file_with_password(self.credfile)
            if 'app_key' in schwab_cred and schwab_cred['app_key'] is not None and \
                schwab_cred['app_key'] != "" and 'app_secret' in schwab_cred and \
                schwab_cred['app_secret'] is not None and schwab_cred['app_secret'] != "":
                return schwab_cred
            else:
                self.log.error("Missing app_key or app_secret in schwab_credentials.yaml. run --startup.")
        else:
            self.log.error("schwab-credentials.yaml doesn't exist in ~/.schwab_auto_trader. run --startup.")

    def get_token_creds(self):
        if os.path.isfile(self.tokenfile):
            return decrypt_file_with_password(self.tokenfile)
        else:
            self.log.error("tokens.yaml doesn't exist in ~/.schwab_auto_trader. run --startup.")

    def check_time(self): # Checks the experation time of the tokenfile. 
        try:
            with open(self.timefile, 'rb') as timefile:
                data = yaml.safe_load(timefile)
            old_time = data['refresh_token_time']     
        except Exception as e:
            self.log.error(e + " Something went wrong, check the timer.yaml file")

        current_time = time.time()
        token_age = current_time-old_time
        if token_age > 604800: # Your token is most likely expired, refresh needed.
            return True
        elif token_age > 475200: # If token file hasn't been updated in 5days12hr it is expiring soon.
            self.log.warning("Your refresh token may expire soon. Please run --startup")
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
            self.log.error(e)
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri=https://127.0.0.1"

        self.log.info("Click to authenticate:")
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
        self.log.info("Paste Returned URL:")
        returned_url = input("\nPaste Returned URL:")
        init_token_headers, init_token_payload = self.construct_headers_and_payload(returned_url, app_key, app_secret)
        init_tokens_dict = self.retrieve_tokens(headers=init_token_headers, payload=init_token_payload)
        self.log.success("Authentication with Schwab successful.")

        # Setting timer file so track refresh token expiration 
        refresh_token_time = time.time() # Both access and refresh are reset here so i reuse the var.
        refresh_data = {'refresh_token_time': refresh_token_time, 'access_token_time': refresh_token_time}
        with open(self.timefile, 'w') as yaml_file:
            yaml.dump(refresh_data, yaml_file, default_flow_style=False)


        if os.path.isfile(self.tokenfile): #We are resetting tokens so delete if present. 
            os.remove(self.tokenfile)
        with open(self.tokenfile, 'w') as yaml_file:
            yaml.dump(init_tokens_dict, yaml_file, default_flow_style=False)
        encrypt_file_with_password(self.tokenfile)

    def _refresh_token(self):
        app_cred = self.get_app_creds() # Retrieve 
        app_key = app_cred['app_key']
        app_secret = app_cred['app_secret']
        token_cred = self.get_token_creds()
        refresh_cred = token_cred['refresh_token']

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_cred,
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
            self.log.success("Retrieved new tokens successfully using refresh token.")
        else:
            self.log.error(
                f"Error refreshing access token: {refresh_token_response.text}"
            )
            return None

        refresh_token_dict = refresh_token_response.json()

        access_token_time = time.time()
        refresh_data = {'access_token_time': access_token_time}

        with open(self.timefile, 'w') as yaml_file:
            yaml.dump(refresh_data, yaml_file, default_flow_style=False)

        if os.path.isfile(self.tokenfile): #We are resetting tokens so delete if present. 
            os.remove(self.tokenfile)

        with open(self.tokenfile, 'w') as yaml_file:
            yaml.dump(refresh_token_dict, yaml_file, default_flow_style=False)
        encrypt_file_with_password(self.tokenfile)

        os.environ['secret_access_token'] = refresh_token_dict['access_token']
        self.log.info("Token dict refreshed.")

        return refresh_token_dict

