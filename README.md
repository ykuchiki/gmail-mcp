# Gmail MCP

<p align="center">
  <img src="https://github.com/ykuchiki/gmail-mcp/blob/main/assets/gmail-mcp-logo.png" alt="Gmail MCP Logo" width="200">
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
  <b><a href="#english">English</a> | <a href="#spanish">Español</a> | <a href="#japanese">日本語</a></b>
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

<a id="overview"></a>
### 🔍 Overview

Gmail MCP is a server implementation that enables AI assistants to interact with Gmail through the MCP (Model Context Protocol). It provides tools for sending emails, managing drafts, reading emails, searching through your inbox, managing Gmail labels and manageing filters.

<a id="features"></a>
### ✨ Features

- ✉️ Send emails and create drafts
- 📬 Read and search emails 
- 🗑️ Delete emails
- 🏷️ Manage Gmail labels (create, update, delete)
- 🗂️ Manage Gmail filters (create, update, delete)
- 🔐 OAuth2.0 authentication with Gmail API

<a id="Prerequisites"></a>
### 📋 Prerequisites

- Python 3.11 or higher
- Gmail account
- Google Cloud Platform project with Gmail API enabled
- [uv](https://github.com/astral-sh/uv) - Python package installer

<a id="Setup"></a>
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
   - Create a directory named credentials in the root of the project
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Create OAuth credentials
   - Add the following URI to the **Authorized redirect URIs**:
     ```
     http://localhost:8080/
     ```
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
                "/path/to/your/gmail-mcp/src",
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

<a id="Usage"></a>
### 💡 Usage

The server can be used with any MCP-compatible client. On first run, it will prompt you to authenticate with your Gmail account.

<a id="License"></a>
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


<a id="概要"></a>
### 🔍 概要

Gmail MCPは、AIアシスタントがMCP（Model Context Protocol）を通じてGmailを使用できるようにするサーバー実装です。メールの送信、下書きの管理、メールの読み取り、受信トレイの検索、Gmailラベルの管理、フィルタの管理などのツールを提供します。

<a id="機能"></a>
### ✨ 機能

- ✉️ メールの送信と下書き作成
- 📬 メールの読み取りと検索
- 🗑️ メールの削除
- 🏷️ Gmailラベルの管理（作成、更新、削除）
- 🗂️ フィルタの管理（作成、更新、削除）
- 🔐 Gmail APIとのOAuth2.0認証
\- 📎 添付ファイル送信・下書き（複数可, ローカルファイルパス）

<a id="前提条件"></a>
### 📋 前提条件

- Python 3.11以上
- Gmailアカウント
- Gmail APIが有効化されたGoogle Cloud Platformプロジェクト
- [uv](https://github.com/astral-sh/uv) - Pythonパッケージインストーラー

<a id="セットアップ"></a>
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
   - 最初にプロジェクトのルートディレクトリ直下にcredentialsディレクトリを作成
   - [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
   - Gmail APIを有効化
   - OAuth認証情報を作成
   - **認証済みのリダイレクトURI**に以下を追加:
     ```
     http://localhost:8080/
     ```
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
                "/path/to/your/gmail-mcp/src",
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

<a id="使用方法"></a>
### 💡 使用方法

このサーバーは、MCP互換のクライアントと共に使用できます。初回実行時には、Gmailアカウントで認証するよう促されます。

#### 添付ファイルを付けて送信 / 下書き作成

`attachments` 引数でローカルファイルのパスを指定します（複数可・絶対パス推奨）。

例: 送信
```json
{
  "to": ["someone@example.com"],
  "subject": "レポート送付の件",
  "body": "ご確認ください。",
  "attachments": [
    "/Users/you/Documents/report.pdf",
    "/Users/you/Pictures/logo.png"
  ]
}
```

例: 下書き作成
```json
{
  "to": ["someone@example.com"],
  "subject": "資料",
  "body": "添付しています。",
  "attachments": ["/absolute/path/to/file.txt"]
}
```

注意事項:
- 合計サイズは約24MBを上限とし、それを超える場合はエラーになります（Gmailの25MB制限に対する安全余裕）。
- MIMEタイプは自動推定します。判別できない場合は`application/octet-stream`として送信します。
- ファイルが存在しない/読み取り不可の場合はエラーになります。

<a id="ライセンス"></a>
### 📄 ライセンス

このプロジェクトはMITライセンスの下で提供されています - 詳細は[LICENSE](LICENSE)ファイルをご覧ください。

---

<a id="spanish"></a>

## 📋 Documentación en Español

Las pull requests a este repositorio son bienvenidas.

### 📖 Tabla de Contenidos
- [Descripción General](#descripción-general)
- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Configuración](#configuración)
- [Uso](#uso)
- [Licencia](#licencia)

<a id="Descripción General"></a>
### 🔍 Descripción General

Gmail MCP es una implementación de servidor que permite a los asistentes de IA interactuar con Gmail a través del MCP (Model Context Protocol). Proporciona herramientas para enviar correos electrónicos, gestionar borradores, leer correos, buscar en tu bandeja de entrada y administrar etiquetas de Gmail.

<a id="Características"></a>
### ✨ Características

- ✉️ Enviar correos y crear borradores
- 📬 Leer y buscar correos
- 🗑️ Eliminar correos
- 🏷️ Gestionar etiquetas de Gmail (crear, actualizar, eliminar)
- 🔐 Autenticación OAuth2.0 con la API de Gmail

<a id="Requisitos Previos"></a>
### 📋 Requisitos Previos

- Python 3.11 o superior
- Cuenta de Gmail
- Proyecto en Google Cloud Platform con la API de Gmail habilitada
- [uv](https://github.com/astral-sh/uv) - Instalador de paquetes Python

<a id="Configuración"></a>
### 🚀 Configuración

1. Clonar este repositorio
```bash
git clone https://github.com/ykuchiki/gmail-mcp.git
cd gmail-mcp
```

2. Crear y activar un entorno virtual
```bash
uv init
```

3. Instalar dependencias
```bash
uv pip install -r requirements.txt
```

4. Configurar credenciales OAuth
   - Crear un directorio llamado credentials en la raíz del proyecto
   - Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
   - Habilitar la API de Gmail
   - Crear credenciales OAuth
   - Agregar la siguiente URI a las **URIs de redirección autorizadas**:
     ```
     http://localhost:8080/
     ```
   - Descargar el archivo JSON de credenciales y guardarlo como `credentials/client_secret_gmail_oauth.json`

5. Agregar servidor MCP
Por favor, consulta la documentación oficial de tu cliente MCP para instrucciones específicas. Asegúrate de ajustar la ruta según tu entorno.
```json
{
    "mcpServers": {
        "gmail-mcp": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/your/gmail-mcp/src",
                "run",
                "main.py"
            ]
        }
    }
}
```

6. Ejecutar el servidor
```bash
uv run main.py
```

<a id="Uso"></a>
### 💡 Uso

El servidor puede ser utilizado con cualquier cliente compatible con MCP. En la primera ejecución, te pedirá que te autentiques con tu cuenta de Gmail.

<a id="Licencia"></a>
### 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

---

### TODO
- [x] 基本機能実装
- [ ] search_emailsで送信メールIDは除外or違う方法で実装
