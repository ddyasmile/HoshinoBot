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

_subscriber_config_dir = os.path.expanduser('~/.hoshino/subscriber_config/')
os.makedirs(_service_config_dir, exist_ok=True)

def _load_subscriber_config(mid):
    config_file = os.path.join(_subscriber_config_dir, 'config.json')
    if not os.path.exists(config_file):
        return {}
    try:
        with open(config_file, encoding='utf8') as f:
            config = json.load(f)
            return config
    except Exception as e:
        svsubscriber.logger.exception(e)
        return {}

def _save_subscriber_config(subscriber):
    config_file = os.path.join(_subscriber_config_dir, 'config.json')
    with open(config_file, 'w', encoding='utf8') as f:
        json.dump(
            subscriber.config,
            f,
            ensure_ascii=False,
            indent=2
        )


class Subscriber:
    """为订阅UP主提供分群权限管理
    """
    def __init__(self):
        self.config: Dict[str, set()] = _load_subscriber_config(mid)

    def add_subscription(self, mid, group_id):
        set(self.config[mid]).add(group_id)
        _save_subscriber_config(self)

    def del_subscription(self, mid, group_id):
        set(self.config[mid]).discard(group_id)
        _save_subscriber_config(self)

    def search_subscription(self, group_id):
        mid_list = []
        for mid, glist in self.config:
            if group_id in glist:
                mid_list.append(mid)
        return mid_list

    def check_subscription(self, mid, group_id):
        return bool(group_id in self.config[mid])

    def get_mids(self):
        return self.config.keys()

    def get_groups(self, mid):
        return list(config[mid])


    



