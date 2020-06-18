# 统计各个群组群元的发言数量

from typing import Dict

from nonebot import NoneBot,CommandSession
from hoshino.service import Service

sv = Service('msgcounter', enable_on_default=True)

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
async def _msg_bus(bot:NoneBot, ctx):
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

@sv.on_command('水量', aliases='氵量', only_to_me=False)
async def query_num(session:CommandSession):
    sendmsg = '今日氵量排位（前五）：\n' + query_msgcounter(session.ctx['group_id'], 5)
    await session.send(sendmsg)

@sv.on_command('完整水量排位', aliases=('完整氵量排位'), only_to_me=False)
async def query_num_all(session:CommandSession):
    sendmsg = '今日氵量排位：\n' + query_msgcounter(session.ctx['group_id'], 999)
    await session.send(sendmsg)

@sv.scheduled_job('cron', hour='0')
def clear_counter():
    _msgcounter.clear()
