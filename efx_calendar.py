from wall_common import *
import TkEasyGUI as sg
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter, ImageChops
import numpy as np
import math
import datetime
import copy
import io
import os
import os.path as pa
import filedialog as fdi
import inspect
import calendar
import tkinter as tk
from tkinter import filedialog
from fontTools.ttLib import TTFont
import glob
import zipfile

SysFont_Dir = r'c:\Windows\Fonts'
Font_Dir = r'd:\usr\pekidocs\Fonts'
FONT_EXT=('.ttf', '.otf', '.ttc')  #, '.fon')
Image_Files = [('PNG','*.png'),('JPG','*.jpg'),('Any','*.*'),]
POS = ['nw', 'n', 'ne', 'w', 'c', 'e', 'sw', 's', 'se']
GRADTYPE = ['None', 'Linear', 'Stripe']
BgMenu = ['FG', 'BG', 'File', 'Plain']
BgInd = ['*frontimage*', '*internal*', '*file*', '*plain*']
Mask_Code = {'cal': 'calendar', 'txt': 'text'}

calendar_preserv = {'shade': {'shift':50, 'alpha':40, 'blur':10,
                              'adjbri':-100.0},
                    'font': {'key':None, 'size':64, 'fontdic':{}},
                    'common': {'pos':2, 'grad':0, 'lspc':1.4, 'spc':1.3,
                               'half':238, 'mid':35},
                    'calendar': {'year':2026, 'month':1, 'wend':1, 'holi':1},
                    'text': {'msg1': '','msg2': ''},
                    }

ExceptList = ['CRCGHankoin.ttc']  # 読み込み時エラーが発生するFONTファイル
SP_HOLIDAY = [(2,23)]  # 追加祝日 天皇誕生日など(ハッピーマンデー系はFFS)
WDAY_INT=0xff
PADDING=32

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


# test util
def check_fflist(directory):
    fonts = list_fonts(directory)
    fflist = []
    for source in fonts:
        #print(basenm(source), ':Z' if source[1] is not None else '', end='')
        info = get_font_info(source)
        if info is None:
            #print(' no info')
            continue
        for ff in info:
            idx, family, jp_family, face = ff
            #print(f' {family}', f' {face}(,{idx})' if idx != 0 else f' {face}')
            fflist.append([jp_family, face, family, source, idx])
            
    return sorted(fflist)

# fontlistの再取得
def make_font_dic(directory):
    font_data_cache = {}   # data_cache クリア
    font_info_cache = {}   # フォント情報 クリア

    fonts = list_fonts(directory)
    fflist = []
    for source in fonts:
        info = get_font_info(source)
        if info is None:
            print(f'Purge {source}.')
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
    #ef_w, ef_h = x2-x1,y2-y1
    #w = max(ef_w, int(size*len(text)*0.5))
    #h = max(ef_h, int(size*1.2))
    #x, y = int(x1 - (w-ef_w)/2), int(y1 - (h-ef_h)/2)
    # print(img.getbbox(), f'-> {x},{y},{w+x1}({w}+{x1}),{h+y}({h}+{y})')
    #img = img.crop((x1, y, x1+w, y+h))
    
    img = img.crop((x1, y1, x2, y2))

    return img  # was ImageTk.PhotoImage(img)


