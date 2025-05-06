from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError


@dataclass
class LabelColor:
    """
    Gmail ラベルの色設定を表すデータクラス。

    Attributes:
        textColor: ラベル名の文字色 (CSS カラーコード)
        backgroundColor: ラベル背景色 (CSS カラーコード)
    """
    textColor: Optional[str] = None
    backgroundColor: Optional[str] = None


@dataclass
class GmailLabel:
    """
    Gmail API の Label オブジェクトに対応したデータクラス。

    Attributes:
        id: ラベルの一意 ID
        name: ラベル名
        type: システム or ユーザー定義
        messageListVisibility: メッセージ一覧における表示設定
        labelListVisibility: ラベル一覧における表示設定
        messagesTotal: 総メッセージ数
        messagesUnread: 未読メッセージ数
        color: ラベル色設定
    """
    id: str
    name: str
    type: Optional[str] = None
    messageListVisibility: Optional[str] = None
    labelListVisibility: Optional[str] = None
    messagesTotal: Optional[int] = None
    messagesUnread: Optional[int] = None
    color: Optional[LabelColor] = None


def create_label(service: Resource,
                 label_name: str,
                 message_list_visibility: str = "show",
                 label_list_visibility: str = "labelshow") -> Dict[str, Any]:
    """
    指定されたラベル名で新しいラベルを作成する

    Args:
        service: Google APIのResourceオブジェクト
        label_name: 作成するラベルの名前
        message_list_visibility: ラベルの表示設定
        label_list_visibility: ラベルリストの表示設定

    Returns:
        Dict[str, Any]: 作成されたラベルの情報
    """
    body = {
        "name": label_name,
        "messageListVisibility": message_list_visibility,
        "labelListVisibility": label_list_visibility,
    }

    try:
        label = service.users().labels().create(userId="me", body=body).execute()
        return label
    except HttpError as error:
        msg = getattr(error, "error_details", str(error))
        if "already exists" in msg:
            raise ValueError(f"Label '{label_name}' already exists")
        raise ValueError(f"Failed to create label: {msg}")
    

def update_label(service: Resource,
                 label_id: str,
                 updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    指定されたラベルの属性を更新する

    Args:
        service: Google APIのResourceオブジェクト
        label_id: 更新するラベルのID
        updates: 更新する属性のディクショナリ

    Returns:
        Dict[str, Any]: 更新されたラベルの情報
    """
    try:
        # パスパラメータとして渡すキーは id
        service.users().labels().get(userId="me", id=label_id).execute()
        response = service.users().labels().update(
            userId="me", id=label_id, body=updates
        ).execute()
        return response
    except HttpError as error:
        if error.status_code == 404:
            raise ValueError(f"Label with ID '{label_id}' not found")
        raise ValueError(f"Failed to update label: {error}")
    


def delete_label(service: Resource, label_id: str) -> Dict[str, Any]:
    """
    指定されたラベルを削除する(システムラベルは削除不可)

    Args:
        service: Google APIのResourceオブジェクト
        label_id: 削除するラベルのID

    Returns:
        Dict[str, Any]: 削除されたラベルの情報
    """
    try:
        data = service.users().labels().get(userId="me", id=label_id).execute()
        if data.get("type") == "system":
            raise ValueError(f"Cannot delete system label '{label_id}'")
        service.users().labels().delete(userId="me", id=label_id).execute()
        return {"success": True, "message": f"Label '{data.get('name')}' deleted successfully"}
    except HttpError as error:
        if error.status_code == 404:
            raise ValueError(f"Label with ID '{label_id}' not found")
        raise ValueError(f"Failed to delete label: {error}")
    

def list_labels(service: Resource) -> Dict[str, Any]:
    """
    全ラベルを取得し、システム/ユーザーラベルを分類して返す

    Args:
        service: Google APIのResourceオブジェクト

    Returns:
        Dict[str, Any]: ラベルのリスト
    """
    try: 
        resp = service.users().labels().list(userId="me").execute()
        labels = resp.get("labels", [])
        system = [lbl for lbl in labels if lbl.get("type") == "system"]
        user = [lbl for lbl in labels if lbl.get("type") == "user"]
        return {
            "all": labels,
            "system": system,
            "user": user,
            "count": {
                "total": len(labels),
                "system": len(system),
                "user": len(user),
            },
        }
    except HttpError as error:
        raise ValueError(f"Failed to list labels: {error}")
    

def find_label_by_name(service: Resource, label_name: str) -> Optional[GmailLabel]:
    """
    名前でラベルを検索し、見つかればそのラベルのGmailLabelインスタンスを返す(大文字小文字の区別はしない)
    見つからない場合はNoneを返す

    Args:
        service: Google APIのResourceオブジェクト
        label_name: 検索するラベルの名前

    Returns:
        Optional[GmailLabel]: 見つかったラベルのインスタンス、見つからない場合はNone
    """
    raw = list_labels(service)["all"]
    for data in raw:
        if data.get("name", "").lower() == label_name.lower():
            color_data = data.get("color", {})
            color = LabelColor(
                textColor=color_data.get("textColor"),
                backgroundColor=color_data.get("backgroundColor"),
            ) if color_data else None
            return GmailLabel(
                id=data.get("id"),
                name=data["name"],
                type=data.get("type"),
                messageListVisibility=data.get("messageListVisibility"),
                labelListVisibility=data.get("labelListVisibility"),
                messagesTotal=data.get("messagesTotal"),
                messagesUnread=data.get("messagesUnread"),
                color=color,
            )
    return None


def get_or_create_label(service: Resource,
                        label_name: str,
                        message_list_visibility: str = "show",
                        label_list_visibility: str = "labelshow" ) -> GmailLabel:
    """
    指定されたラベル名で新しいラベルを作成する
    すでに存在する場合はそのラベルを返す
    
    Args:
        service: Google APIのResourceオブジェクト
        label_name: ラベルの名前
        message_list_visibility: ラベルの表示設定
        label_list_visibility: ラベルリストの表示設定

    Returns:
        GmailLabel: ラベルのインスタンス
    """
    existing = find_label_by_name(service, label_name)
    if existing:
        return existing
    raw = create_label(service, label_name, message_list_visibility, label_list_visibility)
    # create_label の戻り値が dict なので GmailLabel に変換
    color_data = raw.get("color", {})
    color = LabelColor(
        textColor=color_data.get("textColor"),
        backgroundColor=color_data.get("backgroundColor"),
    ) if color_data else None
    return GmailLabel(
        id=raw.get("id"),
        name=raw.get("name"),
        type=raw.get("type"),
        messageListVisibility=raw.get("messageListVisibility"),
        labelListVisibility=raw.get("labelListVisibility"),
        messagesTotal=raw.get("messagesTotal"),
        messagesUnread=raw.get("messagesUnread"),
        color=color,
    )
