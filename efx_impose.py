from wall_common import *
import TkEasyGUI as sg
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps #, ImageTk, ImageChops
import numpy as np
#import math
import datetime
import copy
import io
import os
import os.path as pa
import filedialog as fdi
#import inspect
import calendar
import textwrap
import tkinter as tk
#from tkinter import filedialog
from fontTools.ttLib import TTFont
import glob
import zipfile
import threading

SysFont_Dir = r'c:\Windows\Fonts'
Font_Dir = SysFont_Dir
FONT_EXT=('.ttf', '.otf', '.ttc')  #, '.fon')
Image_Files = [('PNG','*.png'),('JPG','*.jpg'),('Any','*.*'),]
Preview_Size = (560,315)
POS = ['nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se']
GRADTYPE = ['None', 'Linear', 'Stripe']
BgMenu = ['FG', 'BG', 'File', 'Plain']
BgInd = ['*frontimage*', '*internal*', '*file*', '*plain*']
Mask_Code = {'cal': 'calendar', 'txt': 'text', 'lor': 'lorem'}
T_FX = ['None', 'Layerd', 'HollowStack']

calendar_preserv = {'shade': {'shift':8, 'alpha':40, 'blur':10, 'enbri':0.0},
                    'font': {'key':None, 'size':64, 'fontdic':{}},
                    'common': {'pos':8, 'lspc':1.4, 'spc':1.3, 'half':238,
                               'grad':0, 'mid':35, 'xpad':32, 'ypad':60},
                    'calendar': {'year':2026, 'month':1, 'multi':1,
                                 'wend':1, 'holi':1, 'tate':0},
                    'text': {'msg1$': '','msg2$': '',
                             'effect':0, 'stack':0, 'upper':0},
                    'lorem': {'width':30},
                    }

Init_Color = (48, 128, 192)
FontList_Size = 8
ExceptList = ['CRCGHankoin.ttc']  # 読み込み時エラーが発生するFONTファイル
SP_HOLIDAY = [(2,23)]  # 追加祝日 天皇誕生日など(ハッピーマンデー系はFFS)
WDAY_INT = 0xff
PADDING = 32
LOREM = 'Lorem ipsum dolor sit amet, consectetur adipiscing '+\
        'elit, sed do eiusmod tempor incididunt ut labore et '+\
        'dolore magna aliqua. Ut enim ad minim veniam, quis '+\
        'nostrud exercitation ullamco laboris nisi ut aliquip '+\
        'ex ea commodo consequat. Duis aute irure dolor in '+\
        'reprehenderit in voluptate velit esse cillum dolore '+\
        'eu fugiat nulla pariatur. Excepteur sint occaecat '+\
        'cupidatat non proident, sunt in culpa qui officia '+\
        'deserunt mollit anim id est laborum.'

def intro(efxlist: EfxModules, module_name):
    efxlist.add_module(module_name, 'カレンダー貼り付け',
                       {'proc': ['add_calendar',
                                 ]
                        })
    # proc: [(<function>, <usable_subs>),...]
    return module_name


# 保存パラメータがあれば返す
# =========================
def prevset(name, default, funcname, lo=None, hi=None):
    retv = calendar_preserv.get(funcname, {}).get(name, default)
    
    if lo is not None:
        retv = max(lo, retv)
    if hi is not None:
        retv = min(retv, hi)
    
    return retv


def storehist(name, value, funcname):
    if calendar_preserv.get(funcname,None) is None:
        calendar_preserv[funcname] = {}
    calendar_preserv[funcname][name] = value
    return


font_data_cache = {}   # ZIP展開済み bytes
font_info_cache = {}   # フォント情報


# fontファイルのリストを取得する
def list_fonts(font_dir):
    fonts = []

    for file in os.listdir(font_dir):
        if file.lower().endswith(FONT_EXT):
            if file in ExceptList:
                continue
            fonts.append((os.path.join(font_dir,file), None))

        elif file.lower().endswith(".zip"):
            zipname = os.path.join(font_dir, file)
            try:
                with zipfile.ZipFile(zipname) as z:
                    for name in z.namelist():
                        if name.lower().endswith(FONT_EXT):
                            if name in ExceptList:
                                continue
                            fonts.append((zipname,name))
            except Exception:
                continue
    return sorted(fonts)


# fontを展開する
def open_font_source(source):
    path, inner = source

    if inner is None:
        return path

    key = (path, inner)

    if key not in font_data_cache:
        try:
            with zipfile.ZipFile(path) as z:
                font_data_cache[key] = z.read(inner)
        except Exception as e:
            print(f'Skipped {path} / {inner} as {e}')
            return path

    return io.BytesIO(font_data_cache[key])


# fontファイル名(base)の取り出し
def basenm(source):
    if isinstance(source, str):
        return pa.basename(source)
    path, inner = source
    if inner:
        return pa.basename(inner)
    return pa.basename(path)
    

# fontの情報を返す
def get_font_info(source, textsize=48):
    """TTF/OTF/TTC の内部名とスタイルを返す。非対応なら None。
    戻り値: [(index, family, jp_family, style), ...]
    """
    if source in font_info_cache:
        return font_info_cache[source]

    faces = []
    index = 0

    while True:
        try:
            # PIL でフォントを開く
            font = ImageFont.truetype(open_font_source(source), textsize, index=index)
            family, style = font.getname()

            # nameID=1 の日本語名を取得
            try:
                tt = TTFont(open_font_source(source), fontNumber=index)
                jp_family = None
                fallback = None

                for rec in tt["name"].names:
                    if rec.nameID != 1:
                        continue
                    try:
                        name = rec.toUnicode()
                    except Exception:
                        continue

                    fallback = fallback or name
                    if (rec.platformID, rec.langID) in ((3, 0x0411), (0, 0)):
                        jp_family = name
                        break

                jp_family = jp_family or fallback or family

            except Exception:
                jp_family = family

            faces.append((index, family, jp_family, style))
            index += 1

        except OSError:
            break

    font_info_cache[source] = faces or None
    
    return font_info_cache[source]


# fontlistの再取得
def make_font_dic(directory):
    global font_data_cache, font_info_cache
    font_data_cache = {}   # data_cache クリア
    font_info_cache = {}   # フォント情報 クリア

    fonts = list_fonts(directory)
    fflist = []
    for source in fonts:
        info = get_font_info(source)
        if info is None:
            #print(f'Purge {source}.')
            continue
        for ff in info:
            idx, family, jp_family, face = ff
            fflist.append([jp_family, face, family, source, idx])
    fflist = sorted(fflist)

    font_key = []
    font_dic = {}
    for fontface in fflist:
        key = f'{fontface[0]}|{fontface[1]}'
        font_dic[key] = fontface
        font_key.append(key)

    return font_key, font_dic


