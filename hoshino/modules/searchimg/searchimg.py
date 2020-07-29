import os
import re
import io
import json
import requests
from io import BytesIO
from PIL import Image
from collections import OrderedDict

from hoshino import Service
from hoshino.typing import CQEvent, MessageSegment

sv = Service('picfinder', help_='''
[识图+图片] 查询图片来源
'''.strip())

api_key="da234a4bc5f6cc1b28b9995f3c97b9923ababad3"#https://saucenao.com/自行申请
EnableRename=False
minsim='65!'#相似度下限，低于下限不显示结果(80!指80%)
thumbSize = (250,250)

#启用或禁用索引，1：启用，0：禁用
index_hmags='1'#0: H-Magazines  (Last Updated: December 2010) 不完整 - 大部分被 #18 替代
index_reserved='1'#1
index_hcg='1'#2: H-Game CG  (Last Updated: June 2011) 不完整 - 大部分被 #18 替代
index_ddbobjects='1'#3: DoujinshiDB  (Last Updated: January 2011) 不完整 - 大部分被 #18 替代
index_ddbsamples='1'#4
index_pixiv='1'#5: pixiv Images  (Continuously Updated) 相当完整 - All accessible images are added every few hours
index_pixivhistorical='1'#6: pixiv Historical
index_reserved='1'#7
index_seigaillust='1'#8: Nico Nico Seiga  (Continuously Updated) 相当完整 - All accessible images are added every few hours
index_danbooru='1'#9: Danbooru  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_drawr='1'#10: drawr Images  (Site Closed December 2, 2019) Complete - All accessible images were added before site shut down
index_nijie='1'#11: Nijie Images  (Continuously Updated) 相当完整 - All accessible images are added every few hours
index_yandere='1'#12: Yande.re  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_animeop='1'#13
index_reserved='1'#14
index_shutterstock='1'#15: Shutterstock  (Last Updated: August 2015) 不完整 (禁用) - Automatic updater broken, index disabled temporarily
index_fakku='1'#16: FAKKU  (On Hold) 不完整 - Site Changes Broke Update Script
index_hmisc='1'#18,38: H-Misc  (Continuously Updated) 相当完整 - Accessible Doujins, Magazines, HCG, etc are added every few hours.
index_2dmarket='1'#19: 2D-Market  (Continuously Updated) 相当完整 - All accessible images are added every few hours
index_medibang='1'#20: MediBang  (Last Updated Late 2019) 落后... - Updater Broken
index_anime='1'#21: Anime  (Continuously Updated) 相当完整 - New releases added automaticly
index_hanime='1'#22: H-Anime  (Continuously Updated) 相当完整 - New releases added automaticly, slowly filling out backolog of older material.
index_movies='1'#23: Movies  (Periodic) 工作正在进行中 - slowly filling out backlog of old material
index_shows='1'#24: Shows  (Periodic) 工作正在进行中 - slowly filling out backlog of old material
index_gelbooru='1'#25: Gelbooru  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_konachan='1'#26: Konachan  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_sankaku='1'#27: Sankaku Channel  (Updates on Hold) 不完整 - API is broken, can't get updates...
index_animepictures='1'#28: Anime-Pictures.net  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_e621='1'#29: e621.net  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_idolcomplex='1'#30: Idol Complex  (Continuously Updated) 相当完整 - All accessible images are added every few minutes
index_bcyillust='1'#31: bcy.net Illust  (Updates on Hold) 不完整 - Site changes make further updates unlikley
index_bcycosplay='1'#32: bcy.net Cosplay  (Updates on Hold) 不完整 - Site changes make further updates unlikley
index_portalgraphics='1'#33: PortalGraphics.net (Site Closed July 27, 2016) 相当完整 - Most accessible images have been added
index_da='1'#34: deviantArt (Last Updated: July 2017) 落后... - Caught up with dA as of July 2017, but system to keep it up to date is not yet in place. Soon...
index_pawoo='1'#35: Pawoo.net (On Hold) 落后... - Automatic updater broken
index_madokami='1'#36: Madokami (Manga) (Last Updated: November 2018) 相当完整
index_mangadex='1'#37: MangaDex (Continuously Updated) 相当完整 - New chapters are added every few minutes.

#生成bitmask
db_bitmask = int(index_mangadex+index_madokami+index_pawoo+index_da+index_portalgraphics+index_bcycosplay+index_bcyillust+index_idolcomplex+index_e621+index_animepictures+index_sankaku+index_konachan+index_gelbooru+index_shows+index_movies+index_hanime+index_anime+index_medibang+index_2dmarket+index_hmisc+index_fakku+index_shutterstock+index_reserved+index_animeop+index_yandere+index_nijie+index_drawr+index_danbooru+index_seigaillust+index_anime+index_pixivhistorical+index_pixiv+index_ddbsamples+index_ddbobjects+index_hcg+index_hanime+index_hmags,2)

