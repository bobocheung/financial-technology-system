def normalize_hk_symbol(user_input: str) -> str:
    """
    將使用者輸入的港股代碼標準化為 Yahoo Finance 代碼：四位數 + .HK

    支援輸入形式："700"、"0700"、"0700.HK"、"700.HK"（不分大小寫）。
    """
    if not user_input:
        raise ValueError("symbol 不可為空")

    s = user_input.strip().upper()
    if s.endswith(".HK"):
        s = s[:-3]

    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) == 0 or len(digits) > 5:
        raise ValueError(f"無效的港股代碼輸入：{user_input}")

    # Yahoo Finance 港股常見為四位數，如 0700.HK
    digits = digits.zfill(4)
    return f"{digits}.HK"


__all__ = ["normalize_hk_symbol"]