# textを指定fontでビットマップに書き出す
def text_image(text, source, index=0, size=48, color=255):
    temp_w = int(len(text) * size * 4)
    temp_h = int(size * 4)
    
    img = Image.new('L', (temp_w, temp_h), 0)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(open_font_source(source), size,
                                  index=index)
        draw.text((size, size*2), text, font=font, fill=color)
    except Exception:
        draw.text((size, size*2), text, fill=color)
    
    try:
        x1,y1,x2,y2 = img.getbbox()
    except TypeError:
        #img.show()
        # x1,y1,x2,y2 = 0,0,int(size*len(text)),int(size*1.5)
        x1,y1,x2,y2 = 0,0,len(text),1
    
    img = img.crop((x1, y1, x2, y2))

    return img  # was ImageTk.PhotoImage(img)


# ----------
#  MASK functions
# ----------
# Calendar
def calendar_mask():
    # calendar param
    year = prevset('year', None, 'calendar')
    month = prevset('month', None, 'calendar')
    multi = prevset('multi', None, 'calendar')
    weekend = prevset('wend', None, 'calendar') == 1
    holiflag = prevset('holi', None, 'calendar') == 1
    tate = prevset('tate', None, 'calendar') == 1

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    size = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]
    # print(fkey, fdic[fkey])  #####
    # print(calendar_preserv['calendar'], '\n', year, month, holiflag)
    lspc = prevset('lspc', None, 'common')
    spc = int(lspc*size)

    if 0 < multi < 4:
        # print('caller', year, month, multi)
        if tate and multi > 1:
            calimg = multi_calendar(year, month, 1, source, index, size,
                                    weekend=weekend, holiday=holiflag)
            for i in range(multi-1):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                addimg = multi_calendar(year, month, 1, source, index, size,
                                        weekend=weekend, holiday=holiflag)
                w1,h1 = calimg.size
                w2,h2 = addimg.size
                newimg = Image.new('L', (max(w1,w2), h1+h2+spc), 0)
                newimg.paste(calimg, (0,0))
                newimg.paste(addimg, (0,h1+spc))
                calimg = newimg
        else:
            calimg = multi_calendar(year, month, multi, source, index, size,
                                    weekend=weekend, holiday=holiflag)
    elif 3 < multi < 13:

        wi = int(multi-0.5) // 3
        #wi = -(-multi // 3)
        calimg = multi_calendar(year, month, 3, source, index, size,
                                weekend=weekend, holiday=holiflag)
        for j in range(wi):
            month += 3
            if month > 12:
                month = month % 12
                year += 1
            sur = min(multi - (j+1)*3, 3)
            # print('add', year, month, sur, 'wi=', j)
            addimg = multi_calendar(year, month, sur, source, index, size,
                                weekend=weekend, holiday=holiflag)
            w1,h1 = calimg.size
            w2,h2 = addimg.size
            newimg = Image.new('L', (max(w1,w2), h1+h2+spc), 0)
            newimg.paste(calimg, (0,0))
            newimg.paste(addimg, (0,h1+spc))
            calimg = newimg
    else:
        calimg = monthly_calendar(year, month, source, index, size,
                     weekend=True, holiday=True)

    return calimg.crop(calimg.getbbox())


# 複数月横並び生成
def multi_calendar(year, month, num, fontsrc, index, size,
                   weekend=True, holiday=True):
    """numカ月分の横並びカレンダーユニット"""
    dspc = prevset('spc', None, 'common')
    spc = int(dspc*size)
    
    calimg = monthly_calendar(year, month, fontsrc, index, size,
                 weekend, holiday)

    for mm in range(1,num):
        month += 1
        if month > 12:
            month = 1
            year += 1
        addimg = monthly_calendar(year, month, fontsrc, index, size,
                                  weekend, holiday)
        w1,h1 = calimg.size
        w2,h2 = addimg.size
        newimg = Image.new('L', (w1+w2+spc, max(h1,h2)), 0)
        newimg.paste(calimg, (0,0))
        newimg.paste(addimg, (w1+spc,0))
        calimg = newimg
            
    return calimg


