import time
import traceback
from typing import Optional, Union

import pyecharts.options as opts
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image
from pyecharts.charts import Pie
from pyecharts.render import make_snapshot
from snapshot_phantomjs import snapshot

from ..config import *
from .image import image_to_base64, text_to_image
from .maimaidx_api_data import *
from .maimaidx_best_50 import computeRa, generateAchievementList
from .maimaidx_music import Music, mai
from .maimaidx_draw import *
from .maimaidx_draw_dx import *
from .maimaidx_yang_50 import *
from .maimaidx_draw_diff import *
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageEvent,
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
)
import re
from typing import List, Union
from nonebot.plugin import on_message, PluginMetadata


realAchievementList = {}
for acc in [i / 10 for i in range(10, 151)]:
    realAchievementList[f'{acc:.1f}'] = generateAchievementList(acc)


async def music_global_data(music: Music, level_index: int) -> Union[str, MessageSegment, None]:
    stats = music.stats[level_index]
    fc_data_pair = [list(z) for z in zip([c.upper() if c else 'Not FC' for c in [''] + comboRank], stats.fc_dist)]
    acc_data_pair = [list(z) for z in zip([s.upper() for s in scoreRank], stats.dist)]

    Pie(
        init_opts=opts.InitOpts(
            width='1000px',
            height='800px',
            bg_color='#fff',
            js_host='./'
        )
    ).add(
        series_name='全连等级',
        data_pair=fc_data_pair,
        radius=[0, '30%'],
        label_opts=opts.LabelOpts(
            position='outside',
            formatter='{a|{a}}{abg|}\n{hr|}\n {b|{b}: }{c}  {per|{d}%}  ',
            background_color='#eee',
            border_color='#aaa',
            border_width=1,
            border_radius=4,
            rich={
                'a': {'color': '#999', 'lineHeight': 22, 'align': 'center'},
                'abg': {
                    'backgroundColor': '#e3e3e3',
                    'width': '100%',
                    'align': 'right',
                    'height': 22,
                    'borderRadius': [4, 4, 0, 0],
                },
                'hr': {
                    'borderColor': '#aaa',
                    'width': '100%',
                    'borderWidth': 0.5,
                    'height': 0,
                },
                'b': {'fontSize': 16, 'lineHeight': 33},
                'per': {
                    'color': '#eee',
                    'backgroundColor': '#334455',
                    'padding': [2, 4],
                    'borderRadius': 2,
                },
            },
        )
    ).add(
        series_name='达成率等级',
        data_pair=acc_data_pair,
        radius=['50%', '70%'],
        is_clockwise=True,
        label_opts=opts.LabelOpts(
            position='outside',
            formatter='{a|{a}}{abg|}\n{hr|}\n {b|{b}: }{c}  {per|{d}%}  ',
            background_color='#eee',
            border_color='#aaa',
            border_width=1,
            border_radius=4,
            rich={
                'a': {'color': '#999', 'lineHeight': 22, 'align': 'center'},
                'abg': {
                    'backgroundColor': '#e3e3e3',
                    'width': '100%',
                    'align': 'right',
                    'height': 22,
                    'borderRadius': [4, 4, 0, 0],
                },
                'hr': {
                    'borderColor': '#aaa',
                    'width': '100%',
                    'borderWidth': 0.5,
                    'height': 0,
                },
                'b': {'fontSize': 16, 'lineHeight': 33},
                'per': {
                    'color': '#eee',
                    'backgroundColor': '#334455',
                    'padding': [2, 4],
                    'borderRadius': 2,
                },
            },
        )
    ).set_global_opts(
        title_opts=opts.TitleOpts(
            title=f'{music.id} {music.title} {diffs[level_index]}',
            pos_left='center',
            pos_top='20',
            title_textstyle_opts=opts.TextStyleOpts(color='#2c343c'),
        ),
        legend_opts=opts.LegendOpts(
            pos_left=15,
            pos_top=10,
            orient='vertical'
        )
    ).set_series_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger='item', formatter='{a} <br/>{b}: {c} ({d}%)'
        )
    ).render(str(static / 'temp_pie.html'))
    make_snapshot(snapshot, str(static / 'temp_pie.html'), str(static / 'temp_pie.png'), is_remove_html=False)

    im = Image.open(static / 'temp_pie.png')
    msg = MessageSegment.image(image_to_base64(im))

    return msg


