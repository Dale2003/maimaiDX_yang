import math
import traceback
from io import BytesIO
from typing import List, Optional, Tuple, Union

import httpx
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw
from pydantic import BaseModel

from ..config import *
from .image import DrawText, image_to_bytesio
from .maimaidx_api_data import maiApi
from .maimaidx_error import *
from .maimaidx_music import download_music_pictrue, mai


class ChartInfo(BaseModel):
    
    achievements: float
    ds: float
    dxScore: int
    fc: Optional[str] = ''
    fs: Optional[str] = ''
    level: str
    level_index: int
    level_label: str
    ra: int
    rate: str
    song_id: int
    title: str
    type: str
    dis: Optional[float] = None


class Data(BaseModel):

    sd: Optional[List[ChartInfo]] = None
    dx: Optional[List[ChartInfo]] = None


class UserInfo(BaseModel):

    additional_rating: Optional[int]
    charts: Optional[Data]
    nickname: Optional[str]
    plate: Optional[str] = None
    rating: Optional[int]
    username: Optional[str]
    records: Optional[List[ChartInfo]]


class DrawBest:

    def __init__(self, UserInfo: UserInfo, qqId: Optional[Union[int, str]] = None) -> None:

        self.userName = UserInfo.nickname
        self.plate = UserInfo.plate
        self.addRating = UserInfo.additional_rating
        self.Rating = UserInfo.rating
        self.qqId = qqId
        self.records = UserInfo.records

        '''id='382' title='おこちゃま戦争' type='SD' ds=[6.0, 7.3, 10.8, 13.3] level=['6', '7', '10+', '13'] cids=[2751, 2752, 2753, 2754] charts=[Chart(notes=Notes(tap=198, hold=24, slide=3, brk=7), charter='-'), Chart(notes=Notes(tap=345, hold=7, slide=10, brk=14), charter='-'), Chart(notes=Notes(tap=349, hold=58, slide=28, brk=14), charter='某S氏'), Chart(notes=Notes(tap=658, hold=27, slide=40, brk=15), charter='はっぴー')] basic_info=BasicInfo(title='おこちゃま戦争', artist='ギガ/れをる', genre='niconico & VOCALOID', bpm=175, release_date='', version='maimai ORANGE', is_new=False) stats=[Stats(cnt=1461.0, diff='6', fit_diff=6.044117206615401, avg=98.99056872005482, avg_dx=607.2190280629706, std_dev=1.463312987190402, dist=[11, 4, 6, 8, 6, 46, 16, 24, 17, 10, 10, 14, 151, 1138], fc_dist=[204.0, 91.0, 359.0, 470.0, 337.0]), Stats(cnt=2427.0, diff='7', fit_diff=7.464780370564297, avg=96.19806744952581, avg_dx=904.8475484136794, std_dev=3.6903192991508313, dist=[17, 16, 26, 26, 35, 228, 183, 220, 94, 121, 57, 66, 163, 1175], fc_dist=[1045.0, 171.0, 431.0, 635.0, 145.0]), Stats(cnt=11575.0, diff='10+', fit_diff=11.020517983062796, avg=96.49911479049715, avg_dx=1036.1744276457882, std_dev=3.1185126074217053, dist=[20, 24, 23, 30, 70, 725, 1238, 2371, 1439, 1715, 890, 754, 858, 1418], fc_dist=[7877.0, 2534.0, 730.0, 375.0, 59.0]), Stats(cnt=16534.0, diff='13', fit_diff=13.412406903757972, avg=97.52620735454207, avg_dx=1814.7217854118785, std_dev=2.5433036930848902, dist=[60, 33, 60, 39, 69, 602, 964, 2013, 1721, 2293, 1549, 1673, 3151, 2307], fc_dist=[12261.0, 3383.0, 677.0, 185.0, 28.0]), None] diff=[]'''

        # 选出is_new=False的records
        self.sdBest = [i for i in self.records if mai.total_list.by_id(str(i.song_id)).basic_info.is_new == False]
        self.dxBest = [i for i in self.records if mai.total_list.by_id(str(i.song_id)).basic_info.is_new == True]

        self.sdBest = [i for i in self.sdBest if i.achievements < 97]
        self.dxBest = [i for i in self.dxBest if i.achievements < 97]

        #按ra从高到低排序，取前35首
        self.sdBest = sorted(self.sdBest, key=lambda x: x.ra, reverse=True)[:35]
        self.dxBest = sorted(self.dxBest, key=lambda x: x.ra, reverse=True)[:15]

        # 把sdBest和dxBest的所有歌曲ra加起来
        self.Rating = sum([_.ra for _ in self.sdBest]) + sum([_.ra for _ in self.dxBest])

    def _findRaPic(self) -> str:
        if self.Rating < 1000:
            num = '01'
        elif self.Rating < 2000:
            num = '02'
        elif self.Rating < 4000:
            num = '03'
        elif self.Rating < 7000:
            num = '04'
        elif self.Rating < 10000:
            num = '05'
        elif self.Rating < 12000:
            num = '06'
        elif self.Rating < 13000:
            num = '07'
        elif self.Rating < 14000:
            num = '08'
        elif self.Rating < 14500:
            num = '09'
        elif self.Rating < 15000:
            num = '10'
        else:
            num = '11'
        return f'UI_CMN_DXRating_{num}.png'


    def _findMatchLevel(self) -> str:
        if self.addRating <= 10:
            num = f'{self.addRating:02d}'
        else:
            num = f'{self.addRating + 1:02d}'
        return f'UI_DNM_DaniPlate_{num}.png'


    async def whiledraw(self, data: List[ChartInfo], type: bool) -> Image.Image:
        # y为第一排纵向坐标，dy为各排间距
        y = 430 if type else 1670
        dy = 170

        TEXT_COLOR = [(255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (103, 20, 141, 255)]
        DXSTAR_DEST = [0, 330, 320, 310, 300, 290]
        

        for num, info in enumerate(data): 
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            cover = Image.open(await download_music_pictrue(info.song_id)).resize((135, 135))
            version = Image.open(maimaidir / f'UI_RSL_MBase_Parts_{info.type}.png').resize((55, 19))
            rate = Image.open(maimaidir / f'UI_TTR_Rank_{score_Rank[info.rate]}.png').resize((95, 44))

            self._im.alpha_composite(self._diff[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 5, y + 5))
            self._im.alpha_composite(version, (x + 80, y + 141))
            self._im.alpha_composite(rate, (x + 150, y + 98))
            if info.fc:
                fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[info.fc]}.png').resize((45, 45))
                self._im.alpha_composite(fc, (x + 260, y + 98))
            if info.fs:
                fs = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fsl[info.fs]}.png').resize((45, 45))
                self._im.alpha_composite(fs, (x + 315, y + 98))
            
            dxscore = sum(mai.total_list.by_id(str(info.song_id)).charts[info.level_index].notes) * 3
            diff_sum_dx = info.dxScore / dxscore * 100
            dxtype, dxnum = dxScore(diff_sum_dx)
            for _ in range(dxnum):
                self._im.alpha_composite(self.dxstar[dxtype], (x + DXSTAR_DEST[dxnum] + 20 * _ + 2, y + 60))

            y8 = 0
            if info.fc == 'fcp':
                y8 += 1
            elif info.fc == 'ap' or info.fc == 'app':
                y8 += 2
            if info.achievements >= 100.98:
                y8 += 3
            elif info.achievements >= 100.95:
                y8 += 2
            elif info.achievements >= 100.9:
                y8 += 1
            y8 += max(dxnum - 2, 0)

            yrating = info.ds * min((max(100*(info.achievements-100), 0)), (100 * info.dxScore / dxscore))/100

            self._im.alpha_composite(Image.open(maimaidir / 'yang.png').resize((18,18)), (x + 346, y + 78))

            self._tb.draw(x + 40, y + 148, 20, info.song_id, anchor='mm')
            title = info.title
            if coloumWidth(title) > 14:
                title = changeColumnWidth(title, 12) + '...'
            self._siyuan.draw(x + 155, y + 20, 18, title, TEXT_COLOR[info.level_index], anchor='lm')
            p, s = f'{info.achievements:.4f}'.split('.')
            r = self._tb.get_box(p, 32)
            self._tb.draw(x + 155, y + 70, 32, p, TEXT_COLOR[info.level_index], anchor='ld')
            self._tb.draw(x + 155 + r[2], y + 68, 22, f'.{s}%', TEXT_COLOR[info.level_index], anchor='ld')
            self._tb.draw(x + 340, y + 50, 16, f'{info.dxScore}/{dxscore}', TEXT_COLOR[info.level_index], anchor='mm')
            self._tb.draw(x + 155, y + 80, 22, f'{info.ds} -> {info.ra}', TEXT_COLOR[info.level_index], anchor='lm')
            self._tb.draw(x + 320, y + 85, 15, f'{yrating:.3f}', TEXT_COLOR[info.level_index], anchor='mm')
            self._tb.draw(x + 372, y + 85, 16, f'x{y8}', TEXT_COLOR[info.level_index], anchor='mm')
            self._tb.draw(x + 338, y + 20, 23, f'No.{num + 1}', TEXT_COLOR[info.level_index], anchor='mm')


    async def draw(self):
        
        basic = Image.open(maimaidir / 'b40_score_basic.png')
        advanced = Image.open(maimaidir / 'b40_score_advanced.png')
        expert = Image.open(maimaidir / 'b40_score_expert.png')
        master = Image.open(maimaidir / 'b40_score_master.png')
        remaster = Image.open(maimaidir / 'b40_score_remaster.png')
        logo = Image.open(maimaidir / 'logo.png').resize((378, 172))
        dx_rating = Image.open(maimaidir / self._findRaPic()).resize((300, 59))
        Name = Image.open(maimaidir / 'Name.png')
        MatchLevel = Image.open(maimaidir / self._findMatchLevel()).resize((134, 55))
        ClassLevel = Image.open(maimaidir / 'UI_FBR_Class_00.png').resize((144, 87))
        rating = Image.open(maimaidir / 'UI_CMN_Shougou_Rainbow.png').resize((454, 50))
        self._diff = [basic, advanced, expert, master, remaster]
        self.dxstar = [Image.open(maimaidir / f'UI_RSL_DXScore_Star_0{_ + 1}.png').resize((18, 18)) for _ in range(3)]

        # 作图
        self._im = Image.open(maimaidir / 'b40_bg.png').convert('RGBA')

        self._im.alpha_composite(logo, (5, 130))
        if self.plate:
            plate = Image.open(maimaidir / f'{self.plate}.png').resize((1420, 230))
        else:
            plate = Image.open(maimaidir / 'UI_Plate_300101.png').resize((1420, 230))
        self._im.alpha_composite(plate, (390, 100))
        icon = Image.open(maimaidir / 'UI_Icon_309503.png').resize((214, 214))
        self._im.alpha_composite(icon, (398, 108))
        if self.qqId:
            try:
                async with httpx.AsyncClient() as client:
                    res = await client.get(f'http://q1.qlogo.cn/g?b=qq&nk={self.qqId}&s=100')
                    qqLogo = Image.open(BytesIO(res.content))
                self._im.alpha_composite(Image.new('RGBA', (203, 203), (255, 255, 255, 255)), (404, 114))
                self._im.alpha_composite(qqLogo.convert('RGBA').resize((201, 201)), (405, 115))
            except Exception:
                pass
        self._im.alpha_composite(dx_rating, (620, 122))
        Rating = f'{self.Rating:05d}'
        for n, i in enumerate(Rating):
            self._im.alpha_composite(Image.open(maimaidir / f'UI_NUM_Drating_{i}.png').resize((28, 34)), (760 + 23 * n, 137))
        self._im.alpha_composite(Name, (620, 200))
        self._im.alpha_composite(MatchLevel, (935, 205))
        self._im.alpha_composite(ClassLevel, (926, 105))
        self._im.alpha_composite(rating, (620, 275))

        text_im = ImageDraw.Draw(self._im)
        self._meiryo = DrawText(text_im, MEIRYO)
        self._siyuan = DrawText(text_im, SIYUAN)
        self._tb = DrawText(text_im, TBFONT)

        self._siyuan.draw(635, 235, 40, self.userName, (0, 0, 0, 255), 'lm')
        sdrating, dxrating = sum([_.ra for _ in self.sdBest]), sum([_.ra for _ in self.dxBest])
        self._tb.draw(847, 295, 26, f'(Below S) B35: {sdrating} + B15: {dxrating} = {self.Rating}', (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255))
        self._siyuan.draw(1115, 2352, 20, f'（杨氏rating计算方式为：谱面定数*min(100*(达成率-100),dx分/总dx分)，最低为0；8分法计算方式为：FC+，AP，100.9，100.95，100.98，三星，四星，五星各计一分。仅供娱乐，请玩家合理参考，解释权归杨树森6所有。）', (103, 20, 141, 255), 'mm', 3, (255, 255, 255, 255))
        self._siyuan.draw(1115, 2380, 20, f'改编自：Yuri-YuzuChaN，作者：宇航员Dale，Bot：宇航员猫娘', (103, 20, 141, 255), 'mm', 3, (255, 255, 255, 255))
        # self._meiryo.draw(900, 2365, 35, f'Designed by Yuri-YuzuChaN & BlueDeer233 | Generated by {maiconfig.botName} BOT', (103, 20, 141, 255), 'mm', 3, (255, 255, 255, 255))

        await self.whiledraw(self.sdBest, True)
        await self.whiledraw(self.dxBest, False)

        return self._im.resize((1760, 1920))


