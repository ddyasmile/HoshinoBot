# 统计各个群组群元的发言数量

from typing import Dict

import hoshino
from hoshino import Service

from nonebot import NoneBot,CommandSession

sv = Service('msgcounter', enable_on_default=True, help_='群员发言数统计')

_msgcounter:Dict[int, Dict[str, int]] = {}

def query_msgcounter(groupid, length):
    # sort by value
    sort = []
    msgentry = _msgcounter[groupid]
    temp = sorted(msgentry.items(), key=lambda x: x[1], reverse=True)
    for key in temp:
        sort.append(key)

    # check length
    if len(sort) < length:
        length = len(sort)

    ret_msg = ''
    for i in range(0, length):
        ret_msg = ret_msg + f'No.{i+1}, {sort[i][0]} 发言数 {sort[i][1]}\n'
    
    return ret_msg

@sv.on_message('group')
async def _msg_bus(bot, ctx):
    # check sub_type
    if ctx['sub_type'] != 'normal':
        return
    
    # prepare sender name
    name = ctx["sender"]["card"]
    if name == '':
        name = ctx["sender"]["nickname"]

    # count msg
    if not ctx['group_id'] in _msgcounter:
        entry = { f'{name}': 1 }
        _msgcounter[ctx['group_id']] = entry
        return

    msgentry = _msgcounter[ctx['group_id']]
    if not name in msgentry:
        _msgcounter[ctx['group_id']][name] = 1
        return

    msgnum = msgentry[name]
    _msgcounter[ctx['group_id']][name] = msgnum + 1
    return

@sv.on_fullmatch(('水量', '氵量'))
async def query_num(bot, ev):
    sendmsg = '今日氵量排位（前五）：\n' + query_msgcounter(ev.group_id, 5)
    await bot.send(ev, sendmsg)

@sv.on_fullmatch(('完整水量排位', '完整氵量排位', '完整水量', '完整氵量'))
async def query_num_all(bot, ev):
    sendmsg = '今日氵量排位：\n' + query_msgcounter(ev.group_id, 999)
    await bot.send(ev, sendmsg)

@sv.scheduled_job('cron', hour='0')
def clear_counter():
    _msgcounter.clear()