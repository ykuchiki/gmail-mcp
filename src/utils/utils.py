import base64

def decode_base64url(data: str) -> str:
    """
    Base64URL形式の文字列をUTF-8の文字列に変換する

    Gmail API や JWT などが返す Base64URL 形式では、
    パディング用の「=」が省略されていることが多い。
    この関数では、元のBase64文字列の長さを調整するために
    不足している「=」を自動的に追加し、安全にデコードを行う。

    Args:
        data (str): パディングの省略されたBase64URL形式の文字列

    Returns:
        str: UTF-8でデコードされた文字列（メール本文など）

    Raises:
        UnicodeDecodeError: デコード結果がUTF-8として不正な場合
        binascii.Error: 入力がBase64として不正な場合
    """
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8")