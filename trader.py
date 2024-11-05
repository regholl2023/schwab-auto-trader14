# Trader.py is where the simplified trade class is. 
# Imports
import datetime
import os
import requests
import urllib.parse
import json

from tokens import Tokens

class Trader:
    

    def __init__(self):
        self.tk = Tokens()
        