def dxScore(dx: int) -> Tuple[int, int]:
    """
    返回值为 `Tuple`： `(星星种类，数量)`
    """
    if dx <= 85:
        result = (0, 0)
    elif dx <= 90:
        result = (0, 1)
    elif dx <= 93:
        result = (0, 2)
    elif dx <= 95:
        result = (1, 3)
    elif dx <= 97:
        result = (1, 4)
    else:
        result = (2, 5)
    return result


def getCharWidth(o) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloumWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += getCharWidth(ord(ch))
    return res


def changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)


def computeRa(ds: float, achievement: float, israte: bool = False) -> Union[int, Tuple[int, str]]:
    if achievement < 50:
        baseRa = 7.0
        rate = 'D'
    elif achievement < 60:
        baseRa = 8.0
        rate = 'C'
    elif achievement < 70:
        baseRa = 9.6
        rate = 'B'
    elif achievement < 75:
        baseRa = 11.2
        rate = 'BB'
    elif achievement < 80:
        baseRa = 12.0
        rate = 'BBB'
    elif achievement < 90:
        baseRa = 13.6
        rate = 'A'
    elif achievement < 94:
        baseRa = 15.2
        rate = 'AA'
    elif achievement < 97:
        baseRa = 16.8
        rate = 'AAA'
    elif achievement < 98:
        baseRa = 20.0
        rate = 'S'
    elif achievement < 99:
        baseRa = 20.3
        rate = 'Sp'
    elif achievement < 99.5:
        baseRa = 20.8
        rate = 'SS'
    elif achievement < 100:
        baseRa = 21.1
        rate = 'SSp'
    elif achievement < 100.5:
        baseRa = 21.6
        rate = 'SSS'
    else:
        baseRa = 22.4
        rate = 'SSSp'
    
    if israte:
        data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
    else:
        data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

    return data

