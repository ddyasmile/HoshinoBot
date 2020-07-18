import asyncio

import pytz
from datetime import datetime

from hoshino import Service, util
from .ditter import *
from hoshino.typing import *

help_ = """Dit 消息记录系统
<参数>：参数
[可选参数]：可选参数
-----
dit add <msg> 添加记录 返回一个 id
dit del <id> 删除记录 返回一个 id
dit modify <id> <msg> 修改记录 返回一个 id
dit log [num] 返回num条记录，缺省为5条
dit last 返回上一条记录
"""

sv = Service('dit', bundle='dit', help_=help_)
ditter = Ditter()

tz = pytz.timezone('Asia/Shanghai')

@sv.on_prefix(('dit add'))
async def add_dit(bot, ev: CQEvent):
    msg = util.normalize_str(ev.message.extract_plain_text())
    sender  = ev.sender["nickname"]
    if ev.sender["card"] != "":
        sender = ev.sender["card"]
    time =  datetime.now(tz).isoformat()
    ditter.dit_add(str(ev.group_id), sender, time, msg)
    try:
        await bot.send(ev, f'{ditter.dit_last(str(ev.group_id))["id"]}', at_sender=True)
    except Exception as e :
        sv.logger.error(f'群{ev.group_id}添加dit条目失败')
        sv.logger.exception(e)
        await bot.send(ev, '出错了亲~，请再试一次', at_sender=True)

@sv.on_prefix(('dit del'))
async def del_dit(bot, ev: CQEvent):
    dit_id = ev.message.extract_plain_text()
    ditter.dit_del(str(ev.group_id), dit_id)
    try:
        await bot.send(ev, f'{dit_id}', at_sender=True)
    except Exception as e :
        sv.logger.error(f'群{ev.group_id}删除dit条目失败')
        sv.logger.exception(e)
        await bot.send(ev, '出错了亲~，请再试一次', at_sender=True)

@sv.on_prefix(('dit modify'))
async def modify_dit(bot, ev: CQEvent):
    args = util.normalize_str(ev.message.extract_plain_text()).strip()
    arg_list = args.split()
    if len(arg_list) != 2:
        await bot.finish(ev, "请输入要修改的记录ID和新的内容", at_sender=True)
    dit_id = arg_list[0]
    msg = arg_list[1]
    sender  = ev.sender["nickname"]
    if ev.sender["card"] != "":
        sender = ev.sender["card"]
    time =  datetime.now(tz).isoformat()
    ditter.dit_modify(str(ev.group_id), dit_id, sender, time, msg)
    try:
        await bot.send(ev, f'{dit_id}', at_sender=True)
    except Exception as e :
        sv.logger.error(f'群{ev.group_id}修改dit条目失败')
        sv.logger.exception(e)
        await bot.send(ev, '出错了亲~，请再试一次', at_sender=True)


def get_format(logs) -> str:
    if not logs:
        return ""
    ret = []
    for log in logs:
        log_str = f'ID: {log["id"]}\nSender: {log["sender"]}\nTime: {log["time"]}\nMessage: {log["msg"]}'
        ret.append(log_str)
    return '\n======\n'.join(ret)

@sv.on_prefix(('dit log'))
async def log_dit(bot, ev: CQEvent):
    num = util.normalize_str(ev.message.extract_plain_text())
    logs = list()
    if not num:
        logs = ditter.dit_log(str(ev.group_id))
    else:
        logs = ditter.dit_log(str(ev.group_id), num=int(num))

    await bot.send(ev, get_format(logs))

@sv.on_fullmatch(('dit log -a'))
async def log_dit_all(bot, ev: CQEvent):
    logs = ditter.dit_log(str(ev.group_id), all_log=True)
    await bot.send(ev, get_format(logs))

@sv.on_fullmatch(('dit last'))
async def last_dit(bot, ev: CQEvent):
    log = ditter.dit_last(str(ev.group_id))
    logs = [ log ]
    await bot.send(ev, get_format(logs))

