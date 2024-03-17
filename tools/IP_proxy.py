import logging
from typing import Optional, List

import requests
from pydantic import BaseModel, Field


class LetecsProxys(BaseModel):
    ip: str = Field(title="IP地址")
    port: int = Field(title="端口")
    expire_time: Optional[str] = Field(default=None, title="过期时间")
    city: Optional[str] = Field(default=None, title="城市")
    isp: Optional[str] = Field(default=None, title="运营商")
    outip: Optional[str] = Field(default=None, title="出口IP")


class LetecsProxysResponse(BaseModel):
    code: int
    data: List[LetecsProxys]
    msg: Optional[str] = None
    success: Optional[bool] = None


def get_proxy(url: str) -> str:
    """
    This function is used to get a proxy from a given URL.

    Parameters:
    url (str): The URL from where to fetch the proxy.
    https (bool): A flag to indicate if the proxy should be https or http. Default is True (https).

    Returns:
    str: A string representation of the proxy in the format 'http(s)://ip:port'.
    """
    response = requests.get(url)
    response.raise_for_status()
    response = LetecsProxysResponse(**response.json())
    if response.success:
        print(len(response.data))
        for proxy_ in response.data:
            logging.debug(f"Successfully get proxy: {proxy_}")
            yield f"{proxy_.ip}:{proxy_.port}"
