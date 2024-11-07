# Main method that takes in any commandline args and creates any missing config files.
from tokens import Tokens
from trader import Trader
import argparse
import os
from getpass import getpass
import yaml 

from log_obj import Log
from encryption import encrypt_file_with_password

if __name__ == "__main__":
    # Arguemnts that you can pass in with "python3 schwab.py --startup etc etc", self explanitory.
    parser = argparse.ArgumentParser(description="Args for schwab-auto-trader")
    parser.add_argument("--encryption", "-e", action='store_true', default=False, help="Create keyfile for app secret/id storage. Only need to run once.")
    parser.add_argument("--startup","-s", action='store_true', default=False, help="Kickoff flag to authenticate with schwab, run when first launching script.")
    parser.add_argument("--get-token-time","-gtt", action='store_true', default=False, help="Returns remaining authentication time with schwab token.")
    parser.add_argument("--refresh-token","-rt", action='store_true', default=False, help="Manually reset Authentication Token expiration timer.")
    parser.add_argument("--auto-refresh-token", type=bool, default=True, help="Set to false will result in one 30min authentication session.")
    parser.add_argument("--install_path", type=str, default=os.path.expanduser('~/.schwab_auto_trader'), help="Default directory where files will be installed.")
    parser.add_argument("--get-cred", action='store_true', default=False, help="Display token credentials if present.")
    args = parser.parse_args()

password = getpass("Enter encryption password to secure schwab-credentials and schwab-tokens.\n"
                   "If you have already entered this, please submit the password you set. ")
os.environ['super_secret_sauce'] = password
password = None

tokens_file = os.path.join(args.install_path, 'tokens.yaml')
timer_file = os.path.join(args.install_path, 'timer.yaml')
credentials_file = os.path.join(args.install_path, 'schwab-credentials.yaml')

if os.path.isfile(tokens_file) == False: 
      with open(tokens_file, "w") as file:
          pass

if os.path.isfile(timer_file) == False or os.path.getsize(timer_file) == 0:
      with open(timer_file, "w") as file:
          filler = {'refresh_token_time': 0, 'access_token_time': 0}
          yaml.dump(filler, file, default_flow_style=False)

if os.path.isfile(credentials_file) == False: 
    if os.path.getsize(credentials_file) == 0: # schwab-credentials appears empty 
                print("We've detected an Empty Schwab Credential file! This will be saved in an encryped file at "+str(credentials_file))
                app_key = input("Please provide your APP_KEY [found on developer.schwab.com]: ")
                app_secret = input("Please provide your APP_SECRET [found on developer.schwab.com]: ")
                data = {'app_key': app_key, 'app_secret': app_secret}
                with open(credentials_file, 'w') as yaml_file:
                    yaml.dump(data, yaml_file, default_flow_style=False)
                encrypt_file_with_password(credentials_file)
    
                           

trader = Trader(args) # Create the Trader Object.
# ----------------------------------------- Trade Functions -------------------------------------- #
# In the following code you can either manually creates trade calls here, or import from examples.py
# ------------------------------------------------------------------------------------------------ #


# trader.get_account_balance()
# trader._refresh_token()
# trader.quote('AAPL')
# trader.test2() Only working trade call ATM lol. 
# Below imports trade code to exectue
