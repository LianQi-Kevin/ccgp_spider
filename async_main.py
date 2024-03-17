import asyncio
import logging
import random
import re

# import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup, SoupStrainer

from tools.logging_utils import log_set
from tools.tools import headers_list
from tools.tools import match_clean

# https://www.zmhttp.com/users_getapi/
PROXY_URL = ""
PRICE_DETAIL_API = "http://htgs.ccgp.gov.cn/GS8/contractpublish"

log_set(logging.DEBUG)


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


async def get_ccgp_detail(html_data: str) -> list:
    """获取详情页"""
    # 使用bs4实例化并过滤 class='main_list'
    soup = BeautifulSoup(html_data, "lxml", parse_only=SoupStrainer("div", attrs={"class": "main_list"}))
    lst_main = soup.find("ul", attrs={"class": "ulst"}).find_all("li")[1:]  # 去掉第一个元素

    # 遍历列表
    export = []
    for item in lst_main:
        export.append({
            'signing_date': match_clean(item.find('div').span.text),
            'contract_link': item.find('a')['href'],
            'contract_title': match_clean(item.find('a').text),
            'publish_date': match_clean(item.find_all('span')[1].text),
            'purchaser': match_clean(item.find_all('span')[2].text),
            'supplier': match_clean(item.find_all('span')[3].text),
        })
        logging.debug(f"Successfully get data: {export[-1]}")
    return export


async def get_ccgp_main(index: int = 1, proxy: str = None) -> str:
    """获取主页"""
    # response = requests.get(
    #     # url=f"{PRICE_DETAIL_API}/{'index' if index == 1 else f'index_{index}'}",
    #     url="https://www.baidu.com",
    #     headers=random.choice(headers_list),
    #     proxies={"http": proxy, "https": proxy},
    #     # proxies={"http": None, "https": None},
    # )
    # response.raise_for_status()
    # return response.text
    async with ClientSession(trust_env=False) as session:
        async with session.get(
                # url=f"{PRICE_DETAIL_API}/{'index' if index == 1 else f'index_{index}'}",
                url=f"https://www.baidu.com",
                headers=random.choice(headers_list),
                proxy=proxy,
        ) as response:
            # 记录响应状态码和头信息
            logging.debug(f"Response Status: {response.status}")
            logging.debug(f"Response Headers: {response.headers}")

            # 获取响应数据
            html_data = await response.text()
            logging.info(f"Successfully get html data, url: {response.url}, status: {response.status}")

            # 验证数据体
            response.raise_for_status()
            return html_data


async def task_main(semaphore: asyncio.Semaphore, index: int, queue: asyncio.Queue, proxy: str = None):
    async with semaphore:
        html_data = await get_ccgp_main(index=index, proxy=proxy)
        await queue.put(await get_ccgp_detail(html_data))


async def main():
    # 获取最大页数
    max_pages = await get_page_max(await get_ccgp_main(index=1, proxy="http://111.132.16.229:4253"))
    # logging.debug(f"max_pages: {max_pages}")
    # max_pages = 400

    # 创建队列
    # queue = asyncio.Queue()

    # 写入表头
    # csv_headers = list(single_response.list[0].model_dump(by_alias=True).keys())
    # writer_task = asyncio.create_task(write_csv(export_path=export_path, queue=queue, headers=csv_headers))

    # 创建异步任务
    # semaphore = asyncio.Semaphore(100)
    # for proxy in get_proxy(PROXY_URL):
    #     await task_main(semaphore, 1, queue, f"https://{proxy}")
    #     break
    # await task_main(semaphore, 1, queue, proxy)
    # tasks = []
    # for index, proxy in enumerate(get_proxy(PROXY_URL, https=False)):
    #     tasks.append(task_main(semaphore=semaphore, index=index, queue=queue, proxy=proxy))
    #
    # await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
