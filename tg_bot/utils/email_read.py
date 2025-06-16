import base64
import re
import time
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailOTPExtractor:
    def __init__(self, token_file, credentials_file='credintals.json'):
        self.token_file = token_file
        self.creds = None

        if os.path.exists(token_file):
            self.creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)

    def extract_otp(self, text):
        patterns = [
            r"The OTP for your application with VFS Global is (\d{6})",
            r"OTP for your application with VFS Global is (\d{6})",
            r"VFS.*?(\d{4,8})",
            r"OTP[:\s]+(\d{4,8})",
            r"verification code[:\s]+(\d{4,8})",
            r"security code[:\s]+(\d{4,8})",
            r"access code[:\s]+(\d{4,8})",
            r"code[:\s]+(\d{4,8})",
            r"\b(\d{6})\b"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def get_email_body(self, payload):
        body = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body += base64.urlsafe_b64decode(part['body']['data']).decode()
                elif part['mimeType'] == 'text/html' and 'data' in part['body']:
                    html = base64.urlsafe_b64decode(part['body']['data']).decode()
                    text = re.sub(r'<[^>]+>', ' ', html)
                    body += text
        elif 'body' in payload and 'data' in payload['body']:
            body += base64.urlsafe_b64decode(payload['body']['data']).decode()
        return body.strip()

    def read_otp(self, wait_time=30):
        query = 'from:vfsglobal.com OR subject:(VFS Global OTP)'
        end_time = time.time() + wait_time
        print("Waiting for OTP email...")

        while time.time() < end_time:
            results = self.service.users().messages().list(userId='me', q=query, maxResults=5).execute()
            messages = results.get('messages', [])
            for msg in messages:
                msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                payload = msg_data['payload']
                body = self.get_email_body(payload)
                code = self.extract_otp(body)
                if code:
                    print(f"OTP found: {code}")
                    return code
            time.sleep(3)
            print("Retrying...")
        print("Timeout waiting for OTP")
        return None
