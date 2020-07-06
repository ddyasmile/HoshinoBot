import pytz
import random
from datetime import datetime
from hoshino import util
from hoshino.res import R
from hoshino.service import Service

sv = Service('hourcallyao', enable_on_default=False)

@sv.scheduled_job('cron', hour='*', )
async def hour_call_yao():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if not now.hour % 6 == 0:
        return
    await sv.broadcast(str(R.img(f"yao{random.randint(1, 4)}.png").cqcode), 'hourcallyao', 0)
