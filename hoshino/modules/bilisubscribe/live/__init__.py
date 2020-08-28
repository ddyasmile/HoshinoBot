import asyncio
import copy

from nonebot import MessageSegment

from hoshino import Service, priv, util
from .spider import *
from .subscriber import *
from hoshino.typing import *

_help = """B站直播间开播下播提醒服务
==============
[live订阅 <直播间号>] 订阅直播间
[live退订 <直播间号>] 取消订阅直播间
[live订阅查询] 查看本群已订阅的直播间
[开播了吗 <直播间号>] 查看特定直播间是否开播
"""

sv = Service('bili-subscribe-live', bundle='Bilibili订阅', help_=_help)
ss = Subscriber()
sp = BiliLiveSpider()

_live_cache: Dict[ str, Item ] = {}


async def switch_subscribe(bot, ev: CQEvent, sub: bool):
    action_tip = "订阅" if sub else "退订"
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, f'只有管理员才能进行{action_tip}', at_sender=True)
    rid = util.normalize_str(ev.message.extract_plain_text())
    if not rid:
        await bot.finish(ev, f'请在指令后加上要{action_tip}的直播间号', at_sender=True)
    else:
        ss.add_subscription(rid, ev.group_id) if sub else ss.del_subscription(rid, ev.group_id)
        sv.logger.info(f'群{ev.group_id}{action_tip}了直播间{rid}')
        await bot.send(ev, f'已为群{ev.group_id}{action_tip}了直播间{rid}', at_sender=True)

@sv.on_prefix(('live订阅', '订阅直播间', '直播间订阅', '直播订阅'))
async def set_subcribe(bot, ev: CQEvent):
    rid = util.normalize_str(ev.message.extract_plain_text())
    check_flag = await sp.check_rid(rid)
    if check_flag:
        await switch_subscribe(bot, ev, sub=True)

@sv.on_prefix(('live退订', '退订直播间', '直播间退订', '直播退订'))
async def set_unsubscribe(bot, ev: CQEvent):
    await switch_subscribe(bot, ev, sub=False)

@sv.on_prefix(('live订阅查询', '直播间订阅查询'))
async def search_subscribe(bot, ev: CQEvent):
    if not _live_cache:
        await bot.send(ev, "第一次查询会比较慢，请稍等一会儿", at_sender=True)
        await live_poller(sp, sv, send_msg=False)
    rid_list = ss.search_subscription(ev.group_id)
    msg = f'群{ev.group_id}订阅了直播间：'
    for rid in rid_list:
        author: str = ""
        try:
            author = _live_cache[rid].author
        except:
            item = Item()
            await asyncio.sleep(1)
            await sp.get_update(rid, item)
            _live_cache[rid] = copy.deepcopy(item)
            sv.logger.info(f'更新了直播间{rid}的缓存')
            author = _live_cache[rid].author
        msg += f'\n主播 {author} 直播间号：{rid}'
    await bot.send(ev, msg, at_sender=True)


def get_format(rid: str, item: Item, live: bool) -> str:
    action_tip = "开播" if live else "下播"
    baseUrl = "https://live.bilibili.com/"
    content = ""
    if not item.cover:
        content = f'直播间【{item.title}】\n{baseUrl}{rid}'
    else:
        content = f'{MessageSegment.image(item.cover)}\n{item.title}\n{baseUrl}{rid}'
    author = item.author
    return f'{content}\n主播 {author} {action_tip}了'


async def live_poller(spider: BiliLiveSpider, sv: Service, send_msg=True, interval_time=1):
    rid_list = ss.get_rids()
    if not _live_cache:
        for rid in rid_list:
            item = Item()
            await asyncio.sleep(interval_time)
            await spider.get_update(rid, item)
            _live_cache[rid] = copy.deepcopy(item)
        sv.logger.info('直播间缓存为空，已加载至最新')
        return
    for rid in rid_list:
        await asyncio.sleep(interval_time)
        if rid not in _live_cache:
            _live_cache[rid] = Item()
            await spider.get_update(rid, _live_cache[rid])
            if _live_cache[rid]:
                sv.logger.info(f'拉取到直播间{rid}信息')
            else:
                sv.logger.info(f'未拉取到直播间{rid}信息')
            continue
        
        prev_status = _live_cache[rid].live_status
        await spider.get_update(rid, _live_cache[rid])
        sv.logger.info(f'更新了直播间{rid}信息')

        if send_msg:
            status_change = False
            msg = ""
            if prev_status != 1 and _live_cache[rid].live_status == 1:
                msg = get_format(rid, _live_cache[rid], True)
                status_change = True
            elif prev_status == 1 and _live_cache[rid].live_status != 1:
                msg = get_format(rid, _live_cache[rid], False)
                status_change = True
            else:
                continue

            if status_change:
                group_list = ss.get_groups(rid)
                enable_group_list = await sv.get_enable_groups()
                for group_id in group_list:
                    if group_id in enable_group_list:
                        try:
                            await asyncio.sleep(interval_time / 2.0)
                            await sv.bot.send_group_msg(
                                self_id=random.choice(enable_group_list[group_id]), 
                                group_id=group_id,
                                message=msg)
                            sv.logger.info(f'群{group_id}投递直播间{rid}消息成功')
                        except:
                            sv.logger.error(f'群{group_id}投递直播间{rid}消息失败')
                            sv.logger.exception(e)


# @sv.on_prefix(('pull'))
@sv.scheduled_job('interval', minutes=5)
async def poll_lives():
    await live_poller(sp, sv)


async def poll_live_by_rid(bot, ev: CQEvent, sv: Service ,spider: BiliLiveSpider):
    rid = util.normalize_str(ev.message.extract_plain_text())
    if rid not in _live_cache:
        _live_cache[rid] = Item()
    await spider.get_update(rid, _live_cache[rid])
    sv.logger.info(f'拉取了直播间{rid}消息')
    msg = ""
    if _live_cache[rid].live_status == 1:
        msg = get_format(rid, _live_cache[rid], True)
    else:
        msg = f'主播{_live_cache[rid].author}的直播间{rid}尚未开播'
    await bot.send(ev, msg, at_sender=True)


@sv.on_suffix(('开播了吗'))
@sv.on_prefix(('开播了吗'))
async def poll_one_live(bot, ev: CQEvent):
    await poll_live_by_rid(bot, ev, sv, sp)



