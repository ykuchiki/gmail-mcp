"""
tools.py - Gmail操作のためのツール定義
メール送信・下書き・読み取り・検索・修正・削除およびラベル管理機能また、ラベル操作関連のツール定義を提供
"""
import base64
import json
from typing import Dict, Any, Tuple, List
from bs4 import BeautifulSoup

# Utilities
from utils.label_manager import (
    create_label, update_label, delete_label,
    list_labels, find_label_by_name, get_or_create_label
)
import utils.gmail_utils as gmail_utils
from utils.utils import decode_base64url


# --- Tools: Email操作 ---
async def send_email(args: Dict[str, Any]) -> str:
    """
    指定されたパラメータでメールを送信します。

    Args:
        args (Dict[str, Any]): 以下のキーを持つ辞書。
            - to (List[str]): 送信先メールアドレスのリスト。
            - subject (str): メールの件名。
            - body (str): メール本文。
            - cc (List[str], optional): CC先のアドレスリスト。
            - bcc (List[str], optional): BCC先のアドレスリスト。
            - in_reply_to (str, optional): 返信元メッセージID。
            - threadid (str, optional): スレッドID。
            - attachments (List[str], optional): 添付ファイルのローカルパス（複数可、絶対パス推奨）。

    Returns:
        str: 送信結果メッセージ (例: "Email sent: メッセージID").
    """
    msg = gmail_utils.create_email_message({
        "to": args["to"],                       # 送信先メールアドレス
        "subject": args["subject"],             # 件名
        "body": args["body"],                   # 本文
        "cc": args.get("cc"),                   # cc(任意)
        "bcc": args.get("bcc"),                 # bcc(任意)
        "in_reply_to": args.get("in_reply_to"), # 返信元のメッセージID(任意)
        "attachments": args.get("attachments"),  # 添付ファイル(任意)
    }).encode("utf-8")
    # メッセージをBase64でエンコード
    raw = base64.urlsafe_b64encode(msg).decode().rstrip("=")
    # payloadとは、メッセージのデータを含む辞書
    payload: Dict[str, Any] = {"raw": raw}
    # スレッドIDが指定されている場合は、スレッドIDを設定
    if "threadid" in args:
        payload["threadId"] = args["threadid"]
    # メッセージを送信
    resp = gmail_utils.service.users().messages().send(userId="me", body=payload).execute()
    return f"Email sent: {resp.get('id')}"


async def create_draft(args: Dict[str, Any]) -> str:
    """
    指定されたパラメータでメールの下書きを作成します。

    Args:
        args (Dict[str, Any]): 以下のキーを持つ辞書。
            - to (List[str]): 宛先アドレスリスト。
            - subject (str): 件名。
            - body (str): 本文。
            - cc (List[str], optional): CC先。
            - bcc (List[str], optional): BCC先。
            - in_reply_to (str, optional): 返信元ID。
            - threadid (str, optional): スレッドID。
            - attachments (List[str], optional): 添付ファイルのローカルパス（複数可、絶対パス推奨）。

    Returns:
        str: 下書き作成結果メッセージ (例: "Draft created: 下書きID").
    """
    msg = gmail_utils.create_email_message({
        "to": args["to"],
        "subject": args["subject"],
        "body": args["body"],
        "cc": args.get("cc"),
        "bcc": args.get("bcc"),
        "in_reply_to": args.get("in_reply_to"),
        "attachments": args.get("attachments"),
    }).encode("utf-8")
    raw = base64.urlsafe_b64encode(msg).decode().rstrip("=")
    # 下書きを作成
    draft = gmail_utils.service.users().drafts().create(
        userId="me", 
        body={"message": {"raw": raw, "threadId": args.get("threadid")}}
        ).execute()
    return f"Draft created: {draft.get('id')}"


