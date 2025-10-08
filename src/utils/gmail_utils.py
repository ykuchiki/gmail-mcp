import re
import os
import base64
import mimetypes
from typing import List, Dict, Any, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource


service: Optional[Resource] = None

def load_credentials(config_path: str, cred_path: str, oauth_path: str, scopes: List[str]) -> None:
    """OAuth2.0 credentialsを読み込み/更新し、Gmail APIクライアントを初期化する"""
    # exist_ok=True: ディレクトリが存在しない場合は作成, Falseの場合はディレクトリが存在しない場合はエラー
    os.makedirs(config_path, exist_ok=True)
    creds = None
    if os.path.exists(cred_path):
        try:
        # cred_pathあるcredentias.jsonからGoogle APIにアクセスできるトークン情報を読み込んでCredentialsオブジェクトを作成
            creds = Credentials.from_authorized_user_file(cred_path, scopes)
        except ValueError:
            os.remove(cred_path)
            creds = None
    if not creds or not creds.valid:
        # トークン情報がないか期限切れの場合は新しく作成
        if creds and creds.expired and creds.refresh_token:
            # トークン情報が期限切れで、リフレッシュトークンがある場合はリフレッシュ
            creds.refresh(Request())
        else:
            # トークン情報がないか期限切れで、リフレッシュトークンがない場合は認証サーバーにアクセスして認証
            flow = InstalledAppFlow.from_client_secrets_file(oauth_path, scopes)
            # 認証サーバーにアクセスして認証
            creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
        with open(cred_path, "w") as token:
            token.write(creds.to_json())
    global service
    service = build("gmail", "v1", credentials=creds)
            


def encode_email_header(text: str) -> str:
    """
    RFC2047 に準拠して、非ASCII文字を含むヘッダをBase64でエンコードする
    """
    # 非 ASCII文字が含まれるかチェック
    if re.search(r'[^\x00-\x7F]', text):
        # Base64でエンコード
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        # エンコードした文字列をもとに、RFC2047の形式の文字列を作成
        return f"=?UTF-8?b?{encoded}?="
    return text


def validate_email(email: str) -> bool:
    """
    簡易的な正規表現でメールアドレス形式をチェック
    完全網羅はしてないが、基本的な検証には有用
    """
    email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    return bool(email_regex.match(email))


def create_email_message(args: Dict[str, Any]) -> str:
    """
    引数で渡されたメール情報をもとに
    SMTPで送信可能なMIMEメールを文字列で構築する

    args のキー:
        - from: 送信者アドレス (str)
        - to: 受信者リスト (List[str])
        - cc: CC リスト (Optional[List[str]])
        - bcc: BCC リスト (Optional[List[str]])
        - in_reply_to: メッセージ ID (Optional[str])
        - subject: 件名 (str)
        - body: 本文 (str)
        - attachments: 添付ファイルパスのリスト (Optional[List[str]])

    return:
        - RFC 5322 形式のMIMEメール本文 (str)
    """
    # 件名をエンコード
    # args.get("subject", ""): argsという辞書の中からsubjectというキーの値を取得
    # もしsubjectがない場合は空文字を返す
    subject = encode_email_header(args.get("subject", ""))

    # 受信者アドレス検証
    to_list: List[str] = args.get("to", [])
    for addr in to_list:
        if not validate_email(addr):
            raise ValueError(f"Invalid email address: {addr}")

    attachments: Optional[List[str]] = args.get("attachments")

    # 添付ファイルなし: 従来どおりプレーンテキストを返す（後方互換）
    if not attachments:
        headers: List[str] = []
        headers.append(f"From: {args.get('from', 'me')}")
        headers.append(f"To: {', '.join(to_list)}")
        if args.get("cc"):
            headers.append(f"Cc: {', '.join(args['cc'])}")
        if args.get("bcc"):
            headers.append(f"Bcc: {', '.join(args['bcc'])}")
        headers.append(f"Subject: {subject}")
        if args.get("in_reply_to"):
            headers.append(f"In-Reply-To: {args['in_reply_to']}")
            headers.append(f"References: {args['in_reply_to']}")
        headers.append("MIME-Version: 1.0")
        headers.append("Content-Type: text/plain; charset=UTF-8")
        headers.append("Content-Transfer-Encoding: 7bit")

        message = "\r\n".join(headers) + "\r\n\r\n" + args.get("body", "")
        return message

    # 添付ファイルあり: multipart/mixed を構築
    if not isinstance(attachments, list):
        raise ValueError("'attachments' must be a list of file paths")

    # 合計サイズ上限（約24MB）チェック
    total_bytes = 0
    for path in attachments:
        if not isinstance(path, str) or not os.path.isfile(path):
            raise ValueError(f"Attachment not found: {path}")
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            raise ValueError(f"Cannot access attachment: {path}")
    max_bytes = 24 * 1024 * 1024
    if total_bytes > max_bytes:
        raise ValueError(f"Attachments too large: total {total_bytes} bytes exceeds limit {max_bytes} bytes")

    msg = MIMEMultipart('mixed')
    msg['From'] = args.get('from', 'me')
    msg['To'] = ', '.join(to_list)
    if args.get('cc'):
        msg['Cc'] = ', '.join(args['cc'])
    if args.get('bcc'):
        msg['Bcc'] = ', '.join(args['bcc'])
    msg['Subject'] = subject
    if args.get('in_reply_to'):
        msg['In-Reply-To'] = args['in_reply_to']
        msg['References'] = args['in_reply_to']

    body_text = args.get('body', '')
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

    for path in attachments:
        ctype, _ = mimetypes.guess_type(path)
        if not ctype:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(path, 'rb') as f:
            data = f.read()
        part = MIMEBase(maintype, subtype)
        part.set_payload(data)
        encoders.encode_base64(part)
        filename = os.path.basename(path)
        # RFC2231 形式でUTF-8ファイル名を付与
        part.add_header('Content-Disposition', 'attachment', filename=("utf-8", '', filename))
        msg.attach(part)

    return msg.as_string()
    
