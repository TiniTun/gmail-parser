from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Сохрани token
with open('token.json', 'w') as token:
    token.write(creds.to_json())
