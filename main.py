"""
main.py - Gmail MCP Serverエントリーポイント
"""
import asyncio
from dotenv import load_dotenv

from src.server import create_server, init_gmail_credentials

# 環境変数のロード
load_dotenv()

def main():
    """メイン実行関数"""
    # Gmail認証
    asyncio.run(init_gmail_credentials())
    
    # サーバー作成
    server = create_server()
    
    # サーバー起動
    print("[INFO] Starting Gmail MCP server...")
    server.run(transport="stdio")

if __name__ == "__main__":
    main()