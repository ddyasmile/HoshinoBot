import pytz
import random
from datetime import datetime
import hoshino
from hoshino import util, R, Service

sv = Service('hourcallyao', enable_on_default=False, help_='提醒买药')
tz = pytz.timezone('Asia/Shanghai')

@sv.scheduled_job('cron', hour='*', )
async def hour_call_yao():
    now = datetime.now(tz)
    if not now.hour % 6 == 0:
        return
    await sv.broadcast(str(R.img(f"yao{random.randint(1, 4)}.png").cqcode), 'hourcallyao', 0)
