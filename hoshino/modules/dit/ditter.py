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


_dit_dir = os.path.expanduser('~/.hoshino/.dit/')
os.makedirs(_dit_dir, exist_ok=True)

def _load_dit():
    dit_file = os.path.join(_dit_dir, 'dit.json')
    if not os.path.exists(dit_file):
        return {}
    try:
        with open(dit_file, encoding='utf8') as f:
            log = json.load(f)
            log = json.loads(log)
            return log
    except Exception as e:
        return {}

def _save_dit(ditter):
    dit_file = os.path.join(_dit_dir, 'dit.json')
    with open(dit_file, 'w', encoding='utf8') as f:
        json.dump(
            json.dumps(ditter.log),
            f,
            ensure_ascii=False,
            indent=2
        )

class Ditter:
    """模仿 git， 记录版本更新附带消息
    """

    def __init__(self):
        self.log: Dict[str, list()] = _load_dit()

    def get_next_id(self, group_id) -> str:
        return f'D{len(self.log[group_id])}'

    def dit_add(self, group_id, sender, time, msg):
        if group_id not in self.log:
            self.log[group_id] = list()
        dit_id = self.get_next_id(group_id)
        item = dict()
        item["id"] = dit_id
        item["sender"] = sender
        item["time"] = time
        item["msg"] = msg
        self.log[group_id].append(item)
        _save_dit(self)

    def dit_del(self, group_id, dit_id):
        print(self.log)
        if group_id not in self.log:
            print("error")
            return
        for item in self.log[group_id]:
            if item["id"] == dit_id:
                self.log[group_id].remove(item)
                print(self.log)
                _save_dit(self)
                break
    
    def dit_modify(self, group_id, dit_id, sender, time, msg):
        if group_id not in self.log:
            return
        for item in self.log[group_id]:
            if item["id"] == dit_id:
                item["sender"] = sender
                item["time"] = time
                item["msg"] = msg

                _save_dit(self)
                break
    
    def dit_log(self, group_id, num=5, all_log=False):
        if group_id not in self.log:
            return None
        if all_log:
            return self.log[group_id]
        return self.log[group_id][::-1][0:num]
    
    def dit_last(self, group_id):
        if group_id not in self.log:
            return None
        return self.log[group_id][-1]