wait_list = {}

def get_pic(address):
    return requests.get(address,timeout=20).content

@sv.on_fullmatch(('识图', '搜图'))
async def findertrigger(bot, ev: CQEvent):
    await bot.send(ev, '请发送一张图片', at_sender=True)
    wait_list[ev['user_id']] = []

@sv.on_message('group')
async def picfinder(bot, ev: CQEvent):
    user_id = ev['user_id']
    if user_id not in wait_list.keys():
        return

    del wait_list[ev['user_id']]
    sv.logger.info(f'开始为QQ:{ev.user_id}搜索')

    ret = re.match(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    image = Image.open(BytesIO(get_pic(ret.group(2))))
    image = image.convert('RGB')
    image.thumbnail(thumbSize, resample=Image.ANTIALIAS)
    imageData = io.BytesIO()
    image.save(imageData,format='PNG')

    url = 'http://saucenao.com/search.php?output_type=2&numres=1&minsim='+minsim+'&dbmask='+str(db_bitmask)+'&api_key='+api_key
    files = {'file': ("image.png", imageData.getvalue())}
    imageData.close()
    
    processResults = True
    while True:
        r = requests.post(url, files=files)
        if r.status_code != 200:
            if r.status_code == 403:
                sv.logger.info('Incorrect or Invalid API Key! Please Edit Script to Configure...')
            else:
                sv.logger.info("status code: "+str(r.status_code))
        else:
            results = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(r.text)
            if int(results['header']['user_id'])>0:
                sv.logger.info('搜索限制 30s|24h: '+str(results['header']['short_remaining'])+'|'+str(results['header']['long_remaining']))
                if int(results['header']['status'])==0:
                    #搜索所有索引成功，结果可用
                    break
                else:
                    if int(results['header']['status'])>0:
                        #一个或多个索引出现问题。
                        #即使所有索引都失败，此搜索仍被视为部分成功，因此仍将计入接口限制。
                        #错误可能是暂时的，请过段时间再重试。
                        sv.logger.info('API错误。请在600秒后重试。。。')
                    else:
                        #提交的搜索有问题，或请求出错。
                        #出现此问题请不要大量发送请求。
                        sv.logger.info('错误的图像或其他请求错误。。。')
                        processResults = False
                        break
            else:
                #api没有响应
                #出现此问题请不要大量发送请求。
                sv.logger.info('错误的图像或其他请求错误。。。')
                processResults = False
                break
    
    if processResults:
        
        if int(results['header']['results_returned']) > 0:
            #返回了一个或多个结果，判断相似度是否符合要求，取第一条结果
            print(results)
            if float(results['results'][0]['header']['similarity']) > float(results['header']['minimum_similarity']):
                hit = str(results['results'][0]['header']['similarity'])
                ext_url = ''
                ext_urls = []
                preview_url = results['results'][0]['header']['thumbnail']
                service_name = ''
                service_names = []
                illust_id = 0
                illust_ids = []
                member_id = -1
                member_ids = []
                author_name = ''
                author_names = []
                title = ''
                titles = []
                index_id = results['results'][0]['header']['index_id']
                index_ids = []
                page_string = ''
                page_match = re.search(r'(_p[\d]+)\.', results['results'][0]['header']['thumbnail'])
                if page_match:
                    page_string = page_match.group(1)
                    
                if index_id == 5 or index_id == 6:
                    #5->pixiv 6->pixiv historical
                    service_name='pixiv'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['pixiv_id']
                    author_name = results['results'][0]['data']['member_name']
                    title = results['results'][0]['data']['title']
                elif index_id == 8:
                    service_name='nico nico seiga'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['seiga_id']
                    author_name = results['results'][0]['data']['member_name']
                    title = results['results'][0]['data']['title']
                elif index_id == 9:#启用此项需自行修改获取返回的结构
                    service_name='Danbooru'
                    ext_url = results['results'][0]['data']['source']
                    illust_id = results['results'][0]['data']['danbooru_id']
                    author_name = results['results'][0]['data']['creator']
                elif index_id == 10:
                    service_name='drawr Images'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['drawr_id']								
                elif index_id == 11:
                    service_name='Nijie Images'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    member_id = results['results'][0]['data']['member_id']
                    illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 12:#启用此项需自行修改获取返回的结构
                #     service_name='Yande.re'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['yande_id']
                elif index_id == 18 or index_id == 38:#启用此项需自行修改获取返回的结构
                    service_name = results['results'][0]['header']['index_name']
                    author_name = results['results'][0]['data']['creator'][0]
                    title = results['results'][0]['data']['jp_name']
                    ext_url = results['results'][0]['data']['source']
                # elif index_id == 19:#启用此项需自行修改获取返回的结构
                #     service_name='2D-Market'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                elif index_id == 21:
                    service_name='Anime'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    title = results['results'][0]['data']['source']
                    illust_id=results['results'][0]['data']['anidb_aid']
                # elif index_id == 22:#启用此项需自行修改获取返回的结构
                #     service_name='H-Anime'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 25:#启用此项需自行修改获取返回的结构
                #     service_name='Gelbooru'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 26:#启用此项需自行修改获取返回的结构
                #     service_name='Konachan'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 27:
                #     service_name='Sankaku Channel'
                #     illust_id=results['results'][0]['data']['sankaku_id']
                #     author_name = results['results'][0]['data']['creator']
                #     title = results['results'][0]['data']['material']
                # elif index_id == 28:#启用此项需自行修改获取返回的结构
                #     service_name='Anime-Pictures.net'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 29:#启用此项需自行修改获取返回的结构
                #     service_name='e621.net'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 30:#启用此项需自行修改获取返回的结构
                #     service_name='Idol Complex'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                # elif index_id == 31:
                #     service_name='bcy.net Illust'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['bcy_id']
                #     author_name = results['results'][0]['data']['member_name']
                #     title = results['results'][0]['data']['title']
                # elif index_id == 33:#启用此项需自行修改获取返回的结构
                #     service_name='PortalGraphics.net'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                elif index_id == 34:
                    service_name='deviantArt'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    illust_id=results['results'][0]['data']['da_id']
                    author_name = results['results'][0]['data']['pawoo_user_username']
                    title = results['results'][0]['data']['title']
                # elif index_id == 35:
                #     service_name='Pawoo.net'
                #     illust_id=results['results'][0]['data']['pawoo_id']
                #     author_name = results['results'][0]['data']['author_name']
                #     title = results['results'][0]['data']['pawoo_user_display_name']
                # elif index_id == 36:#启用此项需自行修改获取返回的结构
                #     service_name='Madokami (Manga)'
                #     member_id = results['results'][0]['data']['member_id']
                #     illust_id=results['results'][0]['data']['nijie_id']
                elif index_id == 37:#启用此项需自行修改获取返回的结构
                    service_name='MangaDex'
                    ext_url = results['results'][0]['data']['ext_urls'][0]
                    illust_id=results['results'][0]['data']['md_id']
                    author_name = results['results'][0]['data']['artist']
                    title = results['results'][0]['data']['source']
                else:
                    #unknown
                    sv.logger.info(f'未知的索引编号:{index_id}')
                    await bot.send(ev, '没有查询到相似图片。。。', at_sender=True)
                    
                try:
                    sv.logger.info('开始尝试发送图片')
                    await bot.send(ev, MessageSegment.image(preview_url))
                except Exception as e:
                    await bot.send('尝试发送匹配的图片失败，请点击URL前往')
                
                try:
                    if member_id >= 0:
                        if author_name:
                            await bot.send(ev, '相似度:'+hit+'\n来源:'+service_name+'\n标题:'+title+'\n作者:'+author_name+'('+str(member_id)+')'+'\n编号:'+str(illust_id)+page_string+'\nurl:'+ext_url, at_sender=True)
                        else:
                            await bot.send(ev, '相似度:'+hit+'\n来源:'+service_name+'\n标题:'+title+'\n编号:'+str(illust_id)+page_string+'\nurl:'+ext_url, at_sender=True)
                    else:
                        if author_name:
                            await bot.send(ev, '相似度:'+hit+'\n来源:'+service_name+'\n标题:'+title+'\n作者:'+author_name+'\n编号:'+str(illust_id)+page_string+'\nurl:'+ext_url, at_sender=True)
                        else:
                            await bot.send(ev, '相似度:'+hit+'\n来源:'+service_name+'\n标题:'+title+'\n编号:'+str(illust_id)+page_string+'\nurl:'+ext_url, at_sender=True)
                except Exception as e:
                    sv.logger.error(e)
                
            else:
                await bot.send(ev, '相似度'+str(results['results'][0]['header']['similarity'])+'过低,可能：确实找不到此图/图为原图的局部图/图清晰度太低/搜索引擎尚未同步新图', at_sender=True)
                
        else:
            await bot.send(ev, '没有查询到相似图片。。。', at_sender=True)

        if int(results['header']['long_remaining'])<1:
            await bot.send(ev, '超过今日的搜索上限，请在6小时后重试。。。', at_sender=True)
            sv.logger.info('已超过今日的搜索上限')
        if int(results['header']['short_remaining'])<1:
            await bot.send(ev, '超过30秒搜索上限，请稍后再试。。。', at_sender=True)

        sv.logger.info(f'QQ:{ev.user_id}的搜索结束')
