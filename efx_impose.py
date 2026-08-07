from wall_common import *
import TkEasyGUI as sg
from PIL import Image, ImageDraw, ImageFont, ImageFilter #, ImageTk, ImageChops
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
POS = ['nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se']
GRADTYPE = ['None', 'Linear', 'Stripe']
BgMenu = ['FG', 'BG', 'File', 'Plain']
BgInd = ['*frontimage*', '*internal*', '*file*', '*plain*']
Mask_Code = {'cal': 'calendar', 'txt': 'text', 'lor': 'lorem'}

calendar_preserv = {'shade': {'shift':50, 'alpha':40, 'blur':10},
                    'font': {'key':None, 'size':64, 'fontdic':{}},
                    'common': {'pos':2, 'grad':0, 'lspc':1.4, 'spc':1.3,
                               'half':238, 'mid':35},
                    'calendar': {'year':2026, 'month':1, 'multi':1,
                                 'wend':1, 'holi':1},
                    'text': {'msg1$': '','msg2$': ''},
                    'lorem': {'width':30},
                    }

Init_Color = (48, 128, 192)
FontList_Size = 8
ExceptList = ['CRCGHankoin.ttc']  # 読み込み時エラーが発生するFONTファイル
SP_HOLIDAY = [(2,23)]  # 追加祝日 天皇誕生日など(ハッピーマンデー系はFFS)
WDAY_INT=0xff
PADDING=32
LOREM='Lorem ipsum dolor sit amet, consectetur adipiscing '+\
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
def prevset(name, value, funcname, lo=None, hi=None):
    retv = calendar_preserv.get(funcname, {}).get(name, value)
    
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

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    size = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]
    # print(fkey, fdic[fkey])  #####
    # print(calendar_preserv['calendar'], '\n', year, month, holiflag)

    if 0 < multi < 4:
        # print('caller', year, month, multi)
        calimg = multi_calendar(year, month, multi, source, index, size,
                                weekend=weekend, holiday=holiflag)
    elif 3 < multi < 13:
        lspc = prevset('lspc', None, 'common')
        spc = int(lspc*size)

        wi = int(multi-0.5) // 3
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

    return calimg


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