def generateAchievementList(ds: float):
    _achievementList = []
    for index, acc in enumerate(achievementList):
        if index == len(achievementList) - 1:
            continue
        _achievementList.append(acc)
        c_acc = (computeRa(ds, achievementList[index]) + 1) / ds / BaseRaSpp[index + 1] * 100
        c_acc = math.ceil(c_acc * 10000) / 10000
        while c_acc < achievementList[index + 1]:
            _achievementList.append(c_acc)
            c_acc = (computeRa(ds, c_acc + 0.0001) + 1) / ds / BaseRaSpp[index + 1] * 100
            c_acc = math.ceil(c_acc * 10000) / 10000
    _achievementList.append(100.5)
    return _achievementList

async def generate_aaa_50(qqid: Optional[int] = None, username: Optional[str] = None) -> str:
    try:
        if username:
            qqid = None
            
        version = list(set(_v for _v in list(plate_to_version.values())))
        obj = await maiApi.query_user_dev(qqid=qqid, username=username)
        '''
        songlist = []
        for song in obj['records']:
            if song['fc'] == 'ap' or song['fc'] == 'app':
                songlist.append(song)
        songlist = sorted(songlist, key=lambda x: x['achievements'], reverse=True)[:50]
        msg = ''
        # 格式： {'achievements': 100.9732, 'ds': 12.0, 'dxScore': 1514, 'fc': 'ap', 'fs': '', 'level': '12', 'level_index': 3, 'level_label': 'Master', 'ra': 270, 'rate': 'sssp', 'song_id': 11513, 'title': '回る空うさぎ', 'type': 'DX'}
        for idx in enumerate(sorted(songlist, key=lambda x: x['achievements'], reverse=True)):
            msg += f"曲名: {idx[1]['title']}\n"
            print(idx[1]['title'])
            
            msg += f"等级: {idx[1]['level']}\n"
            msg += f"难度: {idx[1]['level_label']}\n"
            msg += f"成绩: {idx[1]['achievements']}\n"
            msg += f"dx分: {idx[1]['dxScore']}\n"
            msg += f"rating: {idx[1]['ra']}\n"
            msg += f"评级: {idx[1]['rate']}\n"
            print(idx[1])
            # for key, value in idx[1].items():
            #    msg += f"{key}: {value}\n"
            msg += "------------------------\n"
        
        for song in obj:
            if song['fc'] == 'ap' or song['fc'] == 'app':
                songlist.append(song)
        songlist = sorted(songlist, key=lambda x: x['achievements'], reverse=True)[:50]
        msg = ''
        for idx in enumerate(sorted(songlist, key=lambda x: x['achievements'], reverse=True)):
            msg += f"歌曲 {idx[0]}:\n"
            msg += f"曲名: {idx[1]['title']}\n"
            msg += f"等级: {idx[1]['level']}\n"
            msg += f"成绩: {idx[1]['achievements']}\n"
            print(idx[1])
            # for key, value in idx[1].items():
            #    msg += f"{key}: {value}\n"
            msg += "------------------------\n"
        
        '''
        # obj1 = await maiApi.query_user('plate', qqid=qqid, username=username)

        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        msg = MessageSegment.image(image_to_bytesio(pic))
    except UserNotFoundError as e:
        msg = str(e)
    except UserDisabledQueryError as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg