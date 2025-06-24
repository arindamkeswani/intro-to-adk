from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from dotenv import load_dotenv
import os
load_dotenv()
import pathlib
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


KEYFILE_PATH = os.getcwd() + "/gdrive/credentials/gcp-oauth.keys.json"
CREDENTIALS_PATH = os.getcwd() + "/gdrive/credentials/.gdrive-server-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
PORT = 8080

# -- Google Drive Client --
def get_drive_client():
    authenticate_and_save()
    creds = Credentials.from_authorized_user_file(CREDENTIALS_PATH, SCOPES)
    return build("drive", "v3", credentials=creds)

def authenticate_and_save():
    if os.path.exists(CREDENTIALS_PATH):
        return
    
    flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, SCOPES)
    creds = flow.run_local_server(port=PORT)
    pathlib.Path(os.path.dirname(CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_PATH, "w") as f:
        f.write(creds.to_json())
    print(f"Credentials saved to {CREDENTIALS_PATH}")

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

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='filesystem_assistant_agent',
    instruction= 'Help the user manage their files. You can list files, search files, read files on Google Drive.'
    tools=[
        list_drive_files, read_drive_file
    ],
)