# Text
def text_mask():
    line1 = prevset('msg1$', None, 'text')
    line2 = prevset('msg2$', None, 'text')
    lines = [line1, line2]

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    size = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]

    lspc = prevset('lspc', None, 'common')
    spc = int(size * lspc)
    grad = prevset('grad', None, 'common', lo=0)
    mid = prevset('mid', None, 'common', lo=0, hi=100)

    limgs = []
    lhlist = []
    maxw = 1
    for ltxt in lines:
        if ltxt == '' or ltxt is None:
            if limgs == []:
                ltxt = ' '
            else:
                continue
        # print(f'{ltxt},{ord(ltxt[0])}')
        limg = text_image(ltxt, source, index=index, size=size, color=WDAY_INT)
        dimg = limg.crop(limg.getbbox())
        w1,h1 = limg.size
        if w1 == 0:
            dimg = Image.new('L',(10,size//4),0)
            
        if grad == 1:  # gradation linear
            maskpat = linear_line_mask(w1, h1, mid)
        elif grad == 2:  # gradation stripe line
            maskpat = stripe_line_mask(w1, h1, mid)
        else:
            maskpat = Image.new('L', (w1, h1), 255)

        img = Image.new('L', (w1, h1), 0)
        img.paste(maskpat, (0,0), dimg)

        limgs.append(img)
        lhlist.append(h1)
        maxw = max(maxw, w1)

    totalh = sum(lhlist)+(len(limgs)-1)*spc
    
    img = Image.new('L', (maxw, totalh), 0)
    y = 0
    for l in limgs:
        img.paste(l, (0,y))
        y = y+l.height+spc

    img = img.crop(img.getbbox())
    return img


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


    img = Image.new('L', (int(lorwidth*size), int(len(lines)*size*lspc)), 0)
    y = 0
    for l in lines:
        lim = text_image(l, source, index=index, size=size, color=WDAY_INT)
        lw, lh = lim.size
        if grad == 1:  # gradation linear
            maskpat = linear_line_mask(lw, lh, mid)
        elif grad == 2:  # gradation stripe line
            maskpat = stripe_line_mask(lw, lh, mid)
        else:
            maskpat = Image.new('L', (lw, lh), 255)
        
        img.paste(maskpat, (0,y), lim)
        y = y+int(lh*lspc)

    img = img.crop(img.getbbox())
    return img


# PROC functions
# 前景を切り抜いて影付きで貼る(numpy版)
def add_silhouette(fgimg, mask_name, bgimg, shift=0, alpha=90, blur=8,
                   sharp_radius=0, sharp_percent=180, sharp_threshold=3,
                   W=1920, H=1080):
    # shift = 30  影のシフト量(pixel)
    # alpha = 90  影の透過度(0-255)
    # blur = 8    影のぼかし半径(pixel)


    W, H = fgimg.size

    if mask_name == 'cal':
        mask = calendar_mask()
    elif mask_name == 'txt':
        mask = text_mask()
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
    dx = -shift
    dy = -shift

    base_np = np.array(fgimg.convert('RGBA'))
    shifted_np = np.roll(base_np, shift=(dy, dx), axis=(0, 1))
    shifted = Image.fromarray(shifted_np, mode='RGBA')

    # マスクで切り抜き
    fg = Image.composite(shifted,
                         Image.new('RGBA', (W, H), (0, 0, 0, 0)),
                         mask)
    if sharp_radius > 0:
        fg = fg.filter(ImageFilter.UnsharpMask(radius=sharp_radius,
                                               percent=sharp_percent,
                                               threshold=sharp_threshold))
    # 合成
    result = bgimg.convert('RGBA')
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, fg)

    return result


def allocate_img(W,H, img):
    baseimg = Image.new('L', (W,H), 0)
    if img.mode != 'L':
        img = img.convert('L')

    iw, ih = img.size
    
    imgpos = prevset('pos', None, 'common', lo=0, hi=8)

    if (imgpos // 3) == 2:  # south
        iy = H - ih - PADDING
    elif (imgpos // 3) == 1:  # center
        iy = (H - ih)//2
    else:  # north
        iy = PADDING
    
    if (imgpos % 3) == 2:  # east
        ix = W - iw - PADDING
    elif (imgpos % 3) == 1:  # center
        ix = (W - iw)//2
    else:  # west
        ix = PADDING

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

    
def getto(va, name, default, lo=None, hi=None):
    key = f'-s_{name}-'
    pv = calendar_preserv['shade'].get(name, default)
    
    try:
        v = va[key]
    except KeyError:
        return None
        
    retv = stoi(v, default, lo=lo, hi=hi)

    calendar_preserv['shade'][name] = retv
    return retv


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
    preview_size = (560,315)
    
    W, H = p.width, p.height
    init_fgimg = image if image is not None else plain_image(W,H, swirl=6)    
    try:
        if init_fgimg.size != (W,H):
            init_fgimg = init_fgimg.resize((W,H), resample=Image.LANCZOS)
    except AttributeError:
        pass

    # default Bacic Params
    shift = prevset('shift', None, 'shade')
    alpha = prevset('alpha', None, 'shade')
    blur = prevset('blur', None, 'shade')

    base = Init_Color
    addv = 255 - max(base)
    init_bgimg = p.bg(W,H)
    if init_bgimg is None:
        bgimg = plain_image(W,H, base=base, baseadd=(addv,addv,addv))
        bgfile = BgInd[3]
        bgmode = BgMenu[3]
    else:
        bgfile = BgInd[1]
        bgmode = BgMenu[1]
        bgimg = init_bgimg
 
    file_image = None
    fgc, bgc = bg_and_font(base)

    font_dir = Font_Dir
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

    txtmsg1 = prevset('msg1$', None, 'text')
    txtmsg2 = prevset('msg2$', None, 'text')

    lorwidth = prevset('width', None, 'lorem')

    chalf = prevset('half', None, 'common')
    cspc = prevset('spc', None, 'common')
    clspc = prevset('lspc', None, 'common')
    cmid = prevset('mid', None, 'common')
    cpos = prevset('pos', None, 'common')
    cgrad = prevset('grad', None, 'common')
     
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
    commonparam = [
        sg.Text(expand_x=True),
        sg.Text('BlockSpace'),
        sg.Input(f'{cspc}', key='-cspc-', width=4),
        sg.Text('LineSpace'),
        sg.Input(f'{clspc}', key='-clspc-', width=4),
        sg.Text(' '),
        sg.Text('Block Align'),
        sg.Combo(POS, key='-cpos-', size=(4,1), readonly=True,
                 default_value=POS[cpos], enable_events=True),
        sg.Text('  '),]
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
                                       default=(calholi==1)),]]),
        ]
    txtparam = [
        sg.Radio('', group_id='-shpg-', default=False,
                 key='-shptxt-', enable_events=True),
        sg.Text('Text', size=(9,1)),
        sg.Column(layout=[[sg.Text('Line 1'),
                           sg.Input(txtmsg1, key='-txtmsg1$-', width=30),],
                          [sg.Text('Line 2'),
                           sg.Input(txtmsg2, key='-txtmsg2$-', width=30),]]),
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
                                 commonparam,
                                 ])
               ]]

    shadeset = [[sg.Text(' Shift='),
                 sg.Input(f'{shift}', key='-s_shift-', width=4),
                 sg.Text(' ', expand_x=True),],
                [sg.Text(' Blur='),
                 sg.Input(f'{blur}', key='-s_blur-', width=4),],
                [sg.Text(' Intent'),
                 sg.Input(f'{alpha}', key='-s_alpha-', width=4),],
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
        sg.Text(' ', expand_x=True),
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
                             [sg.Text(size=(1,3), expand_y=True)],
                             buttonset,], expand_x=True, expand_y=True ),
           ],
          ]
           
    src_path = None
    mask_name = 'cal'
    sample = add_silhouette(bgimg, mask_name, init_fgimg) 
   
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
            # print(fpath)
            if pa.exists(fpath):
                busy = True
                set_gui_disabled(True)
                flag = {'done': False}
                threading.Thread(target=retrieve_fontdir, args=(flag, fpath),
                                 daemon=True).start()
                blink_text(flag)
            #wn['-falt-'].update(' ')
            continue
        elif ev == '-thread-done-':
            busy = False
            wn['-falt-'].update('')
            nfkeys = flag['fkeys']
            nfdic = flag['fdic']
            # print(f'-> {len(nfkeys)}')
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
            #print(f'mask={mask_name}')

        scan_va(va, mask_name)

        shift = getto(va, 'shift', shift, 0)
        alpha = getto(va, 'alpha', alpha, 0, 255)
        blur = getto(va, 'blur', blur, 0)

        v = stoi(wn['-fsize-'].get(),default=48, lo=8, hi=96)
        if v is not None:
            storehist('size', v, 'font')
        v = stoi(wn['-chalf-'].get(),default=128, lo=0, hi=255)
        if v is not None:
            storehist('half', v, 'common')
        v = stoi(wn['-cspc-'].get(),default=1.3, lo=0.5, hi=2.0)
        if v is not None:
            storehist('spc', v, 'common')
        v = stoi(wn['-clspc-'].get(),default=1.4, lo=0.8, hi=2.0)
        if v is not None:
            storehist('lspc', v, 'common')
        v = stoi(wn['-cmid-'].get(),default=35, lo=0, hi=100)
        if v is not None:
            storehist('mid', v, 'common')
        v = wn['-cpos-'].get()
        if v is not None:
            storehist('pos', POS.index(v), 'common')
        v =  wn['-cgrad-'].get()
        if v is not None:
            storehist('grad', GRADTYPE.index(v), 'common')

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

        sample = add_silhouette(bg, mask_name, fg,
                                shift=shift, alpha=alpha, blur=blur)
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
