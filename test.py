import logging
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup, SoupStrainer, NavigableString, Tag
from pydantic import BaseModel, Field

from tools.tools import match_clean
from tools.logging_utils import log_set
from tools.pydantic_types import ContractAnnouncementDetails, ContractMainInfo, ContractMainSubject


log_set(logging.DEBUG)


def match_info(string: str):
    match = re.match(r"^(?:.*?[,、])?(?P<key>.*?)[：:]\s*(?P<value>.*)?$", string)
    if match:
        logging.debug(f"match_dict: {match.groupdict()}")


def parse_contract(_html_content: str):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(_html_content, 'lxml', parse_only=SoupStrainer("div", attrs={"class": "content_2020"}))

    for tag in soup.find('div').contents:
        if isinstance(tag, Tag):
            if tag.find('strong'):
                cleaned_strong = match_clean(tag.strong.text)
                logging.info(f"strong_tag: {cleaned_strong}, match_info: {match_info(cleaned_strong)}")
            else:
                cleaned_p = match_clean(tag.text)
                logging.info(f"p_tag: {cleaned_p}, match_info: {match_info(cleaned_p)}")


if __name__ == '__main__':
    html_content = requests.get(
        url="http://htgs.ccgp.gov.cn/GS8/contractpublish/detail/E0FE725596E64E07BD5CDB6E135982D3?contractSign=0#").text

    # 解析 HTML 内容
    parse_contract(html_content)
