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
            hdrs = {
                h["name"].lower(): h["value"]
                for h in response.get("payload", {}).get("headers", [])
                if "name" in h and "value" in h
            }
            results.append({
                "id": response["id"],
                "threadId": response.get("threadId"),
                "Subject": hdrs.get("subject", ""),
                "From": hdrs.get("from", ""),
                "Date": hdrs.get("date", ""),
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

async def list_filters_tool() -> List[Dict[str, Any]]:
    """
    Gmailのフィルタ一覧を取得してリストで返します。

    Args:
        なし

    Returns: 
        フィルタIDと条件一覧を返す。
        List[
            Dict[str, Any]: {
                "filter_id": フィルタID,
                "criteria":
                    Dict[str, str]: {
                        "from": 送信元メールアドレス/ドメイン ORによる複数指定可,
                        "to": 宛先メールアドレス/ドメイン ORによる複数指定可,
                        "subject": 件名 ORによる複数指定可,
                        "query": 検索クエリ,
                        "negatedQuery": 否定検索クエリ,
                        "hasAttachment": 添付ファイルの有無
                    },
                "action": 
                    Dict[str, Any]: {
                        "addLabelIds": 追加するラベルIDのリスト,
                        "removeLabelIds": 削除するラベルIDのリスト,
                        "forward": 転送先メールアドレス
                    }
            }
        ]

    Note:
        addLabelIds / removeLabelIds に含まれるラベルIDに対応するラベル名を確認したい場合は、
        `list_labels` ツールを併用して名前とIDのマッピングを確認してください。
    """
    filters = gmail_utils.service.users().settings().filters().list(userId="me").execute()

    lines = []
    for f in filters.get("filter", []):
        criteria = remove_empty(f.get("criteria", {}))
        action = remove_empty(f.get("action", {}))

        item = {"filter_id": f.get("id", "")}
        if criteria:
            item["criteria"] = criteria
        if action:
            item["action"] = action
        lines.append(item)
    return lines


async def create_filter_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gmailフィルターを作成します。

    Args:
        args (Dict[str, Any]): 以下のキーを持つ辞書。
            - criteria (Dict[str, Any]): フィルター条件（各項目は省略可だが、いずれか1つ以上は指定が必要）。
                - from (str, 省略可): 送信元メールアドレス/ドメイン（ORによる複数指定可）。
                - to (str, 省略可): 宛先メールアドレス/ドメイン（ORによる複数指定可）。
                - subject (str, 省略可): 件名（ORによる複数指定可）。
                - query (str, 省略可): 検索クエリ。
                - negatedQuery (str, 省略可): 否定検索クエリ（除外条件）。
                - hasAttachment (bool, 省略可): 添付ファイルの有無。
                - excludeChats (bool, 省略可): チャットを除外するかどうか。
                - size (int, 省略可): メールサイズ（バイト単位）。
                - sizeComparison (str, 省略可): サイズ比較条件（"larger" または "smaller"）。
            - action (Dict[str, Any]): フィルター適用時の操作（各項目は省略可）。
                - addLabelIds (List[str], 省略可): 追加するラベルIDのリスト（例: ["STARRED", "IMPORTANT", "Label_123"]）。
                - removeLabelIds (List[str], 省略可): 削除するシステムラベルIDのリスト。
                    - 受信トレイをスキップ（アーカイブ）: ["INBOX"]
                    - 既読にする: ["UNREAD"]
                    - 迷惑メールにしない: ["SPAM"]
                    - ゴミ箱に直行: ["INBOX"] を削除し addLabelIds に ["TRASH"] を指定
                - forward (str, 省略可): 転送先メールアドレス。

    Note:
        - `addLabelIds` にカスタムラベル（自分で作成したラベル）を指定する場合、ラベル名ではなくラベルIDが必要です。事前に `list_labels` ツールでラベルIDを確認してください。

    Example:
        特定の送信元からのメールを受信トレイをスキップして既読にし、スターを付ける場合:
        {
            "criteria": {"from": "newsletter@example.com"},
            "action": {
                "removeLabelIds": ["INBOX", "UNREAD"],
                "addLabelIds": ["STARRED"]
            }
        }

    Returns:
        Dict[str, Any]: 作成されたフィルター情報（Gmail API の Filter オブジェクト）。
            - id (str): 作成されたフィルターの一意なID。
            - criteria (Dict[str, Any]): 設定されたフィルター条件。
            - action (Dict[str, Any]): 設定されたフィルター操作。
    """
    params = args.get("args", args)
    if not isinstance(params.get("criteria"), dict):
        raise ValueError("'criteria' must be a dictionary")
    if not isinstance(params.get("action"), dict):
        raise ValueError("'action' must be a dictionary")

    body = {
        "criteria": params["criteria"],
        "action": params["action"],
    }
    return gmail_utils.service.users().settings().filters().create(
        userId="me", body=body
    ).execute()


async def update_filter_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    既存のGmailフィルターを更新します。

    Gmail APIにはフィルター更新APIが存在しないため、既存フィルターを取得・マージした上で新規作成し、
    作成成功後に旧フィルターを削除する安全な方式で更新を行います。
    そのため、更新後はフィルターIDが新しくなります。

    Args:
        args (Dict[str, Any]): 以下のキーを持つ辞書。
            - filter_id (str): 更新対象のフィルターID（必須）。
            - criteria (Dict[str, Any], 省略可): 更新・追加するフィルター条件。
                - from (str, 省略可): 送信元メールアドレス/ドメイン（ORによる複数指定可）。
                - to (str, 省略可): 宛先メールアドレス/ドメイン（ORによる複数指定可）。
                - subject (str, 省略可): 件名（ORによる複数指定可）。
                - query (str, 省略可): 検索クエリ。
                - negatedQuery (str, 省略可): 否定検索クエリ（除外条件）。
                - hasAttachment (bool, 省略可): 添付ファイルの有無。
                - excludeChats (bool, 省略可): チャットを除外するかどうか。
                - size (int, 省略可): メールサイズ（バイト単位）。
                - sizeComparison (str, 省略可): サイズ比較条件（"larger" または "smaller"）。
            - action (Dict[str, Any], 省略可): 更新・追加するフィルター操作。
                - addLabelIds (List[str], 省略可): 追加するラベルIDのリスト（例: ["STARRED", "IMPORTANT", "Label_123"]）。
                - removeLabelIds (List[str], 省略可): 削除するシステムラベルIDのリスト。
                    - 受信トレイをスキップ（アーカイブ）: ["INBOX"]
                    - 既読にする: ["UNREAD"]
                    - 迷惑メールにしない: ["SPAM"]
                    - ゴミ箱に直行: ["INBOX"] を削除し addLabelIds に ["TRASH"] を指定
                - forward (str, 省略可): 転送先メールアドレス。

    Note:
        - `criteria` または `action` のいずれか1つ以上の指定が必要です。指定されなかったフィールドは既存の設定が引き継がれます。
        - 既存の項目を削除したい場合は、値に空文字 "" や None を指定してください。
        - `addLabelIds` にカスタムラベルを指定する場合、ラベル名ではなくラベルIDが必要です。事前に `list_labels_tool` でラベルIDを確認してください。

    Example:
        フィルターID "AN9n_v... " のアクションにスター追加を指定し、件名条件を更新する場合:
        {
            "filter_id": "AN9n_v...",
            "criteria": {"subject": "[重要] 新着通知"},
            "action": {
                "addLabelIds": ["STARRED"]
            }
        }

    Returns:
        Dict[str, Any]: 新しく作成されたフィルター情報（Gmail API の Filter オブジェクト）。
            - id (str): 新しく割り当てられたフィルターID。
            - previous_filter_id (str): 更新前の旧フィルターID。
            - criteria (Dict[str, Any]): 設定されたフィルター条件。
            - action (Dict[str, Any]): 設定されたフィルター操作。
    """
    params = args.get("args", args)
    filter_id = params.get("filter_id")
    if not filter_id:
        raise ValueError("'filter_id' is required")

    new_criteria = params.get("criteria")
    new_action = params.get("action")

    if new_criteria is None and new_action is None:
        raise ValueError("At least one of 'criteria' or 'action' must be provided for update")

    if new_criteria is not None and not isinstance(new_criteria, dict):
        raise ValueError("'criteria' must be a dictionary if provided")
    if new_action is not None and not isinstance(new_action, dict):
        raise ValueError("'action' must be a dictionary if provided")

    service = gmail_utils.service

    # 1. 既存フィルターの取得
    try:
        existing = service.users().settings().filters().get(userId="me", id=filter_id).execute()
    except Exception as e:
        raise ValueError(f"Failed to retrieve filter with ID '{filter_id}': {e}")

    merged_criteria = existing.get("criteria", {}).copy()
    if new_criteria is not None:
        merged_criteria.update(new_criteria)
    merged_criteria = remove_empty(merged_criteria)

    merged_action = existing.get("action", {}).copy()
    if new_action is not None:
        merged_action.update(new_action)
    merged_action = remove_empty(merged_action)

    if not merged_criteria:
        raise ValueError("Updated filter criteria cannot be empty")
    if not merged_action:
        raise ValueError("Updated filter action cannot be empty")

    body = {
        "criteria": merged_criteria,
        "action": merged_action,
    }

    # 2. 新フィルターの作成
    created = service.users().settings().filters().create(
        userId="me", body=body
    ).execute()

    # 3. 旧フィルターの削除
    try:
        service.users().settings().filters().delete(
            userId="me", id=filter_id
        ).execute()
    except Exception as e:
        created["previous_filter_id"] = filter_id
        created["warning"] = f"New filter created, but failed to delete previous filter '{filter_id}': {e}"
        return created

    created["previous_filter_id"] = filter_id
    return created


async def delete_filter_tool(args: Dict[str, Any]) -> str:
    """
    Gmailフィルターを削除します。

    Args:
        args (Dict[str, Any]):
            - filter_id (str): 削除対象のフィルターID。

    Returns:
        str: 削除結果メッセージ。
    """
    params = args.get("args", args)
    filter_id = params.get("filter_id")
    if not filter_id:
        raise ValueError("'filter_id' is required")

    gmail_utils.service.users().settings().filters().delete(
        userId="me", id=filter_id
    ).execute()
    return f"Filter deleted: {filter_id}"

def remove_empty(data: dict) -> dict:
    """
    値が存在するもの（空文字 ""、空リスト []、None などを除外）のみ抽出
    Args:
        data (dict): 入力の辞書

    Returns:
        dict: 値が存在する項目のみを含む辞書
    """
    return {k: v for k, v in data.items() if v is not None and v != "" and v != []}