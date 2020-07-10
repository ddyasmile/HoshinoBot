from hoshino import Service, priv, util
from .spider import *
from .subscriber import *
from hoshino.typing import *

sv = Service('bili-subscribe', bundle='Bilibili订阅', help_='UP主更新提醒')
sc = Subscriber()

_video_cache: Dict[ str, ItemsCache ] = {}

@sv.on_prefix(('B站订阅'))
async def set_subcribe(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有管理员才能进行订阅', at_sender=True)
    mid = util.normalize_str(ev.message.extract_plain_text())
    if not name:
        await bot.finish(ev, '请在后面加上要订阅UP住的UID', at_sender=True)
    else:
        pass