# 1 month
def monthly_calendar(year, month, fontsrc, index, size,
                     weekend=True, holiday=True):
    """1カ月分のカレンダーユニット"""
    
    half = prevset('half', None, 'common')
    dspc = prevset('spc', None, 'common')
    lspc = prevset('lspc', None, 'common')
    grad = prevset('grad', None, 'common', lo=0)
    mid = prevset('mid', None, 'common', lo=0, hi=100)

    body = calendar_body(year, month)
    if holiday:
        holidays = holiday_map(year)[month-1]
    else:
        holidays = []

    # test_cell
    tim = text_image(' 39', fontsrc, index=index, size=size, color=WDAY_INT)
    std_w, std_h = tim.size
    std_w = int(std_w * dspc)
    std_h = int(std_h * lspc)
    hdr = text_image(f'{year}/{month}', fontsrc, index=index,
                     size=int(size*1.2), color=WDAY_INT)
    hdr_w, hdr_h = hdr.size

    if grad == 1:  # gradation linear
        maskhdr = linear_line_mask(hdr_w, hdr_h, mid)
        maskpat = linear_line_mask(std_w*7, std_h, mid)
    elif grad == 2:  # gradation stripe line
        maskhdr = stripe_line_mask(hdr_w, hdr_h, mid)
        maskpat = stripe_line_mask(std_w*7, std_h, mid)
    else:
        maskhdr = Image.new('L', (hdr_w, hdr_h), 255)
        maskpat = Image.new('L', (std_w*7, std_h), 255)
        
    calimg = Image.new('L', (std_w*7, int(std_h*6.5)+hdr_h), 0)
    calimg.paste(maskhdr, ((std_w*7-hdr_w)//2,0), hdr)


    for j, line in enumerate(body):
        lpat = Image.new('L', (std_w*7, std_h), 0)
        for i, day in enumerate(line):
            if day is None:
                continue
            color = WDAY_INT
            if weekend and i in (0, 6):
                color = half
            elif holiday and day in holidays:
                color = half
            tim = text_image(f'{day}', fontsrc, index=index, size=size,
                             color=color)
            pos = ((i+1)*std_w-tim.width, 0)
            lpat.paste(tim, pos, tim)

        calimg.paste(maskpat, (0, int((j+0.5)*std_h)+hdr_h), lpat)

    return calimg    
    

# 濃淡グラデーション
def linear_line_mask(width, height, pos=33):
    """リニアグラデーション(固定区間あり)"""
    h1 = int(height * pos / 100)
    h2 = height - h1
    start = 255
    stop = 128
    
    top = np.full((h1, width), start, dtype=np.uint8)
    bottom = np.linspace(start, stop, h2, dtype=np.uint8).reshape(h2, 1)
    bottom = np.repeat(bottom, width, axis=1)
    hm = np.concatenate([top, bottom], axis=0)
    
    return Image.fromarray(hm, mode='L')


# 線幅グラデーション
def stripe_line_mask(width, height, fade=30, pitch=10):
    """フェードストライプ pitch=分割数"""
    bandw = height // pitch  # 白黒セット幅
    fade_r = (100 - fade) / 100 #if fade < 60 else 0.4
    img = np.zeros((height, width), dtype=np.uint8)

    # 各セットの開始位置
    y = 0

    for i in range(pitch):
        # 線形補間で白黒幅を決定
        t = i / (pitch - 1)
        w_white = int(bandw * (1 - fade_r*t))
        w_black = bandw - w_white

        # 白黒ストライプを縦方向に描画
        # 白ストライプ
        img[y:y+w_white, :] = 255
        # 黒ストライプ
        img[y+w_white:y+bandw, :] = 0

        y += bandw

    return Image.fromarray(img, mode='L')


# カレンダー文字列生成
def calendar_body(year, month, firstday=calendar.SUNDAY):
    """カレンダー配列 firstday変更可"""
    
    calendar.setfirstweekday(firstday)
    cal = calendar.monthcalendar(year, month)
    cal = [[d or None for d in week] for week in cal]

    return cal

# 春分・秋分（祝日計算用近似式）
def shunbun(y):
    return int(20.8431 + 0.242194*(y-1980)) - (y-1980)//4

def shuubun(y):
    return int(23.2488 + 0.242194*(y-1980)) - (y-1980)//4

# 振替休日（既に祝日なら追加しない）
def furikae(date, holidays):
    if date.weekday() != 6:  # Sunday
        return
    next_day = date + datetime.timedelta(days=1)

    # 連続して祝日ならさらに翌日へ
    while next_day in holidays:
        next_day += datetime.timedelta(days=1)

    holidays.append(next_day)

# 国民の休日（祝日に挟まれた平日）
def kokumin_no_kyujitsu(holidays):
    extra = []
    hs = set(holidays)

    for h in holidays:
        next_day = h + datetime.timedelta(days=1)
        # 祝日 → 平日 → 祝日 の平日を追加
        if (next_day.weekday() < 5) and (next_day not in hs):
            if (h in hs) and ((next_day + datetime.timedelta(days=1)) in hs):
                extra.append(next_day)

    return extra

# 祝日リスト holiday_map(year)[month-1][] でその月の祝日リスト(振替込み)を取得
def holiday_map(year):
    holidays = []

    # 固定祝日
    holidays.append(datetime.date(year, 1, 1))   # 元日
    holidays.append(datetime.date(year, 2, 11))  # 建国記念の日
    holidays.append(datetime.date(year, 4, 29))  # 昭和の日
    holidays.append(datetime.date(year, 5, 3))   # 憲法記念日
    holidays.append(datetime.date(year, 5, 4))   # みどりの日
    holidays.append(datetime.date(year, 5, 5))   # こどもの日
    holidays.append(datetime.date(year, 8, 11))  # 山の日
    holidays.append(datetime.date(year, 11, 3))  # 文化の日
    holidays.append(datetime.date(year, 11, 23)) # 勤労感謝の日

    # 春分・秋分
    holidays.append(datetime.date(year, 3, shunbun(year)))
    holidays.append(datetime.date(year, 9, shuubun(year)))

    # ハッピーマンデー制度
    def nth_monday(month, n):
        d = datetime.date(year, month, 1)
        while d.weekday() != 0:  # Monday
            d += datetime.timedelta(days=1)
        return d + datetime.timedelta(days=7*(n-1))

    holidays.append(nth_monday(1, 2))  # 成人の日
    holidays.append(nth_monday(7, 3))  # 海の日
    holidays.append(nth_monday(9, 3))  # 敬老の日
    holidays.append(nth_monday(10, 2)) # スポーツの日

    for sp in SP_HOLIDAY:
        holidays.append(datetime.date(year, sp[0], sp[1]))

    # 国民の休日
    holidays += kokumin_no_kyujitsu(holidays)

    # 振替休日
    base = holidays.copy()
    for h in base:
        furikae(h, holidays)

    # 重複除去
    holidays = sorted(set(holidays))

    # 月毎の配列に変換
    holiday_map = [[] for _ in range(12)]
    for d in holidays:
        holiday_map[d.month - 1].append(d.day)

    return holiday_map


# ----------
# Text
def text_mask():
    line1 = prevset('msg1$', None, 'text')
    line2 = prevset('msg2$', None, 'text')
    lines = [line1, line2]

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    fsize = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]

    lspc = prevset('lspc', None, 'common')
    spc = int(fsize * lspc)
    grad = prevset('grad', None, 'common', lo=0)
    mid = prevset('mid', None, 'common', lo=0, hi=100)
    pos = prevset('pos', None, 'common', lo=0, hi=8)
    h_align = pos % 3  # 0:left 1:center 2:right

    limgs = []
    lhtotal = 0
    spcmax = 0
    maxw = 1
    for ltxt in lines:
        if ltxt == '' or ltxt is None:
            if limgs == []:
                ltxt = ' '
            else:
                continue
        # print(f'{ltxt},{ord(ltxt[0])}')
        limg = text_image(ltxt, source, index=index,
                          size=fsize, color=WDAY_INT)
        dimg = limg.crop(limg.getbbox())
        w1,h1 = limg.size
        if w1 == 0:
            dimg = Image.new('L',(10,fsize//4),0)
            
        if grad == 1:  # gradation linear
            maskpat = linear_line_mask(w1, h1, mid)
        elif grad == 2:  # gradation stripe line
            maskpat = stripe_line_mask(w1, h1, mid)
        else:
            maskpat = Image.new('L', (w1, h1), 255)

        img = Image.new('L', (w1, h1), 0)
        img.paste(maskpat, (0,0), dimg)

        limgs.append(img)
        lhtotal += max(h1+1, spc)
        spcmax = max(1, spc-h1)
        #lhlist.append(h1)
        maxw = max(maxw, w1)

    #totalh = sum(lhlist)+(len(limgs)-1)*spc
    #img = Image.new('L', (maxw, totalh), 0)

    img = Image.new('L', (maxw, lhtotal), 0)
    y = 0
    for l in limgs:
        lw, lh = l.size
        if h_align == 2:
            x = maxw - lw
        elif h_align == 1:
            x = int((maxw - lw)/2)
        else:
            x = 0
        img.paste(l, (x,y))
        y = y+max(lh+1,spc)

    img = img.crop(img.getbbox())
    effect = prevset('effect', None, 'text')
    if effect == 1:
        stack = prevset('stack', None, 'text', lo=1)  #, hi=12)
        img = layered_np(img, stack, thickness=11)
        img = img.crop(img.getbbox())
        storehist('stack', stack, 'text')
    if effect == 2:
        lower = prevset('stack', None, 'text', lo=0)
        upper = prevset('upper', None, 'text', lo=0)
        img, img2 = stacker(img, upper, lower, spcmax)
        return img, img2
    
    return img, None  # mask(shadow enable), mask2(non shadow)


# layered outline typography
def old_layered(img, step,thickness=8):
    #step -= 1
    base = thick(img, (step+1)*thickness)
    bw, bh = base.size
    base_np = np.array(base.convert('L'), dtype=np.uint8)
    for i in range(step):
        s = (step - i)*thickness
        addim = thick(img,s)
        base = Image.new('L',(bw, bh),0)
        ix, iy = (bw-addim.width)//2, (bh-addim.height)//2
        base.paste(addim, (ix, iy))
        add_np = np.array(base,dtype=np.uint8)
        base_np = np.bitwise_xor(base_np, add_np)

    base = Image.new('L',(bw, bh),0)
    ix, iy = (bw-img.width)//2, (bh-img.height)//2
    base.paste(img, (ix, iy))
    add_np = np.array(base,dtype=np.uint8)
    base_np = np.bitwise_xor(base_np, add_np)

    output = Image.fromarray(base_np).convert('L')
    return output


# layered outline typography
def layered_np(img, step, thickness=8):
    """layeredのNumPy高速版"""
    iw, ih = img.size

    # layered() で最初に作られる thick() の幅
    max_width = (step + 1) * thickness
    if max_width % 2 == 0:
        max_width += 1

    # 最外周のthick()と同じサイズのキャンバスを作る
    bw = iw + max_width * 2
    bh = ih + max_width * 2

    src = np.asarray(img, dtype=np.uint8)

    # 元画像を最大キャンバスの中央へ配置
    base = np.zeros((bh, bw), dtype=np.uint8)
    base[
        max_width:max_width + ih,
        max_width:max_width + iw
    ] = src

    # FIND_EDGES は一度だけ実行
    edge_img = Image.fromarray(base, mode='L').filter(
        ImageFilter.FIND_EDGES
    )
    edge = np.asarray(edge_img, dtype=np.uint8)

    result = np.zeros((bh, bw), dtype=np.uint8)
    for i in range(step):
        width = (step - i) * thickness

        if width % 2 == 0:
            width += 1

        lw = iw + width * 2 # thick(img, width)サイズ
        lh = ih + width * 2
        ix = (bw - lw) // 2
        iy = (bh - lh) // 2

        # FIND_EDGES済み画像から対応部分取得
        e = edge[iy:iy + lh, ix:ix + lw]

        contour = _maxfilter_np(e, width)
        layer = np.maximum(
            base[iy:iy + lh, ix:ix + lw],
            contour
        )
        result[iy:iy + lh, ix:ix + lw] ^= layer  # XOR

    ix = (bw - iw) // 2
    iy = (bh - ih) // 2
    result[iy:iy + ih, ix:ix + iw] ^= src  # 元画像XOR

    return Image.fromarray(result, mode='L')
        

# 水平方向maxfilter
def _maxfilter_1d_horizontal(a, size):
    if size <= 1:
        return a

    r = size // 2
    p = np.pad(a, ((0, 0), (r, r)), mode='constant')
    h, w = p.shape
    nb = (w + size - 1) // size
    ww = nb * size

    if ww != w:
        p = np.pad(p, ((0, 0), (0, ww - w)), mode='constant')

    q = p.reshape(h, nb, size)

    left = np.maximum.accumulate(q, axis=2)
    right = np.maximum.accumulate(q[..., ::-1],axis=2)[..., ::-1]

    left = left.reshape(h, ww)
    right = right.reshape(h, ww)

    try:
        return np.maximum(right[:, :a.shape[1]],
                          left[:, size - 1:size - 1 + a.shape[1]])
    except ValueError:
        return a


# 垂直方向maxfilter
def _maxfilter_1d_vertical(a, size):
    if size <= 1:
        return a

    r = size // 2
    p = np.pad(a, ((r, r), (0, 0)), mode='constant')
    h, w = p.shape
    nb = (h + size - 1) // size
    hh = nb * size

    if hh != h:
        p = np.pad(p, ((0, hh - h), (0, 0)), mode='constant')

    q = p.reshape(nb, size, w)

    left = np.maximum.accumulate(q, axis=1)
    right = np.maximum.accumulate(q[:, ::-1, :], axis=1)[:, ::-1, :]

    left = left.reshape(hh, w)
    right = right.reshape(hh, w)

    try:
        return np.maximum(right[:a.shape[0], :],
                          left[size:size+a.shape[0], :])
    except ValueError:
        return a

# MaxFilterをnumpyで代替、高速化
def _maxfilter_np(img, size):
    """PIL MaxFilter相当の高速NumPy版。"""
    if size <= 1:
        return img
    if size % 2 == 0:
        size += 1
    tmp = _maxfilter_1d_horizontal(img, size)

    return _maxfilter_1d_vertical(tmp, size)


# stacked typography
def stacker(img, upper, lower, gap=2):
    holimg = hollow(img, 3)
    solimg = thick(img, 3)
    sw, sh = holimg.size
    hw, hh = holimg.size
    fh = (hh+gap)*(upper+lower)+sh+gap

    hol_np = np.array(holimg)
    sep = np.zeros((gap,hw),dtype=np.uint8)
    hol2 = np.vstack([hol_np, sep])

    uppart = np.tile(hol2, (upper, 1))
    lopart = np.tile(hol2, (lower, 1))
    sol_np = np.array(solimg)
    
    back = np.zeros((fh, hw), dtype=np.uint8)
    back[0:(hh+gap)*upper] = uppart
    back[(hh+gap)*upper+sh+gap:fh] = lopart
    back = Image.fromarray(back).convert('L')

    out = np.zeros((fh, hw), dtype=np.uint8)
    out[(hh+gap)*upper:(hh+gap)*upper+sh] = sol_np
    out = Image.fromarray(out).convert('L')
    
    return out, back    
    

# thick
def thick(img, width=3):  # img.mode == 'L'
    if width % 2 == 0:
        width += 1
    iw,ih = img.size
    newimg = Image.new('L', (iw+width*2, ih+width*2), 0)
    newimg.paste(img, (width, width))
    base_np = np.array(newimg)
    
    contour = newimg.filter(ImageFilter.FIND_EDGES)
    if width > 1:
        contour = contour.filter(ImageFilter.MaxFilter(width))
    contour_np = np.array(contour)

    or_img = np.maximum(base_np, contour_np) 
    
    return Image.fromarray(or_img, mode="L")

# Hollow
def hollow(img, width=3):  # img.mode == 'L'
    if width % 2 == 0:
        width += 1
    iw,ih = img.size
    newimg = Image.new('L', (iw+width*2, ih+width*2), 0)
    newimg.paste(img, (width, width))
    contour = newimg.filter(ImageFilter.FIND_EDGES)
    if width > 1:
        contour = contour.filter(ImageFilter.MaxFilter(width))

    return contour

# ----------
# Lorem Ipsum
def lorem_mask():
    lorwidth = prevset('width', None, 'lorem')
    lines = textwrap.wrap(LOREM, lorwidth)

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    size = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]

    lspc = prevset('lspc', None, 'common')
    grad = prevset('grad', None, 'common', lo=0)
    mid = prevset('mid', None, 'common', lo=0, hi=100)
    pos = prevset('pos', None, 'common', lo=0, hi=8)
    h_align = pos % 3  # 0:left 1:center 2:right

    limgs = []
    maxw = 0
    maxh = 0
    for l in lines:
        ltmp = text_image(l, source, index=index, size=size, color=WDAY_INT)
        lw, lh = ltmp.size
        if grad == 1:  # gradation linear
            maskpat = linear_line_mask(lw, lh, mid)
        elif grad == 2:  # gradation stripe line
            maskpat = stripe_line_mask(lw, lh, mid)
        else:
            maskpat = Image.new('L', (lw, lh), 255)
        limg = Image.new('L', (lw, lh), 0)
        limg.paste(maskpat, (0,0), ltmp)
        limg = limg.crop(limg.getbbox())
        lw, lh = limg.size
        maxw = max(maxw, lw)
        maxh += lh
        limgs.append(limg)
    maxh = int(maxh*lspc - (lspc-1)*lh)
    
    img = Image.new('L', (maxw, maxh), 0)
    y = 0
    for lim in limgs:
        lw, lh = lim.size
        if h_align == 2:
            x = maxw - lw
        elif h_align == 1:
            x = int((maxw - lw)/2)
        else:
            x = 0
            
        img.paste(lim, (x,y), lim)
        y = y+int(lh*lspc)

    img = img.crop(img.getbbox())
    return img


# ------------------------------------
# 前景を切り抜いて影付きで貼る(numpy版)
# ------------------------------------
def impose_mask(fgimg, mask_name, bgimg, W=None, H=None):
    """bgimg上にfgimgをmaskで切り出してインポーズする"""
    # shift = 8   影のシフト量(pixel)
    # alpha = 40  影の透過度(0-255)
    # blur = 10   影のぼかし半径(pixel)
    shift = prevset('shift', 8, 'shade')
    alpha = prevset('alpha', 40, 'shade')
    blur = prevset('blur', 10, 'shade')
    enbright = prevset('enbri', 0, 'shade')

    if W is None or H is None:
        W, H = fgimg.size

    mask2 = None
    if mask_name == 'cal':
        mask = calendar_mask()
    elif mask_name == 'txt':
        mask, mask2 = text_mask()
    elif mask_name == 'lor':
        mask = lorem_mask()
    else:
        mask = Image.new('L', (1, 1), 0)

    mask = allocate_img(W, H, mask)

    # 影
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, alpha), mask=mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))

    # 周期シフト
    dx = shift
    dy = shift

    shadow_np = np.array(shadow.convert('RGBA'))
    shifted_np = np.roll(shadow_np, shift=(dy, dx), axis=(0, 1))
    shadow = Image.fromarray(shifted_np, mode='RGBA')

    # マスクで切り抜き
    fg = Image.composite(fgimg, Image.new('RGBA', (W, H), (0, 0, 0, 0)), mask)
    if enbright != 0.0:
        fg = adjust_brightness(fg, enbright)
    if mask2 is not None:
        mask2 = allocate_img(W, H, mask2)
        mask2 = Image.composite(fgimg, Image.new('RGBA', (W, H), (0, 0, 0, 0)),
                                mask2)

    # 合成
    result = bgimg.convert('RGBA')
    if mask2 is not None:
        result = Image.alpha_composite(result, mask2)
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, fg)

    return result


