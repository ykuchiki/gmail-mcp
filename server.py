"""
server.py - Gmail MCPサーバー設定と初期化
"""
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
import utils.gmail_utils as gmail_utils
from tools import (
    send_email, create_draft, read_email, search_emails, delete_email,
    modify_label, create_label_tool, delete_label_tool, list_labels_tool,
    get_or_create_label_tool, update_label_tool, find_label_by_name_tool
)

# 設定
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
OAUTH_KEYS = os.getenv("GMAIL_OAUTH_PATH", str(CREDENTIALS_DIR / "client_secret_gmail_oauth.json"))
CRED_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", str(CREDENTIALS_DIR / "credentials.json"))
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def create_server() -> FastMCP:
    """MCP サーバーの作成とツール登録"""
    server = FastMCP("gmail", version="1.0.0")
    
    # ツール登録
    server.tool()(send_email)
    server.tool()(create_draft)
    server.tool()(read_email)
    server.tool()(search_emails)
    server.tool()(delete_email)
    server.tool()(modify_label)
    server.tool()(create_label_tool)
    server.tool()(delete_label_tool)
    server.tool()(list_labels_tool)
    server.tool()(get_or_create_label_tool)
    server.tool()(update_label_tool)
    server.tool()(find_label_by_name_tool)
    
    return server

async def init_gmail_credentials():
    """Gmail認証を行う"""
    await gmail_utils.load_credentials(
        config_path=os.getenv("GMAIL_CONFIG_PATH", str(BASE_DIR)),
        cred_path=CRED_PATH,
        oauth_path=OAUTH_KEYS,
        scopes=SCOPES
    )