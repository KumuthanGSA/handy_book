import json
import os
from django.conf import settings

# Local imports
from core.models import MobileUsers

# Third party imports
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

def get_recipient_fcm_tokens( recipient_type):
        if recipient_type == 'all users':
            users = MobileUsers.objects.filter(fcm_token__isnull=False)
            return [user.fcm_token for user in users]
        
        else:
            return []

def get_access_token():
    """Retrieve a valid access token that can be used to authorize requests.    
    :return: Access token.
    """
    credentials = service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS, scopes=['https://www.googleapis.com/auth/firebase.messaging'])
    request = Request()
    credentials.refresh(request)

    return credentials.token

def send_fcm_notification(tokens, title, body, image):
    access_token = get_access_token()

    failed_tokens = []
    sent_count = 0
    sent_failed_count = 0

    for token in tokens:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json; UTF-8',
        }

        payload = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                    "image": image
                }
            }
        }

        response = requests.post(settings.FCM_URL, headers=headers, json=payload)
        if response.status_code != 200:
            failed_tokens.append(token)
            sent_failed_count += 1
            continue

        sent_count += 1

    detail = {
        "response": response,
        "failed_tokens": failed_tokens,
        "sent_count": sent_count,
        "failed_count": sent_failed_count
    }

    return detail