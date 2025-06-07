import os
import json
import base64
from flask import Flask
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.cloud import storage
from google.oauth2 import service_account

from config import BUCKET_NAME, GCS_PREFIX, TOKEN_FILE, CLIENT_FILE, SENDER, SUBJECT, GOOGLE_APPLICATION_CREDENTIALS

app = Flask(__name__)

# Загружаем token и client_secret из GCS
def download_from_gcs(bucket, filename):
    blob = bucket.blob(filename)
    blob.download_to_filename(filename)
    

# Авторизация в Gmail API
def get_gmail_service(bucket):
    download_from_gcs(bucket, CLIENT_FILE)
    download_from_gcs(bucket, TOKEN_FILE)

    with open(TOKEN_FILE) as f:
        token_info = json.load(f)

    creds = Credentials.from_authorized_user_info(token_info, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
    return build('gmail', 'v1', credentials=creds)

def get_storage_client():
    sa_info = json.loads(GOOGLE_APPLICATION_CREDENTIALS)
    credentials = service_account.Credentials.from_service_account_info(sa_info)

    return storage.Client(credentials=credentials, project=sa_info["project_id"])


def list_existing_blobs(bucket, prefix):
    return {blob.name for blob in bucket.list_blobs(prefix=prefix)}

def sanitize_filename(name):
    return name.replace(" ", "_").replace("/", "_")

def find_messages(service, sender, subject):
    query = f'from:{sender} subject:"{subject}" has:attachment'
    results = service.users().messages().list(userId='me', q=query).execute()
    return results.get('messages', [])

def upload_to_gcs(bucket, destination_blob_name, data):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(data)

    signed_url = generate_signed_url(blob)
    return signed_url
    #print(f"✅ Loaded in GCS: {destination_blob_name}")
    #print(f"🔗 Link: {signed_url}")

def generate_signed_url(blob, expiration_minutes=60):
    sa_info = json.loads(GOOGLE_APPLICATION_CREDENTIALS)
    сredentials = service_account.Credentials.from_service_account_info(sa_info)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
        credentials=сredentials
    )

def download_attachments(service, messages, bucket, prefix):
    existing_files = list_existing_blobs(bucket, prefix)
    new_files = []

    for msg in messages:
        full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
        
        headers = full_msg['payload'].get('headers', [])
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), None)
        try:
            msg_date = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
            date_prefix = msg_date.strftime("%Y-%m-%d")
        except:
            date_prefix = "unknown-date"

        parts = full_msg['payload'].get('parts', [])

        for part in parts:
            if 'filename' in part and part['filename'] and 'attachmentId' in part['body']:
                original_name = sanitize_filename(part['filename'])
                final_blob_name = f"{date_prefix}_{msg['id']}_{original_name}"
                prefix_blob_name = f"{prefix}{final_blob_name}"

                if prefix_blob_name in existing_files:
                    #print(f"⏩ Уже есть в GCS: {final_blob_name}")
                    continue

                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(
                    userId='me', messageId=msg['id'], id=att_id).execute()
                data = base64.urlsafe_b64decode(att['data'])
                signed_url = upload_to_gcs(bucket, prefix_blob_name, data)

                new_files.append({
                    "filename": final_blob_name,
                    "signed_url": signed_url
                })

    return new_files

@app.route("/")
def index():
    storage_client = get_storage_client()
    bucket = storage_client.bucket(BUCKET_NAME)

    service = get_gmail_service(bucket)
    messages = find_messages(service, SENDER, SUBJECT)
    if not messages:
        return json.dumps({"new_files": []})
    
    new_files = download_attachments(service, messages, bucket, GCS_PREFIX)
    
    result = {"new_files": new_files}

    return json.dumps(result, indent=2, ensure_ascii=False)
