import os

BUCKET_NAME = os.environ["BUCKET_NAME"]
GCS_PREFIX = "downloads/bcc/"

TOKEN_FILE = "token.json"
CLIENT_FILE = "client_secret.json"

SENDER = "info@bcc.kz"
SUBJECT = "Выписка"

GOOGLE_APPLICATION_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]