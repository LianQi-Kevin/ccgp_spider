import asyncio
import csv
import logging
import os
import random
import re
from typing import List

import aiofiles
from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup, SoupStrainer, Tag, NavigableString

from tools.logging_utils import log_set
from tools.pydantic_types import ContractModel, ConversionOldContractModel, MainContractModel
from tools.tools import headers_list, clean_contents, match_info, get_fileid, flatten_dict
from tools.tools import match_clean

PRICE_DETAIL_API = "http://htgs.ccgp.gov.cn/GS8/contractpublish"

log_set(logging.INFO, True, "ccgp.log")


async def write_csv(export_path: str, queue, headers: List[str] = None, flush_every: int = 400):
    async with aiofiles.open(export_path, mode='w', encoding='utf-8', newline='') as file:
        logging.debug(f"Event loop: {asyncio.get_running_loop()}")
        writer = None
        item_index = 0

        while True:
            if writer is None:
                # 首次写入，创建writer并写入表头
                writer = csv.DictWriter(file, fieldnames=headers)
                await writer.writeheader()

            data = await queue.get()
            if data is None:
                # None作为结束信号
                break
            await writer.writerow(data)
            item_index += 1
            queue.task_done()

            if item_index % flush_every == 0:
                await file.flush()
                os.fsync(file.fileno())


async def parse_contract(_html_content: str) -> ContractModel:
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(_html_content, 'lxml', parse_only=SoupStrainer("div", attrs={"class": "vT_detail_main"}))

    result_lst = []

    if soup.find("div", attrs={"class": "content_2020"}):
        for tag in soup.find("div", attrs={"class": "content_2020"}).contents:
            if isinstance(tag, Tag):
                # 过滤空内容
                tag_text = match_clean(tag.text)
                if tag_text == "" or "免责声明" in tag_text:
                    continue
                tag_contents = clean_contents(tag.contents)
                if isinstance(tag_contents[0], NavigableString):
                    # 取得上一位主键
                    target = result_lst[-1]
                    if isinstance(target["value"], dict):
                        matched = match_info(match_clean(tag.text))
                        if matched["key"] != "本合同对应的中标成交公告":
                            if matched["key"] != "附件":
                                if matched["key"] not in target["value"].keys():
                                    target["value"][matched["key"]] = matched["value"]
                                else:
                                    target["value"][f"{matched['key']}_2"] = matched["value"]
                            else:
                                result_lst.append(matched)
                        logging.debug(f"p_tag: {matched}", )
                elif isinstance(tag_contents[0], Tag):
                    # 主健
                    if tag.name == "p":
                        # 主键
                        try:
                            matched = match_info(match_clean(tag.strong.text))
                            result_lst.append(matched)
                            logging.debug(matched)
                        except Exception as e:
                            logging.error(f"Failed to match_info: {e}")
                    elif tag.name == "ul":
                        # 文件下载
                        li_body = tag.find("li", attrs={"class": "fileInfo"})
                        cleaned_contents = clean_contents(li_body.contents)
                        if len(cleaned_contents) == 1:
                            # 直接提取文件名和 href
                            filename = li_body.find("a").text
                            href = li_body.find("a")["href"]
                        else:
                            # 提取文件名和 href
                            filename = match_clean(cleaned_contents[0].text)
                            href = get_fileid(li_body.find("a")["onclick"])
                            if href:
                                href = f"https://download.ccgp.gov.cn/oss/download?uuid={href}"
                        target = result_lst[-1]
                        if isinstance(target["value"], dict):
                            target["value"]["filename"] = filename
                            target["value"]["href"] = href
                        logging.debug(f"filename: {filename}, href: {href}")

        # 使用key和value构建字典
        export_dict = {item["key"]: item["value"] for item in result_lst}
        export_dict["中标合同"] = export_dict.pop("其他补充事宜")  # 重命名

        # 展平字典
        try:
            contract_dict = ContractModel(**flatten_dict(export_dict))
            logging.debug(contract_dict)
            return contract_dict
        except Exception as e:
            logging.error(f"Failed to parse contract: {e}")
            return ContractModel()

    elif soup.find("table", attrs={"id": "queryTable"}):
        # 旧版
        for tr in soup.find("table", attrs={"id": "queryTable"}).find_all("tr"):
            matched_info = match_info(match_clean(tr.text))
            if "免责声明" not in matched_info["key"]:
                if matched_info["key"] not in ["中标、成交公告", "合同附件"]:
                    result_lst.append(matched_info)
                    logging.debug(f"matched_info: {matched_info}")
                if tr.find("li", attrs={"class": "fileInfo"}):
                    # 文件下载
                    li_body = tr.find("li", attrs={"class": "fileInfo"})
                    cleaned_contents = clean_contents(li_body.contents)
                    if len(cleaned_contents) == 1:
                        # 直接提取文件名和 href
                        filename = li_body.find("a").text
                        href = li_body.find("a")["href"]
                    else:
                        # 提取文件名和 href
                        filename = match_clean(cleaned_contents[0].text)
                        href = get_fileid(li_body.find("a")["onclick"])
                        if href:
                            href = f"https://download.ccgp.gov.cn/oss/download?uuid={href}"
                    if matched_info["key"] == "中标、成交公告":
                        result_lst.append({"key": "中标、成交公告", "value": {"filename": filename, "href": href}})
                    else:
                        result_lst.append({"key": "合同附件", "value": {"filename": filename, "href": href}})
                    logging.debug(f"key: {matched_info['key']}, filename: {filename}, href: {href}")

        # 使用key和value构建字典
        export_dict = {item["key"]: item["value"] for item in result_lst}
        # 展平字典
        export_dict = flatten_dict(export_dict)
        try:
            contract_dict = ConversionOldContractModel(**flatten_dict(export_dict))
            logging.debug(contract_dict)
            return contract_dict
        except Exception as e:
            logging.error(f"Failed to parse contract: {e}")
            return ContractModel()


