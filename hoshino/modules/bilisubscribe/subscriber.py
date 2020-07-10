import asyncio
import os
import random
import re
from collections import defaultdict
from functools import wraps
from typing import List, Dict

from hoshino import Service

try:
    import ujson as json
except:
    import json

svsubscriber = Service('subscriber-checker', bundle='Bilibili订阅', help_='管理各群Bilibili订阅条目', visible=False)

_loaded_subscriber: Dict[str, "Subscriber"] = {}
_re_legal_char = re.compile(r'[0-9]+')
_subscriber_config_dir = os.path.expanduser('~/.hoshino/subscriber_config/')
os.makedirs(_service_config_dir, exist_ok=True)

def _load_subscriber_config(mid):
    config_file = os.path.join(_subscriber_config_dir, f'{mid}.json')
    if not os.path.exists(config_file):
        return ()
    try:
        with open(config_file, encoding='utf8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        svsubscriber.logger.exception(e)
        return {}

def _save_subscriber_config(subscriber):
    config_file = os.path.join(_subscriber_config_dir, f'{subscriber.mid}.json')
    with open(config_file, 'w', encoding='utf8') as f:
        json.dump(
            {
                "mid": subscriber.mid,
                "subscribe_group": list(subscriber.subscribe_group)
            },
            f,
            ensure_ascii=False,
            indent=2
        )


class Subscriber:
    """为订阅UP主提供分群权限管理
    """

    def __init__(self, mid):
        assert _re_legal_char.match(mid).group(0).length() == len(mid)

        config = _load_subscriber_config(mid)
        self.mid = mid
        self.subscribe_group = set(config.get('subscribe_group', []))

        self.logger = svsubscriber.logger

        assert self.mid not in _loaded_subscriber, f'Subscriber "{self.mid}" already exist!'
        _loaded_subscriber[self.mid] = self

    @staticmethod
    def get_loaded_subscriber() -> Dict[str, "Subscriber"]:
        return _loaded_subscriber

    def add_subscription(self, group_id):
        self.subscribe_group.add(group_id)
        _save_subscriber_config(self)
        self.logger.info(f'Group {group_id} subscribes {self.mid}')

    def del_subscription(self, group_id):
        self.subscribe_group.discard(group_id)
        _save_subscriber_config(self)
        self.logger.info(f'Group {group_id} unsubscribes {self.mid}')

    def check_subscription(self, group_id):
        return bool(group_id in self.subscribe_group)

    def on_subscriber(self) -> Callable:
        def deco(func) -> Callable:
            @wraps(func)
            async def wrapper(bot, ev):
                if self.check_subscription(ev.group_id):
                    try:
                        return await func(bot, ev)
                    except Exception as e:
                        pass
                else:
                    self.logger.info(f'Group {ev.group_id} don\'t subscribe {self.mid}')
                return
            return wrapper
        return deco

    



