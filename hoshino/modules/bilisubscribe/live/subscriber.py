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
os.makedirs(_subscriber_config_dir, exist_ok=True)

def _load_subscriber_config():
    config_file = os.path.join(_subscriber_config_dir, 'live.json')
    if not os.path.exists(config_file):
        return {}
    try:
        with open(config_file, encoding='utf8') as f:
            config = json.load(f)
            config = json.loads(config)
            return config
    except Exception as e:
        return {}

def _save_subscriber_config(subscriber):
    config_file = os.path.join(_subscriber_config_dir, 'live.json')
    with open(config_file, 'w', encoding='utf8') as f:
        json.dump(
            json.dumps(subscriber.config),
            f,
            ensure_ascii=False,
            indent=2
        )

class Subscriber:
    """为订阅直播间提供分群权限管理
    """
    def __init__(self):
        self.config: Dict[str, list()] = _load_subscriber_config()

    def add_subscription(self, rid, group_id):
        if rid not in self.config:
            self.config[rid] = list()
        if group_id not in self.config[rid]:
            self.config[rid].append(group_id)
            _save_subscriber_config(self)

    def del_subscription(self, rid, group_id):
        if rid not in self.config:
            return
        if group_id in self.config[rid]:
            self.config[rid].remove(group_id)
            _save_subscriber_config(self)
    def search_subscription(self, group_id):
        rid_list = []
        for rid in self.config:
            if group_id in self.config[rid]:
                rid_list.append(rid)
        return rid_list

    def check_subscription(self, rid, group_id):
        return bool(group_id in self.config[rid])

    def get_rids(self):
        return self.config.keys()

    def get_groups(self, rid):
        return list(self.config[rid])

