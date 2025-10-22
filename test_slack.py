import os
import requests
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv('SLACK_WEBHOOK_URL')

if not webhook_url:
    print("❌ SLACK_WEBHOOK_URL not found in .env")
    exit(1)

payload = {
    "text": "🎉 Training Orchestrator Test",
    "attachments": [{
        "color": "good",
        "title": "Connection Test",
        "text": "Your Slack integration is working!",
        "footer": "Training Orchestrator"
    }]
}

response = requests.post(webhook_url, json=payload)

if response.status_code == 200:
    print("✅ Slack notification sent successfully!")
else:
    print(f"❌ Failed to send notification: {response.status_code}")
    print(response.text)
