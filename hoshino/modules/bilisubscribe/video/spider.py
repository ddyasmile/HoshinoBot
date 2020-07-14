"""
This is a spider that inquires Bilibili videos from www.bilibili.com.
"""

import abc
from dataclasses import dataclass, field
from typing import List, Union, Set

from bs4 import BeautifulSoup
from hoshino import aiorequests

@dataclass
class Item:
    bvid: str
    author: str
    cover: str
    title: str

    def __eq__(self, other):
        return self.bvid == other.bvid


@dataclass
class ItemsCache:
    bvid_cache: Set[str] = field(default_factory=set)
    item_cache: List[Item] = field(default_factory=list)


class BiliVideoSpider(abc.ABC):
    url1 = "https://api.bilibili.com/x/space/arc/search?mid="
    url2 = "&ps=20&tid=0&pn=1&keyword=&order=pubdate&jsonp=jsonp"
    
    @classmethod
    async def get_response(cls, mid: str) -> aiorequests.AsyncResponse:
        resp = await aiorequests.get(cls.url1 + mid + cls.url2)
        resp.raise_for_status()
        return resp

    @staticmethod
    async def get_items(resp: aiorequests.AsyncResponse) -> List[Item]:
        content = await resp.json()
        if content["code"] == 0:
            items = [
                Item(
                    bvid=n["bvid"],
                    author=n["author"],
                    cover=f'https:{n["pic"]}',
                    title=n["title"]
                ) for n in content["data"]["list"]["vlist"]
            ]
        return items

    @classmethod
    async def get_update(cls, mid: str, cache: ItemsCache) -> List[Item]:
        resp = await cls.get_response(mid)
        items = await cls.get_items(resp)
        updates = [ i for i in items if i.bvid not in cache.bvid_cache ]
        if updates:
            cache.bvid_cache = set(i.bvid for i in items)
            cache.item_cache = items
        return updates

    @classmethod
    async def check_mid(cls, mid: str) -> bool:
        resp = await cls.get_response(mid)
        content = await resp.json()
        return content["code"] == 0




