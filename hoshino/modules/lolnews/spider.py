"""
This is a spider that inquires LOL news from LOL offical website.
"""

import abc
from dataclasses import dataclass
from typing import List, Union

from bs4 import BeautifulSoup
from hoshino import aiorequests

try:
    import ujson as json
except:
    import json

@dataclass
class Item:
    idx: Union[str, int]
    content: str = ""

    def __eq__(self, other):
        return self.idx == other.idx


class BaseSpider(abc.ABC):
    url = None
    src_name = None
    idx_cache = set()
    item_cache = []

    @classmethod
    async def get_response(cls) -> aiorequests.AsyncResponse:
        resp = await aiorequests.get(cls.url)
        resp.raise_for_status()
        return resp

    @staticmethod
    @abc.abstractmethod
    async def get_items(resp: aiorequests.AsyncResponse) -> List[Item]:
        raise NotImplementedError

    @classmethod
    async def get_update(cls) -> List[Item]:
        resp = await cls.get_response()
        items = await cls.get_items(resp)
        updates = [ i for i in items if i.idx not in cls.idx_cache ]
        if updates:
            cls.idx_cache = set(i.idx for i in items)
            cls.item_cache = items
        return updates

    @classmethod
    def format_items(cls, items) -> str:
        return f'{cls.src_name}新闻\n' + '\n'.join(map(lambda i: i.content, items))



class LOLSpider(BaseSpider):
    url = "https://apps.game.qq.com/cmc/zmMcnTargetContentList?r0=jsonp&page=1&num=10&target=23&source=web_pc"
    src_name = "LOL官网"

    @staticmethod
    async def get_items(resp: aiorequests.AsyncResponse):
        contents = await (resp.text)
        contentStr = contents[9:-2]
        contentDir = json.loads(contentStr)

        items = []
        for content in contentDir["data"]["result"]:
            if content["authorID"]:
                index = content["iDocID"]
                title = content["sTitle"]
                url = ""
                if content["sRedirectURL"]:
                    url = content["sRedirectURL"]
                elif content["sUrl"]:
                    url = content["sUrl"]
                else:
                    url = f'https://lol.qq.com/news/detail.shtml?docid={index}'
                items.append(Item(idx=index, content=f'{title}\n▲{url}'))

        return items