async def rise_score_data(qqid: int, username: Optional[str], rating: str, score: str, nickname: Optional[str] = None) -> str:
    """
    上分数据
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `rating` : 定数
    - `score` : 分数
    - `nickname` : 用户昵称
    """
    try:
        dx_ra_lowest = 999
        sd_ra_lowest = 999
        player_dx_list = []
        player_sd_list = []
        music_dx_list: List[List[Union[Music, str, float, int]]] = []
        music_sd_list: List[List[Union[Music, str, float, int]]] = []

        player_data = await maiApi.query_user('player', qqid=qqid, username=username)

        for dx in player_data['charts']['dx']:
            dx_ra_lowest = min(dx_ra_lowest, dx['ra'])
            player_dx_list.append([int(dx['song_id']), int(dx["level_index"]), int(dx['ra'])])
        for sd in player_data['charts']['sd']:
            sd_ra_lowest = min(sd_ra_lowest, sd['ra'])
            player_sd_list.append([int(sd['song_id']), int(sd["level_index"]), int(sd['ra'])])
        player_dx_id_list = [[d[0], d[1]] for d in player_dx_list]
        player_sd_id_list = [[s[0], s[1]] for s in player_sd_list]

        for music in mai.total_list:
            for i, ds in enumerate(music.ds):
                for achievement in realAchievementList[f'{ds:.1f}']:
                    if rating and music.level[i] != rating: continue
                    if f'{achievement:.1f}' == '100.5':
                        index_score = 12
                    else:
                        index_score = [index for index, acc in enumerate(achievementList[:-1]) if acc <= achievement < achievementList[index + 1]][0]
                    if music.basic_info.is_new:
                        music_ra = computeRa(ds, achievement)
                        if music_ra < dx_ra_lowest: continue
                        if [int(music.id), i] in player_dx_id_list:
                            player_ra = player_dx_list[player_dx_id_list.index([int(music.id), i])][2]
                            if music_ra - player_ra == int(score) and [int(music.id), i, music_ra] not in player_dx_list:
                                music_dx_list.append([music, diffs[i], ds, achievement, scoreRank[index_score + 1].upper(), music_ra])
                        else:
                            if music_ra - dx_ra_lowest == int(score) and [int(music.id), i, music_ra] not in player_dx_list:
                                music_dx_list.append([music, diffs[i], ds, achievement, scoreRank[index_score + 1].upper(), music_ra])
                    else:
                        music_ra = computeRa(ds, achievement)
                        if music_ra < sd_ra_lowest: continue
                        if [int(music.id), i] in player_sd_id_list:
                            player_ra = player_sd_list[player_sd_id_list.index([int(music.id), i])][2]
                            if music_ra - player_ra == int(score) and [int(music.id), i, music_ra] not in player_sd_list:
                                music_sd_list.append([music, diffs[i], ds, achievement, scoreRank[index_score + 1].upper(), music_ra])
                        else:
                            if music_ra - sd_ra_lowest == int(score) and [int(music.id), i, music_ra] not in player_sd_list:
                                music_sd_list.append([music, diffs[i], ds, achievement, scoreRank[index_score + 1].upper(), music_ra])

        if len(music_dx_list) == 0 and len(music_sd_list) == 0:
            return '没有找到这样的乐曲'

        appellation = nickname if nickname else '您'
        result = ''
        if len(music_sd_list) != 0:
            result += f'为{appellation}推荐以下标准乐曲：\n'
            for music, diff, ds, achievement, rank, ra in sorted(music_sd_list, key=lambda i: int(i[0].id)):
                result += f'{music.id}. {music.title} {diff} {ds} {achievement} {rank} {ra}\n'
        if len(music_dx_list) != 0:
            result += f'\n为{appellation}推荐以下new乐曲：\n'
            for music, diff, ds, achievement, rank, ra in sorted(music_dx_list, key=lambda i: int(i[0].id)):
                result += f'{music.id}. {music.title} {diff} {ds} {achievement} {rank} {ra}\n'
                
        msg = MessageSegment.image(image_to_base64(text_to_image(result.strip())))
    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
        
    return msg


