import re


def match_clean(string: str) -> str:
    """去除字符串中的所有空白/特殊字符"""
    return re.sub(r"\s+", "", string.strip())
