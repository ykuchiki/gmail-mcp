# Gmail MCP

<p align="center">
  <img src="https://raw.githubusercontent.com/ykuchiki/gmail-mcp/main/assets/gmail-mcp-logo.png" alt="Gmail MCP Logo" width="200">
</p>

<p align="center">
  <a href="https://github.com/ykuchiki/gmail-mcp/LICENSE">
    <img src="https://img.shields.io/github/license/ykuchiki/gmail-mcp" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/MCP-compatible-brightgreen.svg" alt="MCP Compatible">
</p>

<p align="center">
  <b>Gmail API for AI assistants using Model Context Protocol</b><br>
  <b><a href="#english">English</a> | <a href="#japanese">日本語</a></b>
</p>

---

<a id="english"></a>

## 📋 English Documentation

Pull requests to this repository are welcome.

### 📖 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [License](#license)

### 🔍 Overview

Gmail MCP is a server implementation that enables AI assistants to interact with Gmail through the MCP (Model Context Protocol). It provides tools for sending emails, managing drafts, reading emails, searching through your inbox, and managing Gmail labels.

### ✨ Features

- ✉️ Send emails and create drafts
- 📬 Read and search emails 
- 🗑️ Delete emails
- 🏷️ Manage Gmail labels (create, update, delete)
- 🔐 OAuth2.0 authentication with Gmail API

### 📋 Prerequisites

- Python 3.11 or higher
- Gmail account
- Google Cloud Platform project with Gmail API enabled
- [uv](https://github.com/astral-sh/uv) - Python package installer

### 🚀 Setup

1. Clone this repository
```bash
git clone https://github.com/ykuchiki/gmail-mcp.git
cd gmail-mcp
```

2. Create and activate a virtual environment
```bash
uv init
```

3. Install dependencies
```bash
uv pip install -r requirements.txt
```

4. Set up OAuth credentials
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Create OAuth credentials
   - Download the credentials JSON file and save it as `credentials/client_secret_gmail_oauth.json`

5. Add MCP server
Please refer to your MCP client's official documentation for specific instructions. Make sure to adjust the path according to your environment.
```json
{
    "mcpServers": {
        "gmail-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/your/gmail-mcp",
                "run",
                "main.py"
            ]
        }
    }
}
```

6. Run the server
```bash
uv run main.py
```

### 💡 Usage

The server can be used with any MCP-compatible client. On first run, it will prompt you to authenticate with your Gmail account.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<a id="japanese"></a>

## 📋 日本語ドキュメント

本リポジトリはpullリクエスト大歓迎です。

### 📖 目次
- [概要](#概要)
- [機能](#機能)
- [前提条件](#前提条件)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [ライセンス](#ライセンス)

### 🔍 概要

Gmail MCPは、AIアシスタントがMCP（Model Context Protocol）を通じてGmailを使用できるようにするサーバー実装です。メールの送信、下書きの管理、メールの読み取り、受信トレイの検索、Gmailラベルの管理などのツールを提供します。

### ✨ 機能

- ✉️ メールの送信と下書き作成
- 📬 メールの読み取りと検索
- 🗑️ メールの削除
- 🏷️ Gmailラベルの管理（作成、更新、削除）
- 🔐 Gmail APIとのOAuth2.0認証

### 📋 前提条件

- Python 3.11以上
- Gmailアカウント
- Gmail APIが有効化されたGoogle Cloud Platformプロジェクト
- [uv](https://github.com/astral-sh/uv) - Pythonパッケージインストーラー

### 🚀 セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/ykuchiki/gmail-mcp.git
cd gmail-mcp
```

2. 仮想環境の作成と有効化
```bash
uv init
```

3. 依存関係のインストール
```bash
uv pip install -r requirements.txt
```

4. OAuth認証情報の設定
   - [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
   - Gmail APIを有効化
   - OAuth認証情報を作成
   - 認証情報JSONファイルをダウンロードし、`credentials/client_secret_gmail_oauth.json`として保存

5. MCPサーバーを追加
追加方法はご使用のMCPクライアントの公式ドキュメントをご確認ください。
また、パスは環境に合わせて修正してください。
```json
{
    "mcpServers": {
        "gmail-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/your/gmail-mcp",
                "run",
                "main.py"
            ]
        }
    }
}
```

6. サーバーの実行
```bash
uv run main.py
```

### 💡 使用方法

このサーバーは、MCP互換のクライアントと共に使用できます。初回実行時には、Gmailアカウントで認証するよう促されます。

### 📄 ライセンス

このプロジェクトはMITライセンスの下で提供されています - 詳細は[LICENSE](LICENSE)ファイルをご覧ください。