async def player_plate_data(qqid: int, username: Optional[str], ver: str, plan: str, nickname: Optional[str]) -> str:
    """
    查看将牌
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `ver` : 版本
    - `plan` : 目标
    - `nickname` : 用户昵称
    """
    try:
        song_played = []
        song_remain_basic = []
        song_remain_advanced = []
        song_remain_expert = []
        song_remain_master = []
        song_remain_re_master = []
        song_remain_difficult = []
        
        if ver in ['霸', '舞']:
            version = list(set(_v for _v in list(plate_to_version.values())[:-9]))
        elif ver == '真':
            version = list(set(_v for _v in list(plate_to_version.values())[0:2]))
        elif ver == '华':
            version = [plate_to_version['熊']]
        elif ver == '星':
            version = [plate_to_version['宙']]
        elif ver == '祝':
            version = [plate_to_version['祭']]
        else:
            version = [plate_to_version[ver]]
        data = await maiApi.query_user('plate', qqid=qqid, username=username, version=version)
        
        if ver == '真':
            verlist = list(filter(lambda x: x['title'] != 'ジングルベル', data['verlist']))
        else:
            verlist = data['verlist']

        if plan in ['将', '者']:
            for song in verlist:
                if song['level_index'] == 0 and song['achievements'] < (100.0 if plan == '将' else 80.0):
                    song_remain_basic.append([song['id'], song['level_index']])
                if song['level_index'] == 1 and song['achievements'] < (100.0 if plan == '将' else 80.0):
                    song_remain_advanced.append([song['id'], song['level_index']])
                if song['level_index'] == 2 and song['achievements'] < (100.0 if plan == '将' else 80.0):
                    song_remain_expert.append([song['id'], song['level_index']])
                if song['level_index'] == 3 and song['achievements'] < (100.0 if plan == '将' else 80.0):
                    song_remain_master.append([song['id'], song['level_index']])
                if ver in ['舞', '霸'] and song['level_index'] == 4 and song['achievements'] < (100.0 if plan == '将' else 80.0):
                    song_remain_re_master.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        elif plan in ['極', '极']:
            for song in verlist:
                if song['level_index'] == 0 and not song['fc']:
                    song_remain_basic.append([song['id'], song['level_index']])
                if song['level_index'] == 1 and not song['fc']:
                    song_remain_advanced.append([song['id'], song['level_index']])
                if song['level_index'] == 2 and not song['fc']:
                    song_remain_expert.append([song['id'], song['level_index']])
                if song['level_index'] == 3 and not song['fc']:
                    song_remain_master.append([song['id'], song['level_index']])
                if ver == '舞' and song['level_index'] == 4 and not song['fc']:
                    song_remain_re_master.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        elif plan == '舞舞':
            for song in verlist:
                if song['level_index'] == 0 and song['fs'] not in ['fsd', 'fsdp']:
                    song_remain_basic.append([song['id'], song['level_index']])
                if song['level_index'] == 1 and song['fs'] not in ['fsd', 'fsdp']:
                    song_remain_advanced.append([song['id'], song['level_index']])
                if song['level_index'] == 2 and song['fs'] not in ['fsd', 'fsdp']:
                    song_remain_expert.append([song['id'], song['level_index']])
                if song['level_index'] == 3 and song['fs'] not in ['fsd', 'fsdp']:
                    song_remain_master.append([song['id'], song['level_index']])
                if ver == '舞' and song['level_index'] == 4 and song['fs'] not in ['fsd', 'fsdp']:
                    song_remain_re_master.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        elif plan == '神':
            for song in verlist:
                if song['level_index'] == 0 and song['fc'] not in ['ap', 'app']:
                    song_remain_basic.append([song['id'], song['level_index']])
                if song['level_index'] == 1 and song['fc'] not in ['ap', 'app']:
                    song_remain_advanced.append([song['id'], song['level_index']])
                if song['level_index'] == 2 and song['fc'] not in ['ap', 'app']:
                    song_remain_expert.append([song['id'], song['level_index']])
                if song['level_index'] == 3 and song['fc'] not in ['ap', 'app']:
                    song_remain_master.append([song['id'], song['level_index']])
                if ver == '舞' and song['level_index'] == 4 and song['fc'] not in ['ap', 'app']:
                    song_remain_re_master.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        for music in mai.total_list:
            if ver == '真' and music.title == 'ジングルベル':
                continue
            if music.basic_info.version in version:
                if [int(music.id), 0] not in song_played:
                    song_remain_basic.append([int(music.id), 0])
                if [int(music.id), 1] not in song_played:
                    song_remain_advanced.append([int(music.id), 1])
                if [int(music.id), 2] not in song_played:
                    song_remain_expert.append([int(music.id), 2])
                if [int(music.id), 3] not in song_played:
                    song_remain_master.append([int(music.id), 3])
                if ver in ['舞', '霸'] and len(music.level) == 5 and [int(music.id), 4] not in song_played:
                    song_remain_re_master.append([int(music.id), 4])
        song_remain_basic = sorted(song_remain_basic, key=lambda i: int(i[0]))
        song_remain_advanced = sorted(song_remain_advanced, key=lambda i: int(i[0]))
        song_remain_expert = sorted(song_remain_expert, key=lambda i: int(i[0]))
        song_remain_master = sorted(song_remain_master, key=lambda i: int(i[0]))
        song_remain_re_master = sorted(song_remain_re_master, key=lambda i: int(i[0]))
        for song in song_remain_basic + song_remain_advanced + song_remain_expert + song_remain_master + song_remain_re_master:
            music = mai.total_list.by_id(str(song[0]))
            if music.ds[song[1]] > 13.6:
                song_remain_difficult.append([music.id, music.title, diffs[song[1]], music.ds[song[1]], song[1]])

        appellation = nickname if nickname else '您'

        msg = f'''{appellation}的{ver}{plan}剩余进度如下：
Basic剩余{len(song_remain_basic)}首
Advanced剩余{len(song_remain_advanced)}首
Expert剩余{len(song_remain_expert)}首
Master剩余{len(song_remain_master)}首
'''
        song_remain: list[list] = song_remain_basic + song_remain_advanced + song_remain_expert + song_remain_master + song_remain_re_master
        song_record = [[s['id'], s['level_index']] for s in verlist]
        if ver in ['舞', '霸']:
            msg += f'Re:Master剩余{len(song_remain_re_master)}首\n'
        if len(song_remain_difficult) > 0:
            if len(song_remain_difficult) < 60:
                msg += '剩余定数大于13.6的曲目：\n'
                for i, s in enumerate(sorted(song_remain_difficult, key=lambda i: i[3])):
                    self_record = ''
                    if [int(s[0]), s[-1]] in song_record:
                        record_index = song_record.index([int(s[0]), s[-1]])
                        if plan in ['将', '者']:
                            self_record = str(verlist[record_index]['achievements']) + '%'
                        elif plan in ['極', '极', '神']:
                            if verlist[record_index]['fc']:
                                self_record = comboRank[combo_rank.index(verlist[record_index]['fc'])].upper()
                        elif plan == '舞舞':
                            if verlist[record_index]['fs']:
                                self_record = syncRank[sync_rank.index(verlist[record_index]['fs'])].upper()
                    msg += f'No.{i + 1} {s[0]}. {s[1]} {s[2]} {s[3]} {self_record}'.strip() + '\n'
                if len(song_remain_difficult) > 10:
                    msg = MessageSegment.image(image_to_base64(text_to_image(msg.strip())))
            else:
                msg += f'还有{len(song_remain_difficult)}首大于13.6定数的曲目，加油推分捏！\n'
        elif len(song_remain) > 0:
            for i, s in enumerate(song_remain):
                m = mai.total_list.by_id(str(s[0]))
                ds = m.ds[s[1]]
                song_remain[i].append(ds)
            if len(song_remain) < 60:
                msg += '剩余曲目：\n'
                for i, s in enumerate(sorted(song_remain, key=lambda i: i[2])):
                    m = mai.total_list.by_id(str(s[0]))
                    self_record = ''
                    if [int(s[0]), s[-1]] in song_record:
                        record_index = song_record.index([int(s[0]), s[-1]])
                        if plan in ['将', '者']:
                            self_record = str(verlist[record_index]['achievements']) + '%'
                        elif plan in ['極', '极', '神']:
                            if verlist[record_index]['fc']:
                                self_record = comboRank[combo_rank.index(verlist[record_index]['fc'])].upper()
                        elif plan == '舞舞':
                            if verlist[record_index]['fs']:
                                self_record = syncRank[sync_rank.index(verlist[record_index]['fs'])].upper()
                    msg += f'No.{i + 1} {m.id}. {m.title} {diffs[s[1]]} {m.ds[s[1]]} {self_record}'.strip() + '\n'
                if len(song_remain) > 10:
                    msg = MessageSegment.image(image_to_base64(text_to_image(msg.strip())))
            else:
                msg += '已经没有定数大于13.6的曲目了,加油清谱捏！\n'
        else:
            msg = f'已经没有剩余的的曲目了，恭喜{appellation}完成{ver}{plan}！'
    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