async def read_email(args: Dict[str, Any]) -> str:
    """
    指定されたメッセージIDのメールを取得し、本文を抽出して返します。

    Args:
        args (Dict[str, Any]): 以下のキーを含む辞書。
            - messageid (str): 取得するメールのメッセージID。
            - htmlLimit (int, optional): HTML本文の最大文字数。デフォルトは10,000。
            - htmlOffset (int, optional): HTML本文の読み取り開始位置。デフォルトは0。

    Returns:
        str: 以下のキーを含むJSON形式の文字列。
            - text (str): プレーンテキストの本文。
            - html (str): HTML本文の一部（指定された範囲）。
            - truncated (bool): HTML本文が切り取られているかどうか。
            - nextOffset (int or None): 次の読み取り開始位置。全文が取得済みの場合はNone。
    """
    # メッセージを取得
    msg = gmail_utils.service.users().messages().get(userId="me", id=args["messageid"], format="full").execute()

    def extract_email_body(part: Dict[str, Any]) -> Tuple[str, str]:
        """メールの本文を取得する"""
        text, html = "", ""

        if "data" in part.get("body", {}):
            # メールの本文をBase64でURL-safeエンコードからUTF-8の文字列に変換
            content = decode_base64url(part["body"]["data"])
            if part.get("mimeType") == "text/plain": text = content
            elif part.get("mimeType") == "text/html": 
                # HTMLをパースして本文っぽい要素だけ残す
                soup = BeautifulSoup(content, "html.parser")
                main_texts = [p.get_text(strip=True) for p in soup.find_all(["p", "div"])]
                html = "\n".join(main_texts)

        for sub in part.get("parts", []):
            # メール本文はネストされてる可能性があるため、再帰的にメールの本文を取得
            t, h = extract_email_body(sub); text += t; html += h
        return text, html
    
    text, html = extract_email_body(msg["payload"])

    # クライアントから指定できるオプション
    limit = args.get("htmlLimit", 10_000)  # 1チャンクあたりの最大文字数
    offset = args.get("htmlOffset", 0)     # 何文字目から読み取るか

    # HTML部分を分割して返す
    html_chunks = html[offset: offset + limit] 
    truncated = len(html) > offset + limit

    return json.dumps({
        "text": text,
        "html": html_chunks,
        "truncated": truncated,  # 次チャンクがあるかどうか
        "nextOffset": offset + limit if truncated else None
    }, ensure_ascii=False)