async def get_subPage(url: str):
    async with ClientSession(trust_env=False) as session:
        # 异步delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        async with session.get(
                url=url,
                headers=random.choice(headers_list),
                proxy=None,
        ) as response:
            response.raise_for_status()
            # 记录响应状态码和头信息
            logging.debug(f"Response Status: {response.status}")
            logging.debug(f"Response Headers: {response.headers}")

            # 获取响应数据
            html_data = await response.text()
            logging.info(f"Successfully get sub html data, url: {response.url}, status: {response.status}")

            return html_data


async def get_page_max(html_data: str) -> int:
    """获取最大页数"""
    # 使用bs4实例化并过滤 class='pagigation'
    soup = BeautifulSoup(html_data, "lxml", parse_only=SoupStrainer("div", attrs={"class": "pagigation"}))
    # 使用正则获取分页最大值
    match = re.search(r"size:(\d+),", soup.find("p", attrs={"class": "pager"}).find_all("script")[1].text)
    if match:
        return int(match.group(1))
    else:
        logging.error("Failed to get page max value.")
        return 0


async def get_ccgp_detail(html_data: str, queue: asyncio.Queue) -> None:
    """获取详情页"""
    # 使用bs4实例化并过滤 class='main_list'
    soup = BeautifulSoup(html_data, "lxml", parse_only=SoupStrainer("div", attrs={"class": "main_list"}))
    lst_main = soup.find("ul", attrs={"class": "ulst"}).find_all("li")[1:]  # 去掉第一个元素

    async def fetch_detail(item):
        base_data = {
            'signing_date': match_clean(item.find('div').span.text),
            'contract_URL': f"{PRICE_DETAIL_API}/{item.find('a')['href']}",
            'contract_title': match_clean(item.find('a').text),
        }

        # 组装子URL
        logging.debug(f"sub_url: {base_data['contract_URL']}")
        sub_html_data = await get_subPage(base_data['contract_URL'])
        subpage_info = await parse_contract(sub_html_data)

        # 将处理好的数据放入队列
        write_data = {**base_data, **subpage_info.model_dump()}
        await queue.put(write_data)

    tasks = [fetch_detail(item) for item in lst_main]
    await asyncio.gather(*tasks)


async def get_ccgp_main(index: int = 1) -> str:
    """获取主页"""
    async with ClientSession(trust_env=False) as session:
        async with session.get(
                url=f"{PRICE_DETAIL_API}/{'index' if index == 1 else f'index_{index}'}",
                # url=f"http://ip-api.com/json",
                headers=random.choice(headers_list),
                proxy=None,
        ) as response:
            response.raise_for_status()
            # 记录响应状态码和头信息
            logging.debug(f"Response Status: {response.status}")
            logging.debug(f"Response Headers: {response.headers}")

            # 获取响应数据
            html_data = await response.text()
            logging.info(f"Successfully get main html data, url: {response.url}, status: {response.status}")

            return html_data


async def task_main(queue: asyncio.Queue, semaphore: asyncio.Semaphore = asyncio.Semaphore(10),  index: int = 1,
                    delay: float = random.uniform(1.0, 3.0), retry_count: int = 10):
    if retry_count <= 0:
        logging.error("Maximum retry attempts reached. Failed to Get XinFaDi Price Detail.")
        # raise RuntimeError("Failed to Get XinFaDi Price Detail.")
    try:
        async with semaphore:
            # 异步delay
            await asyncio.sleep(delay)
            await get_ccgp_detail(html_data=await get_ccgp_main(index=index), queue=queue)

    except ClientError as e:
        logging.warning(f"aiohttp request error, retry count: {retry_count}, error: {e}")
        await asyncio.sleep(3)
        return await task_main(queue, semaphore, index, delay, retry_count - 1)
    except Exception as e:
        logging.warning(f"Get XinFaDi Price Detail failed, retry count: {retry_count}, error: {e}")
        await asyncio.sleep(3)
        return await task_main(queue, semaphore, index, delay, retry_count - 1)


async def main(export_path: str = "ccgp.csv"):
    # 获取最大页数
    # await get_ccgp_main(index=1)
    # max_pages = await get_page_max(await get_ccgp_main(index=1))
    # logging.debug(f"max_pages: {max_pages}")

    max_pages = 1

    # 创建队列
    queue = asyncio.Queue()

    # 写入表头
    csv_headers = list(MainContractModel().model_dump().keys())
    writer_task = asyncio.create_task(write_csv(export_path=export_path, queue=queue, headers=csv_headers))

    # 创建异步任务
    semaphore = asyncio.Semaphore(100)
    tasks = [
        task_main(queue=queue, semaphore=semaphore, index=index, delay=random.uniform(1.0, 5.0), retry_count=15)
        for index in range(1, max_pages + 1)
    ]

    await asyncio.gather(*tasks)

    await queue.put(None)  # 发送None结束写入任务
    await writer_task


if __name__ == '__main__':
    asyncio.run(main())