def allocate_img(W,H, img):
    baseimg = Image.new('L', (W,H), 0)
    if img.mode != 'L':
        img = img.convert('L')

    iw, ih = img.size
    xpad = prevset('xpad', None, 'common', lo=0)
    ypad = prevset('ypad', None, 'common', lo=0)
    imgpos = prevset('pos', None, 'common', lo=0, hi=8)

    if (imgpos // 3) == 2:  # south
        iy = H - ih - ypad
    elif (imgpos // 3) == 1:  # center
        iy = (H - ih)//2
    else:  # north
        iy = ypad
    
    if (imgpos % 3) == 2:  # east
        ix = W - iw - xpad
    elif (imgpos % 3) == 1:  # center
        ix = (W - iw)//2
    else:  # west
        ix = xpad

    baseimg.paste(img, (ix, iy), img)
    # print(f'{imgpos} -> {ix},{iy}')

    return baseimg


def plain_image(W, H, base=(207,207,207), baseadd=(48,48,48), swirl=None):
    c = []
    for i in range(3):
        c.append(clip8(base[i]))
        if c[i] < 255 and baseadd[i] > 0:
            c[i] = clip8(np.random.randint(c[i], base[i]+baseadd[i]))
    img = Image.new('RGBA', (W, H), color=tuple(c))

    if swirl is None:
        return img

    fg = np.array(img, dtype=np.float32)
    factor = swirl_marble(W,H, swirl=swirl)
    res = (fg * factor[...,None]).astype(np.uint8)
        
    return Image.fromarray(res, mode='RGBA')


def swirl_marble(W, H, freq=10, swirl=13, wobble=3.3, contrast=0.04):
    xs = np.linspace(-1, 1, W, endpoint=False)
    ys = np.linspace(-1, 1, H, endpoint=False)
    X, Y = np.meshgrid(xs, ys)

    # アスペクト比補正
    aspect = W / H
    if aspect > 1:
        Y = Y * aspect
    else:
        X = X / aspect

    rad = np.sqrt(X * X + Y * Y)
    phi = np.arctan2(Y, X)

    flow = (
        rad * freq
        + phi * swirl
        + wobble * np.sin(phi * 5 + rad * 8)
    )

    base = (1.0 + contrast * np.sin(flow)).astype(np.float32)
    return np.clip(base, 0, 1)


# 明度変更補助
def srgb_to_linear(x, gamma):
    """numpy配列: sRGB(ガンマあり) → リニア変換"""
    x = x / 255.0
    base = np.maximum(x + 0.055, 0.0) / 1.055
    return np.where(x <= 0.04045, x / 12.92, base ** gamma)

def linear_to_srgb(x, gamma):
    """numpy配列: リニア → sRGB(ガンマあり)変換"""
    x = np.clip(x, 0.0, 1.0)
    return np.where(x < 0.0031308, x * 12.92,
                    1.055 * (x ** (1/gamma)) - 0.055) * 255.0

# --- 明度加算（ガンマ込み） ---
def adjust_brightness(img, delta: float, gamma: float = 2.2):
    """PILイメージの明度をdelta(-255.0..255.0)加算
    (gamma=2.2(sRGB), 1.8(Mac68k), )"""
    
    arr = np.asarray(img).astype(np.float32)

    # RGB / RGBA 判定
    has_alpha = (arr.shape[-1] == 4)
    rgb = arr[..., :3]
    alpha = arr[..., 3] if has_alpha else None

    # 明度加算（linear 空間で行う）
    rgb_lin = srgb_to_linear(rgb, gamma)
    delta_lin = srgb_to_linear(np.array([delta], dtype=np.float32), gamma)[0]
    rgb_lin = rgb_lin + delta_lin

    # 再構成
    rgb_srgb = linear_to_srgb(rgb_lin, gamma)
    if has_alpha:
        out = np.dstack([rgb_srgb, alpha])
    else:
        out = rgb_srgb

    return Image.fromarray(out.astype(np.uint8))


# --------------------
# main
# --------------------
def scan_va(va, mask_name):
    pre = f'-{mask_name}'
    for paramname in va.keys():
        if paramname.startswith(pre):
            param = paramname[len(pre):-1]
            val = va[paramname]
            if param.endswith('$'):
                pass
            elif isinstance(val, bool):
                val = 1 if val else 0
            else:
                val = stoi(val)
            # print(param, '=', val)
            storehist(param, val, Mask_Code[mask_name])
    return

    
def getval(elemval, name, cat, default=None, lo=None, hi=None):
    """elementの値(文字列)を数値化して保存"""
    v = stoi(elemval, default, lo, hi)
    if v is not None:
        storehist(name, v, cat)
    return v


# FontDir探索スレッド
def retrieve_fontdir(done_flag, fpath):
    fkeys, fdic = make_font_dic(fpath)

    done_flag['fkeys'] = fkeys
    done_flag['fdic'] = fdic
    done_flag['done'] = True

Dis_List = ['-fdsl-', '-fdfl-','-cgrad-', '-cpos-', '-flst-',   
            '-shpcal-', '-shptxt-', '-shplor-',
            '-bgsel-', '-swap-', '-bgc-', '-file1-',
            '-test-','-ok-','-can-']

def efx(image, p: Param):
    global calendar_preserv
    dcpy = copy.deepcopy(calendar_preserv)
    preview_size = Preview_Size
    
    W, H = p.width, p.height
    init_fgimg = image if image is not None else plain_image(W,H, swirl=6)    
    try:
        if init_fgimg.size != (W,H):
            init_fgimg = init_fgimg.resize((W,H), resample=Image.LANCZOS)
    except AttributeError:
        pass
    file_image = None

    # default Bacic Params
    shift = prevset('shift', None, 'shade')
    alpha = prevset('alpha', None, 'shade')
    blur = prevset('blur', None, 'shade')
    enbri = prevset('enbri', None, 'shade')

    base = Init_Color
    addv = 255 - max(base)
    fgc, bgc = bg_and_font(base)
    bgimg = plain_image(W,H, base=base, baseadd=(addv,addv,addv))
    bgfile = BgInd[3]
    bgmode = BgMenu[3]

    init_bgimg = p.bg(W,H)
 
    font_dir = Font_Dir  # 初期フォントディレクトリ
    fkeys, fdic = make_font_dic(font_dir)
    if len(fkeys) == 0:
        fkeys, fdic = make_font_dic(SysFont_Dir)
    storehist('key', fkeys[0], 'font')
    storehist('fontdic', fdic, 'font')
    fsize = prevset('size', None, 'font')

    # fdic["jp_family|face"] = [jp_family, face, family, source, idx]

    t = datetime.date.today()
    year = t.year
    month = t.month
    storehist('year', year, 'calendar')
    storehist('month', month, 'calendar')
    calwend = prevset('wend', None, 'calendar')
    calholi = prevset('holi', None, 'calendar')
    caltate = prevset('tate', None, 'calendar')

    txtmsg1 = prevset('msg1$', None, 'text')
    txtmsg2 = prevset('msg2$', None, 'text')
    txteffect = prevset('effect', None, 'text')
    txtstack = prevset('stack', None, 'text')
    txtupper = prevset('upper', None, 'text')

    lorwidth = prevset('width', None, 'lorem')

    chalf = prevset('half', None, 'common')
    cspc = prevset('spc', None, 'common')
    clspc = prevset('lspc', None, 'common')
    cmid = prevset('mid', None, 'common')
    cpos = prevset('pos', None, 'common')
    cgrad = prevset('grad', None, 'common')
    cxpd = prevset('xpad', None, 'common')
    cypd = prevset('ypad', None, 'common')
    
     
    # UI panel                
    fontset = [[sg.Text(f'Fonts ({font_dir})', '-fdir-'),
                sg.Button(' ... ', key='-fdsl-', background_color='#ddddff'),
                sg.Button('Sys', key='-fdfl-'),],
               [sg.Listbox(fkeys, key='-flst-', size=(35,FontList_Size),
                           enable_events=True),],
               [sg.Text('', key='-falt-', text_color='#772222'),],
               ]
    fontextparam = [
        sg.Text('Size'),
        sg.Input(f'{fsize}', key='-fsize-', width=3),
        sg.Text('Halftone'),
        sg.Input(f'{chalf}', key='-chalf-', width=4),
        sg.Text(' '),
        sg.Text('Gradient'),
        sg.Combo(GRADTYPE, key='-cgrad-', size=(6,1), readonly=True, 
                 default_value=GRADTYPE[cgrad], enable_events=True),
        sg.Text('boundary(%)'),
        sg.Input(f'{cmid}', key='-cmid-', width=3),
        sg.Text(expand_x=True),
        ]
    commonparam = [[sg.Text('BlockSpace', expand_x=True),
                    sg.Input(f'{cspc}', key='-cspc-', width=4),],
                   [sg.Text('LineSpace', expand_x=True),
                    sg.Input(f'{clspc}', key='-clspc-', width=4),],
                   [sg.Text('X-pad'),
                    sg.Input(f'{cxpd}', key='-cxpd-', width=4),
                    sg.Text('Y-pad'),
                    sg.Input(f'{cypd}', key='-cypd-', width=4),],
                   [sg.Text(expand_x=True),
                    sg.Text('Block Align'),
                    sg.Combo(POS, key='-cpos-', size=(4,1), readonly=True,
                             default_value=POS[cpos], enable_events=True),]
                   ]
    calparam = [
        sg.Radio('', group_id='-shpg-', default=True,
                 key='-shpcal-', enable_events=True),
        sg.Text('Calendar', size=(9,1)),
        sg.Column(layout=[[sg.Text('Year'),
                           sg.Input(f'{year}',key='-calyear-', width=5),
                           sg.Text('Month'),
                           sg.Input(f'{month}',key='-calmonth-', width=3),
                           sg.Text('Num of month'),
                           sg.Combo(['1','2','3','6','9','12'],
                                    key='-calmulti-', width=3,
                                    default_value='1', readonly=True),
                           ],
                          [sg.Checkbox('WeekEnd', key='-calwend-',
                                       default=(calwend==1)),
                           sg.Checkbox('Holiday', key='-calholi-',
                                       default=(calholi==1)),
                           sg.Checkbox('Vertical', key='-caltate-',
                                       default=(caltate==1)),]]),
        ]
    txtparam = [sg.Radio('', group_id='-shpg-', default=False,
                         key='-shptxt-', enable_events=True),
                sg.Text('Text', size=(9,1)),
                sg.Column([[sg.Text('Line 1'),
                            sg.Input(txtmsg1, key='-txtmsg1$-', width=30),],
                           [sg.Text('Line 2'),
                            sg.Input(txtmsg2, key='-txtmsg2$-', width=30),],
                           [sg.Combo(T_FX, key='-t_efx-', readonly=True,
                                     default_value=T_FX[txteffect], width=12),
                            sg.Text('Stack'),
                            sg.Input(txtstack,key='-txtstack-',width=3),
                            sg.Text('Upper'),
                            sg.Input(txtupper,key='-txtupper-',width=3),
                            sg.Text(expand_x=True)
                            ]
                           ]),
                ]
    lorparam = [
        sg.Radio('', group_id='-shpg-', default=False,
                 key='-shplor-', enable_events=True),
        sg.Text('LoremIpsum', size=(9,1)),
        sg.Text('Width'),
        sg.Input(f'{lorwidth}',key='-lorwidth-', width=3),
        ]
        
    cal_lo = [[sg.Column(layout=fontset),
               sg.Column(layout=[calparam,
                                 txtparam,
                                 lorparam,[],
                                 fontextparam,
                                 ])
               ]]

    shadeset = [[sg.Text('Shift='),
                 sg.Input(f'{shift}', key='-sshift-', width=4),
                 sg.Text(' ', expand_x=True),],
                [sg.Text('Blur='),
                 sg.Input(f'{blur}', key='-sblur-', width=4),],
                [sg.Text('Intent'),
                 sg.Input(f'{alpha}', key='-salpha-', width=4),],
                [],
                [sg.Text('Fg-Enbright'),
                 sg.Input(f'{enbri}', key='-senbri-', width=4),],
                ]
    bgset = [[sg.Combo(BgMenu, default_value=bgmode, key='-bgsel-',
                       width=5, readonly=True, enable_events=True),
              sg.Checkbox('Swap FG/BG', default=False, key='-swap-'),
              sg.Text(' Plain: '),
              sg.Button('BaseColor', key='-bgc-', text_color=fgc,
                        background_color=bgc),
              sg.Text('Jitter'), sg.Input(f'{addv}',
                                          key='-badd-', width=4),
              sg.Text(' '),
              sg.Text('BG file:'),
              sg.Button('Select BG', key='-file1-', background_color='#ffffdd'),
              sg.Text(bgfile, key='-fn1-', expand_x=True),
              ],
             ]
    buttonset = [
        sg.Text(' ', expand_x=True, expand_y=True),
        sg.Button('Test', key='-test-'),
        sg.Button('Ok', key='-ok-', background_color='#ddffdd'),
        sg.Button('Cancel', key='-can-', background_color='#ffdddd'),
        ]

    lo = [[sg.Frame(title='Text Overlay', layout=cal_lo, relief='ridge', expand_x=True)],
          [sg.Frame('Background', layout=bgset, relief='ridge',
                    expand_x=True)],
          [sg.Image(size=preview_size, key='-timg-'),
           sg.Column(layout=[[sg.Frame('Shading', layout=shadeset,
                                       relief='ridge', expand_x=True),],
                             [sg.Frame('Align Text', layout=commonparam,
                                       relief='ridge', expand_x=True),],
                             buttonset,], expand_x=True, expand_y=True ),
           ],
          ]
           
    src_path = None
    mask_name = 'cal'
    sample = impose_mask(bgimg, mask_name, init_fgimg, W, H)
   
    wn = sg.Window('Inpose Texts', layout=lo)
    busy = False
    
    def blink_text(flag):
        if flag['done']:
            fdi.flush_ev(wn)
            wn.dispatch_event('-thread-done-')
            return

        current = wn['-falt-'].get()
        wn['-falt-'].update('' if current else 'Processing...')
        wn.refresh()

        wn['-falt-'].widget.after(300, blink_text, flag)
        # register and return

    def set_gui_disabled(disable=True, list=Dis_List):
        for key in list:
            try:
                wn[key].set_disabled(disable)
            except:
                pass
    
    while True:
        wn['-timg-'].update(data=sample)
        
        ev, va = wn.read()
        # print(ev, va)

        if busy and ev != '-thread-done-':
            print('.', end='')
            continue

        if ev == sg.WINDOW_CLOSED or ev == '-can-':
            sample = image
            calendar_preserv = dcpy
            break
        elif ev == '-ok-':
            break
        elif ev == '-file1-':
            src_path = fdi.get_openfile(fdi.sanitize_filename(bgfile),
                                        filetypes=Image_Files)
            bgfile = pa.basename(src_path)
            if pa.exists(src_path):
                file_image = Image.open(src_path).convert('RGBA')
                file_image = file_image.resize((W,H), resample=Image.LANCZOS)
                va['-bgsel-'] = 'File'
                bgmode = None
            fdi.flush_ev(wn)
        elif ev == '-bgc-':
            base = to_rgb(sg.popup_color('Select Base Color',
                                         default_color=base))
            fgc, bgc = bg_and_font(base)
            wn['-bgc-'].update(background_color=bgc, text_color=fgc)
            va['-bgsel-'] = 'Plain'
            bgmode = None
            fdi.flush_ev(wn)
        elif ev == '-test-':
            bgmode = None
        elif ev == '-flst-':
            v = wn['-flst-'].get()
            if len(v) != 1:  # Listboxの値はlistで返る
                continue
            if v[0] in fdic:
                storehist('key', v[0], 'font')
                fkey = v
        elif ev == '-fdsl-' or ev == '-fdfl-':
            if ev == '-fdfl-':
                fpath = SysFont_Dir
            else:
                fpath = fdi.get_folder(init_dir=font_dir)
            if pa.exists(fpath):
                busy = True
                set_gui_disabled(True)
                flag = {'done': False}
                threading.Thread(target=retrieve_fontdir, args=(flag, fpath),
                                 daemon=True).start()
                blink_text(flag)
            continue
        elif ev == '-thread-done-':
            busy = False
            wn['-falt-'].update('')
            nfkeys = flag['fkeys']
            nfdic = flag['fdic']
            if len(nfkeys) > 0:
                fkeys = nfkeys
                fdic = nfdic
                font_dir = fpath
                storehist('key', fkeys[0], 'font')
                storehist('fontdic', fdic, 'font')
                set_gui_disabled(False, ['-fdir-','-flst-'])
                wn['-fdir-'].update(f'Fonts ({font_dir})')
                wn['-flst-'].update(values=fkeys)
            wn.refresh()
            fdi.flush_ev(wn)
            set_gui_disabled(False)
            flag['done'] = True
            continue
        elif ev.startswith('-shp'):
            mask_name = ev[4:-1]

        scan_va(va, mask_name)

        shift = getval(va['-sshift-'], 'shift', 'shade', default=0)
        alpha = getval(va['-salpha-'], 'alpha', 'shade', default=0,
                       lo=0, hi=255)
        blur = getval(va['-sblur-'], 'blur', 'shade', default=10, lo=0)
        getval(va['-senbri-'], 'enbri', 'shade', default=0)

        getval(va['-fsize-'], 'size', 'font', default=48, lo=8, hi=288)
        getval(va['-chalf-'], 'half', 'common', default=128, lo=0, hi=255)
        getval(va['-cspc-'], 'spc', 'common', default=1.3, lo=0.5, hi=2.0)
        getval(va['-clspc-'], 'lspc', 'common', default=1.4, lo=0.8, hi=2.0)
        getval(va['-cxpd-'], 'xpad', 'common', default=32, lo=0)
        getval(va['-cypd-'], 'ypad', 'common', default=32, lo=0)
        getval(va['-cmid-'], 'mid', 'common', default=35, lo=0, hi=100)
        #print(f'va = {va}\nshade = {calendar_preserv["shade"]}\n\n') 

        v = va['-cpos-']
        if v is not None:
            storehist('pos', POS.index(v), 'common')
        v =  va['-cgrad-']
        if v is not None:
            storehist('grad', GRADTYPE.index(v), 'common')
        v = va['-t_efx-']
        if v is not None:
            storehist('effect', T_FX.index(v), 'text')

        if va['-bgsel-'] == 'Plain' and bgmode != 'Plain':
            # print('Plain selected')
            bgmode = 'Plain'
            wn['-fn1-'].update(BgInd[3])
            addv = stoi(va['-badd-'])
            bgimg = plain_image(W, H, base=base, baseadd=(addv,addv,addv))
        elif va['-bgsel-'] == 'File':
            # print('File selected')
            if file_image is not None and bgmode != 'File':
                bgmode = 'File'
                wn['-fn1-'].update(bgfile)
                bgimg = file_image
        elif va['-bgsel-'] == 'BG':
            # print('BG selected')
            if bgmode != 'BG':
                if init_bgimg is not None:
                    bgmode = 'BG'
                    wn['-fn1-'].update(BgInd[1])
                    bgimg = init_bgimg
                else:
                    wn['-bgsel-'].update(bgmode)
        elif va['-bgsel-'] == 'FG':  # and bgmode != 'FG':
            # print('FG selected')
            bgmode = 'FG'
            wn['-fn1-'].update(BgInd[0])
            bgimg = init_fgimg

        wn['-bgsel-'].update(bgmode)
        wn['-falt-'].update('')
                
        if va['-swap-']:
              bg = init_fgimg
              fg = bgimg
        else:
              fg = init_fgimg
              bg = bgimg

        sample = impose_mask(bg, mask_name, fg, W, H)
        wn['-timg-'].update(sample)

        wn.refresh()

    wn.close()

    return sample


if __name__ == "__main__":
    p = Param()
    p.width, p.height = (1920,1080)
    
    img = efx(None, p)
    if img is not None:
        img.show()

    fk,fd = make_font_dic(Font_Dir)
    storehist('key', fk[0], 'font')
    storehist('fontdic', fd, 'font')
    storehist('msg1$','TestTest Test', 'text')
