# 📥 Gmail Attachment Parser to GCS

This project automatically parses Gmail messages with specific subjects/senders, downloads their attachments, stores them in Google Cloud Storage (GCS), and returns signed URLs in JSON format or sends them to an external endpoint.

## 🚀 Features

- Searches Gmail for messages with a defined subject and sender
- Downloads only new (unprocessed) attachments
- Saves attachments to GCS with a naming convention based on the email date
- Generates signed URLs for private file access
- Supports optional sending of signed URLs to an external endpoint (webhook)
- Designed to run on **Google Cloud Run** with **--no-allow-unauthenticated**
- Compatible with **Cloud Scheduler** for periodic execution

## ⚙️ Configuration

The app uses environment variables and optionally Google Secret Manager:

| Variable                      | Description                                     |
|------------------------------|-------------------------------------------------|
| `BUCKET_NAME`                | GCS bucket name                                |
| `GCS_PREFIX`                 | Folder path inside the bucket (e.g. `downloads/bcc/`) |
| `EMAIL_SUBJECT`              | Email subject filter                           |
| `EMAIL_SENDER`               | Email sender filter (e.g. `info@bcc.kz`)       |
| `NOTIFY_ENDPOINT` *(optional)* | URL to POST signed URLs instead of printing   |
| `GOOGLE_APPLICATION_CREDENTIALS` | JSON service account (passed as string)     |

## 🗂 Folder Structure

```
gmail_parser/
├── main.py                  # Flask entry point
├── main_cli.py              # CLI entry point
├── config.py                # Config system
├── config_cli.py            # Config system for cli
├── requirements.txt         # Python dependencies
├── Dockerfile               # Cloud Run Docker build
├── .dockerignore
```

## 🐳 Deployment (Cloud Run)

Build and deploy:

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gmail-parser
```

```bash
gcloud run deploy gmail-parser \
  --image gcr.io/YOUR_PROJECT_ID/gmail-parser \
  --platform managed \
  --region australia-southeast1 \
  --no-allow-unauthenticated \
  --set-secrets GOOGLE_APPLICATION_CREDENTIALS=gmail-sa-key:latest,BUCKET_NAME=gmail-bucket-key:latest \
  --set-env-vars EMAIL_SUBJECT="...",EMAIL_SENDER="..."
```

## 🕒 Run on Schedule (Cloud Scheduler)

```bash
gcloud scheduler jobs create http gmail-parser-cron \
  --schedule="0 7 * * *" \
  --uri=https://<cloud-run-url> \
  --http-method=GET \
  --oidc-service-account-email=scheduler-sa@your-project.iam.gserviceaccount.com \
  --location=australia-southeast1
```

## 🔐 Security

- Cloud Run is private (`--no-allow-unauthenticated`)
- All secrets (tokens, service accounts) are stored in Secret Manager
- GCS access via signed URLs only

## 🧪 Local Development

```bash
python main.py  # or main-cli.py
```

Make sure to load `.env` or set environment variables manually.  
Use a virtual environment and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🛠 Requirements

- Python 3.10+
- Google Cloud SDK
- Gmail API enabled
- GCS bucket created
- Service Account with Gmail + GCS access

## 📄 License

MIT