async def search_emails(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gmail API でメールを検索し、ID とヘッダ情報をまとめて返す。

    Args:
        args:
            - query (str, optional): Gmail 検索クエリ (例: "is:unread newer_than:1d")
            - maxResults (int, optional): 最大取得件数 (デフォルト 10)
            - pageToken (str, optional): 次ページを取得するトークン

    Returns:
        Dict[str, Any]: {
            "messages": [
                {
                    "id": <メールID>,
                    "threadId": <スレッドID>,
                    "Subject": <件名>,
                    "From": <送信者>,
                    "Date": <日時>
                },
                ...
            ],
            "nextPageToken": <str>  # 次ページがなければ None
        }
    """
    service = gmail_utils.service

    # 引数の整形
    query = args.get("query", "")
    max_results = args.get("maxResults", 10)
    page_token = args.get("pageToken")

    # list API を叩く
    list_params = {"userId": "me", "maxResults": max_results}
    if query:
        list_params["q"] = query
    if page_token:
        list_params["pageToken"] = page_token

    resp = service.users().messages().list(**list_params).execute()
    ids = [m["id"] for m in resp.get("messages", [])]
    next_token = resp.get("nextPageToken")

    # メタデータだけ一括取得するバッチリクエスト
    results: List[Dict[str, Any]] = []
    if ids:
        batch = service.new_batch_http_request()
        def _collect(request_id, response, exception):
            if exception:
                # 個別失敗は飛ばす
                return
            hdrs = {h["name"]: h["value"] for h in response["payload"]["headers"]}
            results.append({
                "id": response["id"],
                "threadId": response.get("threadId"),
                "Subject": hdrs.get("Subject", ""),
                "From": hdrs.get("From", ""),
                "Date": hdrs.get("Date", ""),
            })

        for msg_id in ids:
            batch.add(
                service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"]
                ),
                callback=_collect
            )
        batch.execute()

    return {
        "messages": results,
        "nextPageToken": next_token
    }


async def delete_email(args: Dict[str, Any]) -> str:
    """
    指定メッセージIDのメールを削除します。

    Args:
        args (Dict[str, Any]):
            - messageid (str): 削除対象のメッセージID。

    Returns:
        str: 削除結果メッセージ (例"Email deleted: メッセージID").
    """
    gmail_utils.service.users().messages().delete(userId="me", id=args["messageid"]).execute()
    return f"Email deleted: {args['messageid']}"


# --- Tools: ラベル操作 ---
async def modify_label(args: Dict[str, Any]) -> str:
    """
    メッセージIDを受け取り該当のメールにラベルを追加または削除します。

    Args:
        args (Dict[str, Any]):
            - messageid (str): 対象メッセージID。
            - addLabelIds (List[str], optional): 追加するラベルIDリスト。
            - removeLabelIds (List[str], optional): 削除するラベルIDリスト。

    Returns:
        str: 操作結果メッセージ。
    """
    body: Dict[str, Any] = {}
    # 必要なパラメータだけ動的にbodyに追加
    if "addLabelIds" in args: body["addLabelIds"] = args["addLabelIds"]
    if "removeLabelIds" in args: body["removeLabelIds"] = args["removeLabelIds"]
    # bodyのキーを解析し、指定したラベルIDを追加・削除
    gmail_utils.service.users().messages().modify(
        userId="me",
        id=args["messageid"],
        body=body
    ).execute()
    return f"Label modified: {args['messageid']}"


async def create_label_tool(args: Dict[str, Any]) -> str:
    """
    新しいラベルを作成します。

    Args:
        args (Dict[str, Any]):
            - name (str): ラベル名。
            - messageListVisibility (str, optional): メール一覧表示設定。
            - labelListVisibility (str, optional): ラベル一覧表示設定。

    Returns:
        str: 作成結果メッセージ。
    """
    lbl = create_label(
        gmail_utils.service,
        args["name"],
        args.get("messageListVisibility", "show"),
        args.get("labelListVisibility", "labelShow")
    )
    return f"Label created: {lbl['id']}: {lbl['name']}"


async def delete_label_tool(args: Dict[str, Any]) -> str:
    """
    指定ラベルを削除します。

    Args:
        args (Dict[str, Any]):
            - name (str): 削除対象ラベル名。

    Returns:
        str: 削除結果メッセージ。
    """
    label = find_label_by_name(gmail_utils.service, args["name"])
    if not label:
        raise ValueError(f"Label '{args['name']}' not found")
    
    result = delete_label(gmail_utils.service, label.id)
    return result["message"]


async def list_labels_tool() -> str:
    """
    全ラベルの一覧を取得して文字列で返します。

    Args:
        なし

    Returns:
        str: ラベル名(ID)とタイプ一覧を改行区切りで返す。
    """
    lbls = list_labels(gmail_utils.service)
    lines = [f"{l['name']} (ID: {l['id']}), Type: {l['type']}" for l in lbls["all"]]
    return "\n".join(lines)


async def get_or_create_label_tool(args: Dict[str, Any]) -> str:
    """
    指定ラベルを取得または存在しなければ作成します。

    Args:
        args (Dict[str, Any]):
            - name (str): ラベル名。
            - messageListVisibility (str, optional)
            - labelListVisibility (str, optional)

    Returns:
        str: 準備完了メッセージ。
    """
    lbl = get_or_create_label(
        gmail_utils.service, args["name"],
        args.get("messageListVisibility", "show"),
        args.get("labelListVisibility", "labelShow")
    )
    return f"Label ready: {lbl.id}: {lbl.name}"


async def update_label_tool(args: Dict[str, Any]) -> str:
    """
    指定ラベルの設定を更新します。

    対象ラベルは名前で検索し、以下の属性を更新可能：
    - name: ラベルの表示名(必須)
    - messageListVisibility: メール一覧での表示設定 ("show" / "hide")
    - labelListVisibility: ラベル一覧での表示設定 ("labelShow" / "labelHide" / "labelShowIfUnread")
    - color: ラベルの色設定（textColor / backgroundColor を持つ dict）
        - 背景色（backgroundColor）: 
            #ac2b16, #cc3a21, #eaa041, #f2c960, #16a766, #43d692,
            #3c78d8, #4986e7, #8e63ce, #b99aff, #f691b2, #e07798,
            #616161, #a4c2f4, #d0bcf1, #fbc8d9, #f6c5be, #e4d7f5,
            #fad165, #fef1d1, #c6f3de, #a0eac9, #c9daf8, #b3efd3
        - 文字色（textColor）: 
            #ffffff, #000000

    Args:
        args (Dict[str, Any]):
            - name (str): 更新対象ラベル名（既存ラベルの名前）
            - updates (Dict[str, Any]): 更新内容（上記フィールドのいずれか）
    """
    # 1) ネストされている場合があるので一度ほどく
    params = args.get("args", args)

    # 2) 必須フィールドのチェック
    name = params.get("name")
    if not name:
        raise ValueError("Missing required argument: 'name'")

    label = find_label_by_name(gmail_utils.service, name)
    if not label:
        raise ValueError(f"Label '{name}' not found")
    label_id = label.id

    # 3) updates の取り出し
    raw_updates = params.get("updates")
    if not isinstance(raw_updates, dict):
        raise ValueError("Missing or invalid 'updates' argument")

    # 4) 許可するトップレベルキー
    allowed_top = {"name", "messageListVisibility", "labelListVisibility", "color"}
    allowed_backgrounds = {
        "#ac2b16","#cc3a21","#eaa041","#f2c960","#16a766","#43d692",
        "#3c78d8","#4986e7","#8e63ce","#b99aff","#f691b2","#e07798",
        "#616161","#a4c2f4","#d0bcf1","#fbc8d9","#f6c5be","#e4d7f5",
        "#fad165","#fef1d1","#c6f3de","#a0eac9","#c9daf8","#b3efd3"
    }
    allowed_texts = {"#ffffff", "#000000"}

    updates: Dict[str, Any] = {}
    for k, v in raw_updates.items():
        if k not in allowed_top:
            continue
        if k == "color":
            if not isinstance(v, dict):
                continue
            color_updates: Dict[str, str] = {}
            if "textColor" in v:
                if v["textColor"] not in allowed_texts:
                    raise ValueError(f"Invalid textColor: {v['textColor']}")
                color_updates["textColor"] = v["textColor"]
            if "backgroundColor" in v:
                if v["backgroundColor"] not in allowed_backgrounds:
                    raise ValueError(f"Invalid backgroundColor: {v['backgroundColor']}")
                color_updates["backgroundColor"] = v["backgroundColor"]
            if color_updates:
                updates["color"] = color_updates
        else:
            updates[k] = v

    if not updates:
        raise ValueError("No valid update fields provided")

    # 5) 実際に更新
    try:
        updated = update_label(gmail_utils.service, label_id, updates)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"update_label failed. updates={updates!r}, error={e!r}")

    name_display = updated.get("name") or label.name
    return f"Label updated: {updated.get('id', 'unknown')}: {name_display}"


async def find_label_by_name_tool(args: Dict[str, Any]) -> str:
    """
    名前で指定したラベルを取得します。

    Args:
        args (Dict[str, Any]):
            - name (str): 検索するラベル名。

    Returns:
        str: 検索結果メッセージ。
    """
    lbl = find_label_by_name(gmail_utils.service, args["name"])
    return f"Label found: {lbl.id}: {lbl.name}"