async def level_process_data(qqid: int, username: Optional[str], rating: str, rank: str, nickname: Optional[str]) -> str:
    """
    查看谱面等级进度
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `rating` : 定数
    - `rank` : 评价等级
    - `nickname` : 用户昵称
    """
    try:
        song_played = []
        song_remain = []
        version = list(set(_v for _v in list(plate_to_version.values())))
        data = await maiApi.query_user('plate', qqid=qqid, username=username, version=version)

        if rank.lower() in scoreRank:
            achievement = achievementList[scoreRank.index(rank.lower()) - 1]
            for song in data['verlist']:
                if song['level'] == rating and song['achievements'] < achievement:
                    song_remain.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        elif rank.lower() in comboRank:
            combo_index = comboRank.index(rank.lower())
            for song in data['verlist']:
                if song['level'] == rating and ((song['fc'] and combo_rank.index(song['fc']) < combo_index) or not song['fc']):
                    song_remain.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        elif rank.lower() in syncRank:
            sync_index = syncRank.index(rank.lower())
            for song in data['verlist']:
                if song['level'] == rating and ((song['fs'] and sync_rank.index(song['fs']) < sync_index) or not song['fs']):
                    song_remain.append([song['id'], song['level_index']])
                song_played.append([song['id'], song['level_index']])
        for music in mai.total_list:
            for i, lv in enumerate(music.level[2:]):
                if lv == rating and [int(music.id), i + 2] not in song_played:
                    song_remain.append([int(music.id), i + 2])
        song_remain = sorted(song_remain, key=lambda i: int(i[1]))
        song_remain = sorted(song_remain, key=lambda i: int(i[0]))
        songs = []
        for song in song_remain:
            music = mai.total_list.by_id(str(song[0]))
            songs.append([music.id, music.title, diffs[song[1]], music.ds[song[1]], song[1]])

        appellation = nickname if nickname else '您'

        msg = ''
        if len(song_remain) > 0:
            if len(song_remain) < 50:
                song_record = [[s['id'], s['level_index']] for s in data['verlist']]
                msg += f'{appellation}的{rating}全谱面{rank.upper()}剩余曲目如下：\n'
                for i, s in enumerate(sorted(songs, key=lambda i: i[3])):
                    self_record = ''
                    if [int(s[0]), s[-1]] in song_record:
                        record_index = song_record.index([int(s[0]), s[-1]])
                        if rank.lower() in scoreRank:
                            self_record = str(data['verlist'][record_index]['achievements']) + '%'
                        elif rank.lower() in comboRank:
                            if data['verlist'][record_index]['fc']:
                                self_record = comboRank[combo_rank.index(data['verlist'][record_index]['fc'])].upper()
                        elif rank.lower() in syncRank:
                            if data['verlist'][record_index]['fs']:
                                self_record = syncRank[sync_rank.index(data['verlist'][record_index]['fs'])].upper()
                    msg += f'No.{i + 1} {s[0]}. {s[1]} {s[2]} {s[3]} {self_record}'.strip() + '\n'
                if len(songs) > 10:
                    msg = MessageSegment.image(image_to_base64(text_to_image(msg.strip())))
            else:
                msg = f'{appellation}还有{len(song_remain)}首{rating}曲目没有达成{rank.upper()},加油推分捏！'
        else:
            msg = f'恭喜{appellation}达成{rating}全谱面{rank.upper()}！'
    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


