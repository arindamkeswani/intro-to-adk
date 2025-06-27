from google.adk.agents.llm_agent import LlmAgent
from dotenv import load_dotenv
import os
load_dotenv()
import pathlib
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

import asyncio
from email.message import EmailMessage
from email import message_from_bytes

import base64
from base64 import urlsafe_b64decode


KEYFILE_PATH = os.getcwd() + "/gsuite/credentials/gcp-oauth.keys.json"
GDRIVE_CREDENTIALS_PATH = os.getcwd() + "/gsuite/credentials/.gdrive-server-credentials.json"
GMAIL_CREDENTIALS_PATH = os.getcwd() + "/gsuite/credentials/.gmail-server-credentials.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
PORT = 8080

def authenticate_and_save(app: str = "drive"):
    
    if(app == "drive"):
        if os.path.exists(GDRIVE_CREDENTIALS_PATH):
            return
        
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, DRIVE_SCOPES)
        creds = flow.run_local_server(port=PORT)
        pathlib.Path(os.path.dirname(GDRIVE_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GDRIVE_CREDENTIALS_PATH}")
    if(app == "gmail"):
        if os.path.exists(GMAIL_CREDENTIALS_PATH):
            return
        
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, GMAIL_SCOPES)
        creds = flow.run_local_server(port=PORT)
        pathlib.Path(os.path.dirname(GMAIL_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GMAIL_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GMAIL_CREDENTIALS_PATH}")

# -- Google Drive Client --
def get_drive_client():
    authenticate_and_save("drive")
    creds = Credentials.from_authorized_user_file(GDRIVE_CREDENTIALS_PATH, DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds)

def list_drive_files(page_size: int = 10, cursor: str = "", query: str = "") -> dict:
    """List files in Google Drive.
    Args:
        cursor (string): Page token for pagination, which can be None.
        page_size (int): Number of files to return per page.
        query (str): Query string to filter files.
    Returns:
        dict: A dictionary containing a list of files and the next page token.
    """

    drive = get_drive_client()
    if not query:
        query = "trashed = false"
    else:
        query = f"name contains '{query}' and trashed = false"
    params = {"pageSize": page_size, "fields": "nextPageToken, files(id, name, mimeType)", "q": query}
    if cursor:
        params["pageToken"] = cursor
    resp = drive.files().list(**params).execute()
    files = resp.get("files", [])
    return {"resources": [{"uri": f"gdrive:///{f['id']}", "mimeType": f["mimeType"], "name": f["name"]} for f in files], "nextCursor": resp.get("nextPageToken")}

def read_drive_file(file_id: str):
    drive = get_drive_client()
    meta = drive.files().get(fileId=file_id, fields="mimeType").execute()
    mime = meta.get("mimeType", "")
    if mime.startswith("application/vnd.google-apps"):
        exports = {
            "application/vnd.google-apps.document": "text/markdown",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "text/plain",
            "application/vnd.google-apps.drawing": "image/png",
        }
        out_type = exports.get(mime, "text/plain")
        data = drive.files().export(fileId=file_id, mimeType=out_type).execute()
        return {"mimeType": out_type, "content": data}
    resp = drive.files().get_media(fileId=file_id).execute()
    if mime.startswith("text/") or mime == "application/json":
        text = resp.decode("utf-8")
    else:
        text = resp.encode("base64")
    return {"mimeType": mime, "content": text}


# -- Gmail Client --
def get_gmail_client():
    authenticate_and_save("gmail")
    creds = Credentials.from_authorized_user_file(GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
    return build("gmail", "v1", credentials=creds)

def get_current_user_email_id():
    """Get current user's email address"""
    client = get_gmail_client()
    profile = client.users().getProfile(userId='me').execute()
    emailId = profile.get("emailAddress", "")

    return {
        "content": {
            "emailId": emailId,
        }
    }

async def send_email(sender_id: str, recipient_id: str, subject: str, message: str,) -> dict:
    """Creates and sends an email message"""
    client = get_gmail_client()
    message_obj = EmailMessage()
    message_obj.set_content(message)
    
    message_obj['To'] = recipient_id
    message_obj['From'] = sender_id
    message_obj['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message_obj.as_bytes()).decode()
    create_message = {'raw': encoded_message}
    
    send_message = await asyncio.to_thread( 
        client.users().messages().send(userId="me", body=create_message).execute
    )
    return {"status": "success", "message_id": send_message["id"]}

async def get_emails(type: str = "unread"):
        """
        Fetch messages from mailbox.
        Returns list of messsage IDs in as 'message_id'.
        """
        client = get_gmail_client()

        user_id = 'me'
        query = f'in:inbox is:{type} category:primary'

        response = client.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = client.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages


async def read_email_content(email_id: str) -> dict[str, str]| str:
    """Retrieves email contents including to, from, subject, and contents."""

    client = get_gmail_client()

    msg = client.users().messages().get(userId="me", id=email_id, format='raw').execute()
    email_data = {}

    raw_data = msg['raw']
    decoded_data = urlsafe_b64decode(raw_data)

    mime_message = message_from_bytes(decoded_data)

    # Extract the email body
    body = None
    if mime_message.is_multipart():
        for part in mime_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = mime_message.get_payload(decode=True).decode()
    email_data['content'] = body
    
    email_data['subject'] = mime_message.get('subject', '')
    email_data['from'] = mime_message.get('from','')
    email_data['to'] = mime_message.get('to','')
    email_data['date'] = mime_message.get('date','')
    
    
    # DIY: Mark email as read

    return email_data
    
async def delete_email(message_id: str) -> str:
    """Moves email to trash given ID."""
    client = get_gmail_client()
    client.users().messages().trash(userId="me", id=message_id).execute()
    return "Email deleted successfully."



root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='gsuite_assistant_agent',
    instruction= 'Help the user use Google\'s services. ' \
    'Manage their files. You can list files, search files, read files on Google Drive.'\
    'You can also read, send & delete emails, and get the current user\'s information.',
    tools=[
        list_drive_files, read_drive_file, 
        get_current_user_email_id, send_email, get_emails, read_email_content, delete_email
    ],
)
