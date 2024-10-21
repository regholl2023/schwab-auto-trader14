import os
from flask import Request
import base64
import requests
from loguru import logger

# 
def refresh_tokens():
    app_key = os.getenv('secret_app_id')
    app_secret = os.getenv('secret_app_secret')
    refresh_token_value = os.getenv('secret_refresh_token')

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