# ----------
#  MASK functions
# ----------
# Calendar
def calendar_mask(W, H):
    # calendar param
    year = prevset('year', None, 'calendar')
    month = prevset('month', None, 'calendar')
    weekend = prevset('wend', None, 'calendar') == 1
    holiflag = prevset('holi', None, 'calendar') == 1

    half = prevset('half', None, 'common')
    lspc = prevset('lspc', None, 'common')
    dspc = prevset('spc', None, 'common')
    calpos = prevset('pos', None, 'common', lo=0, hi=8)
    grad = prevset('grad', None, 'common', lo=0)
    mid = prevset('mid', None, 'common', lo=0, hi=100)

    # font param
    fkey = prevset('key', None, 'font')
    fdic = prevset('fontdic', None, 'font')
    size = prevset('size', None, 'font')
    source = fdic[fkey][3]
    index = fdic[fkey][4]
    # print(fkey, fdic[fkey])  #####
    # print(calendar_preserv['calendar'], '\n', year, month, holiflag)

    body = calendar_body(year, month)
    if holiflag:
        holidays = holiday_map(year)[month-1]
    else:
        holidays = []

    # test_cell
    source = fdic[fkey][3]
    if index > fdic[fkey][4]:
        index = 0
    tim = text_image(' 39', source, index=index, size=size, color=WDAY_INT)
    std_w, std_h = tim.size
    std_w = int(std_w * dspc)
    std_h = int(std_h * lspc)
    hdr = text_image(f'{year}/{month}', source, index=index,
                     size=int(size*1.2), color=WDAY_INT)
    hdr_w, hdr_h = hdr.size


    if grad == 1:  # gradation linear
        maskhdr = linear_line_mask(hdr_w, hdr_h, mid)
        maskpat = linear_line_mask(std_w*7, std_h, mid)
    elif grad == 2:  # gradation stripe line
        maskhdr = stripe_line_mask(hdr_w, hdr_h)
        maskpat = stripe_line_mask(std_w*7, std_h)
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
            elif holiflag and day in holidays:
                color = half
            tim = text_image(f'{day}', source, index=index, size=size,
                             color=color)
            pos = ((i+1)*std_w-tim.width, 0)
            lpat.paste(tim, pos, tim)

        calimg.paste(maskpat, (0, int((j+0.5)*std_h)+hdr_h), lpat)

    cal_w, cal_h = calimg.size
    baseimg = Image.new('L', (W,H), 0)

    # print(f'{pos}, {type(pos)}')

    if (calpos // 3) == 2:  # south
        cal_y = H - cal_h - PADDING
    elif (calpos // 3) == 1:  # center
        cal_y = (H - cal_h)//2
    else:  # north
        cal_y = PADDING
    
    if (calpos % 3) == 2:  # east
        cal_x = W - cal_w - PADDING
    elif (calpos % 3) == 1:  # center
        cal_x = (W - cal_w)//2
    else:  # west
        cal_x = PADDING

    baseimg.paste(calimg, (cal_x, cal_y), calimg)

    return baseimg


# 濃淡グラデーション
def linear_line_mask(width, height, pos=33):
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
def stripe_line_mask(width, height):
    thick = [7,2,7,2,7,2,7,2,4,2,4,2,4,2,3,2,3,2,3,2,
             2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2]
    total_units = sum(thick)
    unit = height / total_units
    color = 255

    line = []
    for t in thick:
        h_stripe = int(t * unit)
        line.append(np.full((h_stripe, 1), color, dtype=np.uint8))
        color = 0 if color == 255 else 255
    column = np.vstack(line)
    
    if column.shape[0] < height:
        pad = height - column.shape[0]
        column = np.vstack([column, np.full((pad, 1), column[-1,0],
                                            dtype=np.uint8)])
    else:
        column = column[:height]

    mask = np.repeat(column, width, axis=1)    
    return Image.fromarray(mask, mode='L')


# カレンダー文字列生成
def calendar_body(year, month, firstday=calendar.SUNDAY):
    """カレンダー配列 firstday変更可"""
    
    calendar.setfirstweekday(firstday)
    cal = calendar.monthcalendar(year, month)
    cal = [[d or None for d in week] for week in cal]

    #for line in cal:
    #    for day in line:
    #        if day:
    #            print(f'{day:2d} ', end='')
    #        else:
    #            print('   ', end='')
    #    print('')


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


# PROC functions
# 前景を切り抜いて影付きで貼る(numpy版)
def add_silhouette(fgimg, mask, bgimg,
                   shift=0, alpha=90, blur=8, adjbri=0.0,
                   sharp_radius=0, sharp_percent=180, sharp_threshold=3,
                   W=1920, H=1080):
    # shift = 30  影のシフト量(pixel)
    # alpha = 90  影の透過度(0-255)
    # blur = 8    影のぼかし半径(pixel)


    W, H = fgimg.size

    if mask == 'cal':
        mask = calendar_mask(W, H)
    else:
        mask = Image.new('L', (W, H), 0)

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
    result = adjust_brightness(bgimg.convert('RGBA'), adjbri)
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, fg)

    return result


def resize_keepasp(img, W, H):
    iw, ih = img.size
    if ih == H and iw == W:
        return img

    r = min(W/iw, H/ih)
    return img.resize((int(iw*r),int(ih*r)), resample=Image.LANCZOS)


def plain_image(W, H, base=(207,207,207), baseadd=(48,48,48)):
    c = []
    for i in range(3):
        c.append(clip8(base[i]))
        if c[i] < 255 and baseadd[i] > 0:
            c[i] = clip8(np.random.randint(c[i], base[i]+baseadd[i]))
    img = Image.new('RGBA', (W, H), color=tuple(c))

    #fg = np.array(img, dtype=np.float32)
    #factor = swirl_marble(W,H, swirl=8, contrast=contrast)
    #res = (fg * factor[...,None]).astype(np.uint8)
        
    #return Image.fromarray(res, mode='RGBA')
    return img


def swirl_marble(W, H, freq=10, swirl=6, wobble=0.25, contrast=0.22):
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


# -----
# 明度変更
# -----
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

def luminance_linear(arr_lin):
    """numpy配列の輝度算出(リニア)"""
    return 0.2126*arr_lin[...,0] + 0.7152*arr_lin[...,1] + 0.0722*arr_lin[...,2]


# --- 明度加算（ガンマ込み） ---
def adjust_brightness(img: Image.Image, delta: float,
                      gamma: float = 2.2) -> Image.Image:
    """PILイメージの明度をdelta(-255.0..255.0)加算
    (gamma=2.2(sRGB), 1.8(Mac68k), )"""
    
    arr = np.asarray(img).astype(np.float32)

    # RGB / RGBA 判定
    has_alpha = (arr.shape[-1] == 4)
    rgb = arr[..., :3]
    alpha = arr[..., 3] if has_alpha else None

    # sRGB → linear
    rgb_lin = srgb_to_linear(rgb, gamma)

    # delta を linear に変換
    delta_lin = srgb_to_linear(np.array([delta], dtype=np.float32), gamma)[0]
    # print(np.max(delta_lin), np.min(delta_lin)) 

    # 明度加算（linear 空間で行う）
    rgb_lin = rgb_lin + delta_lin
    # print(np.max(rgb_lin), np.min(rgb_lin)) 

    # linear → sRGB
    rgb_srgb = linear_to_srgb(rgb_lin, gamma)

    # 再構成
    if has_alpha:
        out = np.dstack([rgb_srgb, alpha])
    else:
        out = rgb_srgb

    return Image.fromarray(out.astype(np.uint8))


# --- 明度を絶対値指定 ---
def set_brightness_absolute(img: Image.Image, target_L: float,
                            gamma: float = 2.2) -> Image.Image:
    """PILイメージの明度を絶対値(0.0..255.0)で指定
    (gamma=2.2(sRGB), 1.8(Mac68k), )"""
    arr = np.asarray(img).astype(np.float32)

    # RGB / RGBA 判定
    has_alpha = (arr.shape[-1] == 4)
    rgb = arr[..., :3]
    alpha = arr[..., 3] if has_alpha else None

    rgb_lin = srgb_to_linear(rgb, gamma)

    # 現在の明度（linear）
    L = luminance_linear(rgb_lin)

    # RGB 比を維持してスケール
    target_lin = srgb_to_linear(np.array([target_L], dtype=np.float32),
                                gamma)[0]
    scale = target_lin / (L + 1e-6)
    rgb_lin = rgb_lin * scale[..., None]

    # linear → sRGB
    rgb_srgb = linear_to_srgb(rgb_lin, gamma)

    # 再構成
    if has_alpha:
        out = np.dstack([rgb_srgb, alpha])
    else:
        out = rgb_srgb

    return Image.fromarray(out.astype(np.uint8))


# --------------------
# main
# --------------------
def mask_line(mask_name, sw):
    if not mask_name in FN:
        return None
    args = FN[mask_name]['defaults']
    
    lo = [sg.Radio('', default=sw, key=mask_name, group_id='-item-'),
          sg.Text(FN[mask_name]['display'], width=12)]
    for param in args.keys():
        lo.append(sg.Text(param))
        val = prevset(param, args[param], mask_name)
        lo.append(sg.Input(f'{val}', key=f'-{mask_name}_{param}-', width=4))

    return lo

def scan_va(va, mask_name):
    pre = f'-{mask_name}'
    for paramname in va.keys():
        if paramname.startswith(pre):
            val = stoi(va[paramname])
            param = paramname[len(pre):-1]
            # print(param)
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


def efx(image, p: Param):
    global calendar_preserv
    dcpy = copy.deepcopy(calendar_preserv)
    preview_size = (640,360)
    
    W, H = p.width, p.height
    init_fgimg = image if image is not None else plain_image(W,H)    
    try:
        if init_fgimg.size != (W,H):
            init_fgimg = init_fgimg.resize((W,H), resample=Image.LANCZOS)
    except AttributeError:
        pass

    # default Bacic Params
    shift = prevset('shift', None, 'shade')
    alpha = prevset('alpha', None, 'shade')
    blur = prevset('blur', None, 'shade')
    adjbri = prevset('adjbri', None, 'shade')

    base = (207,207,207)
    baseadd = tuple(255-base[i] for i in range(3))
    init_bgimg = plain_image(W,H, base=base, baseadd=baseadd)
    bgfile = BgInd[3]
    bgmode = BgMenu[3]
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
               [sg.Listbox(fkeys, key='-flst-', size=(35,10),
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
                 default_value=GRADTYPE[cgrad]),  #, enable_events=True),
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
                 default_value=POS[cpos]),  #, enable_events=True),
        sg.Text('  '),]
    calparam = [
        sg.Radio('', group_id='-shpg-', default=True,
                 key='-shpcal-', enable_events=True),
        sg.Text('Calendar', size=(9,1)),
        sg.Text('Year'),
        sg.Input(f'{year}',key='-calyear-', width=5),
        sg.Text('Month'),
        sg.Input(f'{month}',key='-calmonth-', width=3),
        sg.Checkbox('WeekEnd', key='-calwend-', default=(calwend==1)),
        sg.Checkbox('Holiday', key='-calholi-', default=(calholi==1)),
        ]
    txtparam = [
        sg.Radio('', group_id='-shpg-', default=False,
                 key='-shptxt-', enable_events=True),
        sg.Text('Text', size=(9,1)),
        sg.Column(layout=[[sg.Text('Line 1'),
                           sg.Input('',key='-txtmsg1-', width=30),],
                          [sg.Text('Line 2'),
                           sg.Input('',key='-txtmsg2-', width=30),]]),
        ]
    cal_lo = [[sg.Column(layout=fontset),
               sg.Column(layout=[calparam,[],
                                 #txtparam,[],
                                 [sg.Text(expand_y=True,size=(1,4))],
                                 fontextparam,
                                 commonparam,
                                 ])
               ]]

    shadeset = [[sg.Text(' Shift='),
                 sg.Input(f'{shift}', key='-s_shift-', width=4),
                 sg.Text(' Blur='),
                 sg.Input(f'{blur}', key='-s_blur-', width=4),
                 sg.Text(' Intent'),
                 sg.Input(f'{alpha}', key='-s_alpha-', width=4),
                 sg.Text(' BG Brightness='),
                 sg.Input(f'{adjbri}', key='-s_adjbri-', width=7),
                 sg.Text(expand_x=True),
                 ]]

    bgset = [[sg.Combo(BgMenu, default_value=bgmode, key='-bgsel-',
                       width=5, readonly=True, enable_events=True),
              sg.Checkbox('Swap FG/BG', default=False, key='-swap-'),
              sg.Text(' Plain: '),
              sg.Button('BaseColor', key='-bgc-', text_color=fgc,
                        background_color=bgc),
              sg.Text('Jitter'), sg.Input(f'{clip8(255-max(*base))}',
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
          [sg.Image(size=preview_size, key='-timg-')],
          [sg.Frame('Common Shading', layout=shadeset, relief='ridge',
                    expand_x=True)],
          [sg.Frame('Background', layout=bgset, relief='ridge',
                    expand_x=True)],
          buttonset,
          ]
           
    src_path = None
    mask_name = 'cal'

    sample = add_silhouette(bgimg, mask_name, init_fgimg) 
   
    wn = sg.Window('Inject Calendar', layout=lo)
    
    while True:
        wn['-timg-'].update(data=sample)
        
        ev, va = wn.read()
        # print(ev, va)

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
            base = to_rgb(sg.popup_color('Select Base Color', default_color=base))
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
                fpath = fdi.get_folder(init_dir=Font_Dir)
            # print(fpath)
            if pa.exists(fpath):
                nfkeys, nfdic = make_font_dic(fpath)
                # print(f'-> {len(nfkeys)}')
                if len(nfkeys) > 0:
                    fkeys = nfkeys
                    fdic = nfdic
                    font_dir = fpath
                    storehist('key', fkeys[0], 'font')
                    storehist('fontdic', fdic, 'font')
                    wn['-fdir-'].update(f'Fonts ({font_dir})')
                    wn['-flst-'].update(values=fkeys)
                else:
                    wn['-falt-'].update('Not valid dir!')
            continue


        scan_va(va, mask_name)

        shift = getto(va, 'shift', shift, 0)
        alpha = getto(va, 'alpha', alpha, 0, 255)
        blur = getto(va, 'blur', blur, 0)
        adjbri = getto(va, 'adjbri', adjbri)

        v = stoi(wn['-fsize-'].get(),default=48, lo=8, hi=96)
        if v:
            storehist('size', v, 'font')
        v = stoi(wn['-chalf-'].get(),default=128, lo=0, hi=255)
        if v:
            storehist('half', v, 'common')
        v = stoi(wn['-cspc-'].get(),default=1.3, lo=0.5, hi=2.0)
        if v:
            storehist('spc', v, 'common')
        v = stoi(wn['-clspc-'].get(),default=1.4, lo=0.8, hi=2.0)
        if v:
            storehist('lspc', v, 'common')
        v = stoi(wn['-cmid-'].get(),default=35, lo=0, hi=100)
        if v:
            storehist('mid', v, 'common')
        v = wn['-cpos-'].get()
        if v:
            storehist('pos', POS.index(v), 'common')
        v =  wn['-cgrad-'].get()
        if v:
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
            if init_bgimg is not None and bgmode != 'BG':
                bgmode = 'BG'
                wn['-fn1-'].update(BgInd[1])
                bgimg = init_bgimg
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

        sample = add_silhouette(bg, mask_name, fg, shift=shift, alpha=alpha,
                                blur=blur, adjbri=adjbri)
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
