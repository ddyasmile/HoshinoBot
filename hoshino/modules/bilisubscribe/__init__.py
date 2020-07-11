import asyncio
import copy

from nonebot import MessageSegment

from hoshino import Service, priv, util
from .spider import *
from .subscriber import *
from hoshino.typing import *

sv = Service('bili-subscribe', bundle='Bilibili订阅', help_='UP主更新提醒')
ss = Subscriber()
sp = BiliSpider()

_video_cache: Dict[ str, ItemsCache ] = {}

async def switch_subscribe(bot, ev: CQEvent, sub: bool):
    action_tip = "订阅" if sub else "退订"
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, f'只有管理员才能进行{action_tip}', at_sender=True)
    mid = util.normalize_str(ev.message.extract_plain_text())
    if not mid:
        await bot.finish(ev, f'请在指令后加上要{action_tip}UP主的UID', at_sender=True)
    else:
        ss.add_subscription(mid, ev.group_id) if sub else ss.del_subscription(mid, ev.group_id)
        sv.logger.info(f'群{ev.group_id}{action_tip}了UP主{mid}')
        await bot.send(ev, f'已为群{ev.group_id}{action_tip}了UP主{mid}', at_sender=True)

@sv.on_prefix(('B站订阅'))
async def set_subcribe(bot, ev: CQEvent):
    mid = util.normalize_str(ev.message.extract_plain_text())
    check_flag = await sp.check_mid(mid)
    if check_flag:
        await switch_subscribe(bot, ev, sub=True)

@sv.on_prefix(('B站退订'))
async def set_unsubscribe(bot, ev: CQEvent):
    await switch_subscribe(bot, ev, sub=False)

@sv.on_prefix(('B站订阅查询'))
async def search_subscribe(bot, ev: CQEvent):
    await video_poller(sp, sv, send_msg=False)
    mid_list = ss.search_subscription(ev.group_id)
    msg = f'群{ev.group_id}订阅了UP主：'
    # print(mid_list)
    for mid in mid_list:
        # print(mid)
        # print(_video_cache[mid].item_cache)
        print(_video_cache[mid].item_cache[0].author)
        author = _video_cache[mid].item_cache[0].author
        msg += f'\n{author} UID：{mid}'
    await bot.send(ev, msg, at_sender=True)


def get_format(mid: str, items: List[Item]) -> str:
    baseUrl = "https://www.bilibili.com/video/"
    content = [ f'{MessageSegment.image(item.cover)}\n{item.title}\n{baseUrl}{item.bvid}' for item in items ]
    author = items[0].author
    return f'UP主{author}{mid}更新了视频：\n' + '\n'.join(content)


async def video_poller(spider: BiliSpider, sv: Service, send_msg=True, interval_time=1):
    mid_list = ss.get_mids()
    print(mid_list)
    if not _video_cache:
        for mid in mid_list:
            items_cache = ItemsCache()
            await asyncio.sleep(interval_time)
            await spider.get_update(mid, items_cache)
            _video_cache[mid] = copy.deepcopy(items_cache)
            print(items_cache.item_cache)
        sv.logger.info('视频缓存为空，已加载至最新')
        return
    for mid in mid_list:
        await asyncio.sleep(interval_time)
        videos = await spider.get_update(mid, _video_cache[mid])
        if not videos:
            sv.logger.info(f'未检索到UP主{mid}更新')
            continue
        sv.logger.info(f'检索到UP主{mid}{len(videos)}条更新')
        if send_msg:
            group_list = ss.get_groups(mid)
            enable_group_list = sv.get_enable_groups()
            for group_id in group_list:
                if group_id in enable_group_list:
                    msg = get_format(mid, videos)
                    try:
                        await asyncio.sleep(interval_time / 2.0)
                        await sv.bot.send_group_msg(
                            self_id=random.choice(enable_group_list[group_id]), 
                            group_id=group_id,
                            message=msg)
                        sv.logger.info(f'群{group_id}投递UP主{mid}更新信息成功')
                    except Exception as e:
                        sv.logger.error(f'群{group_id}投递UP主{mid}更新信息失败')
                        sv.logger.exception(e)
                


@sv.scheduled_job('interval', minutes=5)
async def poll_videos():
    await video_poller(sp, sv)


async def poll_videos_by_mid(bot, ev: CQEvent, spider: BiliSpider, max_num=3):
    mid = util.normalize_str(ev.message.extract_plain_text())
    await spider.get_update(mid, _video_cache[mid])
    videos = _video_cache[mid].item_cache[0:max_num]
    await bot.send(ev, get_format(mid, videos), at_sender=True)


@sv.on_prefix(('新视频'))
async def poll_latest_videos(bot, ev: CQEvent):
    await poll_videos_by_mid(bot, ev, sp)

    