async def level_achievement_list_data(qqid: int, username: Optional[str], rating: str, page: Optional[str], nickname: Optional[str], bot: Bot, event: MessageEvent) -> str:
    """
    查看分数列表
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `rating` : 定数
    - `page` : 页数
    - `nickname` : 用户昵称
    """
    fake_msg_list = []

    try:
        
        song_list = []
        version = list(set(_v for _v in list(plate_to_version.values())))
        data = await maiApi.query_user_dev(qqid=qqid, username=username)

        for song in data['records']:
            if song['level'] == rating:
                song_list.append(song)

        page = max(min(int(page), len(song_list) // SONGS_PER_PAGE + 1), 1) if page else 1

        if username!=None:
            qqid = None

        msg_pic = await generate_list(qqid, username, rating, page)

    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'

    return msg_pic

async def level_achievement_list_data_dx(qqid: int, username: Optional[str], rating: str, page: Optional[str], nickname: Optional[str], bot: Bot, event: MessageEvent) -> str:
    """
    查看分数列表
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `rating` : 定数
    - `page` : 页数
    - `nickname` : 用户昵称
    """
    fake_msg_list = []

    try:
        
        song_list = []
        version = list(set(_v for _v in list(plate_to_version.values())))
        data = await maiApi.query_user_dev(qqid=qqid, username=username)

        for song in data['records']:
            if song['level'] == rating:
                song_list.append(song)

        page = max(min(int(page), len(song_list) // SONGS_PER_PAGE + 1), 1) if page else 1

        if username!=None:
            qqid = None

        msg_pic = await generate_list_dx(qqid, username, rating, page)

    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'

    return msg_pic

async def level_achievement_list_diff_data(qqid: int, username: Optional[str], rating: str, diff: str, page: Optional[str], nickname: Optional[str], bot: Bot, event: MessageEvent) -> str:
    """
    查看谱面等级进度
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `rating` : 定数
    - `diff` : 难度
    - `nickname` : 用户昵称
    """
    try:
        song_list = []

        if username!=None:
            qqid = None
        
        data = await maiApi.query_user_dev(qqid=qqid, username=username)


        if diff == '绿':
            diff_index = 0
        elif diff == '黄':
            diff_index = 1
        elif diff == '红':
            diff_index = 2
        elif diff == '紫':
            diff_index = 3
        elif diff == '白':
            diff_index = 4
        for song in data['records']:
            if song['level'] == rating and song['level_index'] == diff_index:
                song_list.append(song)

        song_list = sorted(song_list, key=lambda i: i['achievements'], reverse=True)

        page = max(min(int(page), len(song_list) // SONGS_PER_PAGE + 1), 1) if page else 1

        msg_pic = await generate_list_diff(qqid, username, rating, page, diff_index)

    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg_pic

async def yang_b50_data(qqid: int, username: Optional[str], nickname: Optional[str], bot: Bot, event: MessageEvent) -> str:
    """
    查看杨氏B50
    
    - `qqid` : 用户QQ
    - `username` : 查分器用户名
    - `nickname` : 用户昵称
    """
    fake_msg_list = []
    try:

        msg_pic = await generate_yang50(qqid, username)

        '''
        song_list = []
        data = await maiApi.query_user_dev(qqid=qqid, username=username)

        for song in data['records']:
            if song['achievements'] > 100.0:
                song_list.append(song)

        appellation = nickname if nickname else '我'

        msg = ''
        # fake_msg_list.append((appellation, qqid, Message(msg)))

        for i, s in enumerate(song_list):
            m = mai.total_list.by_id(str(s['song_id']))
            total_dxscore = sum(mai.total_list.by_id(str(s['song_id'])).charts[s["level_index"]].notes) * 3
            dxrate = s["dxScore"] / total_dxscore * 100
            if dxrate <= 85:
                starnum = 0
            elif dxrate <= 90:
                starnum = 1
            elif dxrate <= 93:
                starnum = 2
            elif dxrate <= 95:
                starnum = 3
            elif dxrate <= 97:
                starnum = 4
            else:
                starnum = 5
            yrating = m.ds[s["level_index"]] * min((max(100*(s["achievements"]-100), 0)), dxrate)/100
            y8 = 0
            if s["fc"] == 'fcp':
                y8 += 1
            elif s["fc"] == 'ap' or s["fc"] == 'app':
                y8 += 2
            if s["achievements"] >= 100.98:
                y8 += 3
            elif s["achievements"] >= 100.95:
                y8 += 2
            elif s["achievements"] >= 100.9:
                y8 += 1
            y8 += max(starnum - 2, 0)
            song_list[i] = [m.id, m.title, diffs[s["level_index"]], m.ds[s["level_index"]], s["achievements"], s["fc"], s["fs"], s["dxScore"], total_dxscore, starnum, yrating, y8]
        song_list = sorted(song_list, key=lambda i: i[10], reverse=True)
        msg += f'共有{len(song_list)}首杨氏rating不为0的谱面成绩，前50首的平均杨氏rating为{sum([s[10] for s in song_list[:50]])/50:.3f}\n，前30首的平均杨氏rating为{sum([s[10] for s in song_list[:30]])/30:.3f}\n\n'
        msg += f'前50首杨氏rating列表（从高至低）：\n'
        for i, s in enumerate(song_list):
            if i < 50:
                msg_i = f'No.{i + 1} | {s[0]}. {s[1]} | {s[2]} | {s[3]} \n达成率：{s[4]:.4f}'
                if s[5]: msg_i += f' ({comboRank[combo_rank.index(s[5])].upper()})'
                if s[6]: msg_i += f' ({syncRank[sync_rank.index(s[6])].upper()})'
                msg_i += f'\ndx分：{s[7]}/{s[8]} ({s[9]})\n杨氏rating及8分法：{s[10]:.3f} ({s[11]})\n----------------------------'
                msg += f' {msg_i}\n'
                name = await bot.get_stranger_info(user_id=qqid)
                name = name["nickname"]
                qq = qqid
            # fake_msg_list.append((name, qq, Message(msg_i)))

        msg += f'\n（杨氏rating计算方式为：谱面定数*min(100*(达成率-100),dx分/总dx分)，最低为0；8分法计算方式为：FC+，AP，100.9，100.95，100.98，三星，四星，五星各计一分。仅供娱乐，请玩家合理参考，解释权归杨树森6所有。）'
        fake_msg_list.append((appellation, qqid, Message(msg)))
        '''
    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    # await send_forward_msg(bot, event, fake_msg_list)
    return msg_pic

async def rating_ranking_data(name: Optional[str], page: Optional[int]) -> str:
    """
    查看查分器排行榜
    
    - `name`: 指定用户名
    - `page`: 页数
    """
    try:
        rank_data = await maiApi.rating_ranking()

        sorted_rank_data = sorted(rank_data, key=lambda r: r['ra'], reverse=True)
        if name:
            if name in [r['username'].lower() for r in sorted_rank_data]:
                rank_index = [r['username'].lower() for r in sorted_rank_data].index(name) + 1
                nickname = sorted_rank_data[rank_index - 1]['username']
                data = f'截止至 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n玩家 {nickname} 在Diving Fish网站已注册用户ra排行第{rank_index}'
            else:
                data = '未找到该玩家'
        else:
            user_num = len(sorted_rank_data)
            msg = f'截止至 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}，Diving Fish网站已注册用户ra排行：\n'
            if page * 50 > user_num:
                page = user_num // 50 + 1
            end = page * 50 if page * 50 < user_num else user_num
            for i, ranker in enumerate(sorted_rank_data[(page - 1) * 50:end]):
                msg += f'{i + 1 + (page - 1) * 50}. {ranker["username"]} {ranker["ra"]}\n'
            msg += f'第{page}页，共{user_num // 50 + 1}页'
            data = MessageSegment.image(image_to_base64(text_to_image(msg.strip())))
    except Exception as e:
        log.error(traceback.format_exc())
        data = f'未知错误：{type(e)}\n请联系Bot管理员'
    return data

async def player_ranking_data(qqid: int, username: Optional[str], nickname: Optional[str]) -> str:
    try:
        rank_data = await maiApi.rating_ranking()
        rank_data = sorted(rank_data, key=lambda r: r['ra'], reverse=True)

        data = await maiApi.query_user_dev(qqid=qqid, username=username)
        user_ra = data['rating']
        user_rank = [r['username'].lower() for r in rank_data].index(data['username'].lower()) + 1
        nickname = data['username']
        data = f'截止至 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}，玩家 {nickname} 的rating为{user_ra}，在水鱼网站已注册用户排行第{user_rank}，超过了{(100-(user_rank / len(rank_data) * 100)):.2f}%的玩家。\n所有玩家的平均rating为{sum([r["ra"] for r in rank_data]) / len(rank_data):.2f}，中位rating为{rank_data[len(rank_data) // 2]["ra"]}。'
    except UserNotFoundError as e:
        data = str(e)
    except UserDisabledQueryError as e:
        data = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        data = f'未知错误：{type(e)}\n请联系Bot管理员'
    return data
'''
async def _(bot: Bot, event: Union[PrivateMessageEvent, GroupMessageEvent]):
    raw_message = event.raw_message
    fake_msg_list = []
    user_msgs = raw_message.split(user_split)
    for user_msg in user_msgs:
        qq_msg = user_msg.split("说", 1)[0].strip()
        if qq_msg.isdigit():
            qq = qq_msg
        else:
            qq = re.match(r"^\[CQ:at,qq=(\d{6,10})\]", qq_msg).group(1)
        msgs = user_msg.split("说", 1)[1].split(message_split)
        name = await bot.get_stranger_info(user_id=qq)
        name = name["nickname"]
        for msg in msgs:
            fake_msg_list.append((name, qq, Message(msg)))
    await send_forward_msg(bot, event, fake_msg_list)
'''

async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    msgs: List[Message],
) -> dict:
    """
    发送 forward 消息

    > 参数：
        - bot: Bot 对象
        - event: MessageEvent 对象
        - msgs: 消息列表

    > 返回值：
        - 成功：返回消息发送结果
        - 失败：抛出异常
    """

    def to_json(msg):
        return {
            "type": "node",
            "data": {"name": msg[0], "uin": msg[1], "content": msg[2]},
        }

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        return await bot.call_api(
            "send_group_forward_msg", group_id=event.group_id, messages=messages
        )
    else:
        return await bot.call_api(
            "send_private_forward_msg", user_id=event.user_id, messages=messages
        )