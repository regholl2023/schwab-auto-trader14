# Not needed atm. 
# Beep Beep Beep!
from tokens import Tokens
import argparse
import os
from getpass import getpass

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

trader = Tokens(args)
