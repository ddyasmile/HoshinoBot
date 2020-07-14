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
    room_id: int = 0
    live_status: int = 0
    author: str = ''
    cover: str = ''
    title: str = ''

    def __eq__(self, other):
        return self.room_id == other.room_id


class BiliLiveSpider(abc.ABC):
    url = "https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id="
    
    @classmethod
    async def get_response(cls, rid: str) -> aiorequests.AsyncResponse:
        resp = await aiorequests.get(cls.url + rid)
        resp.raise_for_status()
        return resp

    @staticmethod
    async def get_item(resp: aiorequests.AsyncResponse) -> Item:
        content = await resp.json()
        if content["code"] == 0:
            item = Item(
                room_id=content["data"]["room_info"]["room_id"],
                live_status=content["data"]["room_info"]["live_status"],
                author=content["data"]["anchor_info"]["base_info"]["uname"],
                cover=content["data"]["room_info"]["cover"],
                title=content["data"]["room_info"]["title"]
            )
        return item

    @classmethod
    async def get_update(cls, rid: str, cache: Item):
        resp = await cls.get_response(rid)
        item = await cls.get_item(resp)
        if item:
            cache.room_id = item.room_id
            cache.live_status = item.live_status
            cache.author = item.author
            cache.cover = item.cover
            cache.title = item.title

    @classmethod
    async def check_rid(cls, rid: str) -> bool:
        resp = await cls.get_response(rid)
        content = await resp.json()
        return content["code"] == 0

