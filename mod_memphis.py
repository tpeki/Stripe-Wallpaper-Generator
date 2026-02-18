import math
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image, ImageDraw
import TkEasyGUI as sg
from wall_common import *

# --- 定数設定 ---
PATTERN_SIZE = 80
TRIALS = 50
DELTA = 20
BGCOLOR1 = (1,1,0x99)
BGCOLOR2 = (1,1,1)
TINT = 100

# --- 内部定数設定 ---
WIDTH = 1920
HEIGHT = 1080
AA = 3
LINE_WIDTH = 2*AA
ABANDON = 8

COLORS = [(255,0,0), (80,240,80), (255,255,0),
          (100,100,255), (255,0,255), (0,255,255)]

Choco = [(246,230,119),  # plain
         (91,36,50),  # Chocolate
         (233,151,222),  # Strawberry
         (126,213,96),  # Green Tea
         (248,244,231),  # White
         ]

SHAPES = [
    ('triangle_solid', 'triangle_hollow'),
    ('triangle_hollow', 'triangle_hollow'),
    ('square_solid', 'square_hollow'),
    ('square_hollow', 'square_hollow'),
    ('circle_solid', 'circle_hollow'),
    ('circle_solid', 'circle_lattice'),
    ('circle_hollow', 'circle_hollow'),
    ('square_dot', None),
    ('chevron_line', None),
    ]

APPENDS = [
    ('pon_de_ring', None),
    ('donuts', None),
    ('fish', None),
    ('takoyaki', None),
    ('crown_solid', 'crown_hollow'),
    ('medal', None),
    ('dot', None),
    ('dot2', None),
    ('cross', None),
    ('arc', None),
    ('heart', None),
    ]

FN = {}

memphis_preserv = {
    'shapes': [],
    }

# module基本情報
def intro(modlist: Modules, module_name):
    modlist.add_module(module_name, 'メンフィス (サイズ×トライ数=320程度を推奨)',
                       {'color1':'背景色', 'color2':'背景色2',
                        'color_jitter':'彩度',
                        'pwidth':'パターンサイズ', 'pheight':'トライ数',
                        'pdepth':'間隔'})
    return module_name


# おすすめパラメータ
def default_param(p: Param):
    p.color1.itoc(*BGCOLOR1)
    p.color2.itoc(*BGCOLOR2)
    p.color_jitter = TINT
    p.pwidth = PATTERN_SIZE
    p.pheight = TRIALS
    p.pdepth = DELTA
    return p

# ----
# エレメント描画
# ----
def register(func):
    FN[func.__name__] = func
    return func

@register
def triangle_solid(size: int, color: tuple):
    mask = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(mask)

    obj_w = size *1.0
    obj_h = min(size * np.sin(np.deg2rad(60)), size)
    dx = size * 0.5
    dy = obj_h

    md.polygon((0,dy, dx,0, size,dy), fill=color)
    return mask

@register
def triangle_hollow(size: int, color: tuple):
    mask = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(mask)

    obj_w = size *1.0
    obj_h = min(size * np.sin(np.deg2rad(60)), size)
    dx = size * 0.5
    dy = obj_h
    lw = max(2, int(size/32))*AA

    md.polygon((0,dy, dx,0, size,dy), fill=0, outline=color,
               width=lw)
    return mask

@register
def square_solid(size: int, color: tuple):
    mask = Image.new('RGBA', (size,size), color)
    return mask

@register
def square_hollow(size: int, color: tuple):
    mask = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(mask)
    lw = max(2, int(size/32))*AA

    md.rectangle((lw, lw, size-lw, size-lw),
                 fill=0, outline=color, width=lw)
    return mask

@register
def circle_solid(size: int, color: tuple):
    r = size//2
    mask = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(mask)

    md.circle((r,r), r, fill=color)
    return mask

@register
def circle_hollow(size: int, color: tuple):
    r = size // 2
    mask = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(mask)
    lw = max(2, int(size/32))*AA

    md.circle((r,r), r-lw, fill=0, outline=color, width=lw)
    return mask

@register
def cross(size: int, color: tuple):
    size = int(size*0.3)
    r = max(2, int(size/32))*AA*2
    image = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(image)

    md.line([(r,r),(size-r,size-r)], fill=color, width=r*2)
    md.line([(r,size-r),(size-r,r)], fill=color, width=r*2)
    md.circle((r,r), r, fill=color)
    md.circle((r,size-r), r, fill=color)
    md.circle((size-r,r), r, fill=color)
    md.circle((size-r,size-r), r, fill=color)

    return image

@register
def arc(size: int, color: tuple):
    size = int(size*0.9)
    r = size / 2
    pr = int(r)//4
    sa,ea = 10,65
    image = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(image)
    cs,ss = np.cos(np.deg2rad(sa)), np.sin(np.deg2rad(sa))
    ce,se = np.cos(np.deg2rad(ea)), np.sin(np.deg2rad(ea))

    md.arc([(-size+pr,-size+pr),(size-pr,size-pr)], sa, ea,
           fill=color, width=pr*2)
    md.circle((cs*(r-pr)*2,ss*(r-pr)*2), pr, fill=color)
    md.circle((ce*(r-pr)*2,se*(r-pr)*2), pr, fill=color)

    return image

@register
def dot(size: int, color: tuple):
    r = max(2, int(size/32))*AA*3
    size = r*2
    image = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(image)
    md.circle((r,r), r, fill=color)

    return image

@register
def dot2(size: int, color: tuple):
    r = max(2, int(size/32))*AA*3
    pr = max(2, int(size/32))*AA*2
    size = r*3
    image = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(image)
    color1 = np.random.randint(0,len(COLORS))
    color2 = np.random.randint(0,len(COLORS))
    if color1 == color2:
        color2 = (color1 + 2) % len(COLORS)
    
    md.circle((r+pr,r+pr), r, fill=COLORS[color2])
    md.circle((r,r), r, fill=COLORS[color1])

    return image

@register
def heart(size: int, color: tuple):
    w = size // 2
    px = int((size - w)/2)
    el1 = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(el1)
    md.ellipse([(px,0),(px+w,size)], fill=color)
    el1 = el1.rotate(30,expand=True) #, resample= Image.Resampling.NEAREST)
    el1 = el1.crop(el1.getbbox())
    
    el2 = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(el2)
    md.ellipse([(px,0),(px+w,size)], fill=color)
    el2 = el2.rotate(-30,expand=True) #, resample=Image.Resampling.BICUBIC)
    el2 = el2.crop(el2.getbbox())
    
    size2x = int(max(el1.width, el2.width)*1.5)
    size2y = max(el1.height, el2.height)

    image = Image.new('RGBA', (size2x, size2y), 0)
    image.paste(el1,(0,0,el1.width,el1.height),el1)
    image.paste(el2,(size2x-el2.width,0,size2x,el2.height),el2)
    
    return image

@register
def square_dot(size: int, color: tuple):
    dot_count = 5
    space = int(size/(dot_count+1))
    dot_r = min(max(int(space // 4), AA), 10*AA)

    mask = Image.new('L', (size, size), 0)
    md = ImageDraw.Draw(mask)
    
    for x in range(dot_count):
        for y in range(dot_count):
            md.circle((x*space+dot_r, y*space+dot_r), dot_r, fill=255)

    ci = Image.new('RGB', (size, size), color)
    image = Image.new('RGBA', (size, size), 0)
    image.paste(ci, (0,0), mask)

    return image

@register
def circle_lattice(size: int, color: tuple):
    r = size // 2
    line_count = 8
    space = int(size/line_count)
    lw = max(2, int(size/32))*AA

    mask = Image.new('L', (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.circle((r,r), r, fill=255)

    ci = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(ci)
    
    for x in range(line_count):
        xx = x*space+space//2
        md.line([(0, xx),(size,xx)], fill=color, width=lw)
        md.line([(xx, 0),(xx, size)], fill=color, width=lw)

    image = Image.new('RGBA', (size, size), 0)
    image.paste(ci, (0,0), mask)

    return image


@register
def chevron_line(size: int, color: tuple):
    peaks = 4
    pat_w = int(size*peaks/2)
    band_width = max(pat_w//40, 2)*AA
    r = band_width // 2
    space = int((pat_w-band_width)/(peaks+1)/2)
    
    image = Image.new('RGBA', (pat_w,(space+band_width+r)*2), 0)
    md = ImageDraw.Draw(image)

    line_coords = []
    for x in range(peaks):
        line_coords.append((x*2*space+band_width+r, space+band_width+r))
        line_coords.append(((x*2+1)*space+band_width+r, band_width+r))
    line_coords.append((peaks*space*2+band_width+r, space+band_width+r))
    md.line(line_coords, width=band_width, fill=color, joint='curve')
    md.circle((band_width+r, space+band_width+r), r, fill=color)
    md.circle((peaks*space*2+band_width+r, space+band_width+r), r, fill=color)

    return image

@register
def pon_de_ring(size: int, color: tuple):
    cxy = size // 2
    r = cxy*0.6

    sin8 = np.sin(np.pi/8.0)
    r_center = r/(1+sin8)
    r_small = r - r_center

    colnum = len(Choco)
    cc = Choco[np.random.randint(1,colnum)]  # プレーン以外でコーティング

    mask = Image.new('L', (size,size), 0)
    md = ImageDraw.Draw(mask)
    for i in range(8):
        angle = i*np.pi/4
        cx = cxy + r_center*np.cos(angle)
        cy = cxy + r_center*np.sin(angle)
        md.circle((cx, cy), r_small, fill=255)

    coating = Image.new('RGBA', (size,size), cc)
    doe = Image.new('RGBA', (size,size), Choco[0])

    image = Image.new('RGBA', (size,size), 0)
    image.paste(doe, (0, 0), mask)
    if np.random.randint(0,4) > 2:  # 1/4の確率でチョコ掛け
        image.paste(coating, (0, -size//35), mask)

    return image
    
@register
def donuts(size: int, color: tuple):
    cxy = size // 2
    r = cxy*0.8
    colnum = len(Choco)
    cc = Choco[np.random.randint(1,colnum)]  # プレーン以外でコーティング

    mask = Image.new('L', (size,size), 0)
    md = ImageDraw.Draw(mask)
    md.circle((cxy, cxy), r, fill=255)
    md.circle((cxy, cxy), size//6, fill=0)
    
    coating = Image.new('RGBA', (size,size), cc)
    doe = Image.new('RGBA', (size,size), Choco[0])

    image = Image.new('RGBA', (size,size), 0)
    image.paste(doe, (0, 0), mask)
    if np.random.randint(0,8) > 0:  # 1/8の確率でプレーン
        image.paste(coating, (0, -size//14), mask)

    return image

@register
def crown_solid(size: int, color: tuple):
    y1 = size * 0.2
    y2 = size * 0.45
    y3 = size * 0.8
    x1 = size * 0.25
    x2 = size * 0.5
    x3 = size * 0.75

    image = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(image)
    md.polygon([(0,y1),(x1,y2),(x2,y1),(x3,y2),(size,y1),
                (size,y3),(0,y3),(0,y1)], fill=color)

    return image
    
@register
def crown_hollow(size: int, color: tuple):
    y1 = size * 0.2
    y2 = size * 0.45
    y3 = size * 0.8
    x1 = size * 0.25
    x2 = size * 0.5
    x3 = size * 0.75
    lw = max(2, int(size/32))*AA

    image = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(image)
    md.polygon([(lw,y1),(x1,y2),(x2,y1),(x3,y2),(size-lw,y1),
                (size-lw,y3),(lw,y3),(lw,y1)],
               outline=color, width=lw)

    return image

@register
def medal(size: int, color: tuple):
    y1 = size*0.375
    y2 = size*0.5
    y3 = size*0.75
    y4 = size*0.875
    x1 = size*0.375
    x2 = size*0.25
    x3 = size*0.375
    x4 = size*0.51
   
    image = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(image)
    md.circle((size//2,size//4), size//4, fill=color)
    md.polygon([(x1,y1),(x2,y3),(x3,y3),(x3,y4),(x4,y2)], fill=color)
    md.polygon([(size-x1,y1),(size-x2,y3),(size-x3,y3),
                (size-x3,y4),(size-x4,y2)], fill=color)
    return image

@register
def fish(size: int, color: tuple):
    size = min(size, 500)
    t_color = (*list(color[:3]), 0)
    color = (*list(color[:3]), 0xff)

    # 元画像
    im = Image.new('RGBA', (500,500), t_color)
    dr = ImageDraw.Draw(im)

    dr.circle((200,220),155,fill=color)
    dr.polygon([(160,120),(280,50),(332,138),(160,120)],fill=color)
    dr.polygon([(244,264),(450,190),(380,420),(244,264)],fill=color)
    dr.polygon([(200,370),(260,400),(310,330),(200,370)],fill=color)
    dr.polygon([(50,265),(90,260),(60,290),(50,265)],fill=(0,0,0,0))

    # 丸面取り
    alpha = np.array(im.split()[3]) > 0
    alpha = alpha.astype(np.uint8)
    r = 2  # 面取り半径
    kernel = circular_kernel(r)
    dil = npdilate(alpha, kernel)  # dilation → erosion
    ero = nperode(dil, kernel)

    rounded = (ero * 255).astype(np.uint8)
    im.putalpha(Image.fromarray(rounded))

    # 目と口を後から抜く
    dr.polygon([(50,265),(90,260),(60,290),(50,265)],fill=(0,0,0,0))
    dr.circle((140,150),32,fill=(0,0,0,0))

    # 縮小して返す
    im.thumbnail((size, size), Image.LANCZOS)
    return im

@register
def takoyaki(size: int, color: tuple):
    size = min(size, 500)
    im = Image.new('RGBA',(520, 520),0)
    md = ImageDraw.Draw(im)

    md.ellipse([(0,120),(460,520)],fill=Choco[0])
    md.polygon([(480,0),(380,160),(396,180),(500,28),(480,0)],fill=color)
    points = [(30,256)]
    for x in range(5):
        dy = 2-abs(x-2)
        points.append((x*80+80,170-dy*20))
        points.append((x*80+60,320))
    points.append((445,260))
    md.line(points, fill=Choco[1], width=50, joint='curve')
    for x in range(13):
        md.rectangle(((x*28+40, 240-(x%2)*80),(x*28+60, 260-(x%2)*80)),
                     fill=Choco[3])

    # 縮小して返す
    im.thumbnail((size, size), Image.LANCZOS)
    return im


# --- 描画サポート: dilation / erosion ---
def circular_kernel(r):
    y, x = np.ogrid[-r:r+1, -r:r+1]
    return (x*x + y*y <= r*r).astype(np.uint8)

def npdilate(mask, kernel):
    kh, kw = kernel.shape
    r_y, r_x = kh//2, kw//2
    H, W = mask.shape
    out = np.zeros_like(mask)

    for dy in range(-r_y, r_y+1):
        for dx in range(-r_x, r_x+1):
            if kernel[dy+r_y, dx+r_x] == 0:
                continue
            y1 = max(0, dy)
            y2 = min(H, H+dy)
            x1 = max(0, dx)
            x2 = min(W, W+dx)
            out[y1:y2, x1:x2] |= mask[y1-dy:y2-dy, x1-dx:x2-dx]
    return out

def nperode(mask, kernel):
    kh, kw = kernel.shape
    r_y, r_x = kh//2, kw//2
    H, W = mask.shape
    out = np.ones_like(mask)

    for dy in range(-r_y, r_y+1):
        for dx in range(-r_x, r_x+1):
            if kernel[dy+r_y, dx+r_x] == 0:
                continue
            y1 = max(0, dy)
            y2 = min(H, H+dy)
            x1 = max(0, dx)
            x2 = min(W, W+dx)
            out[y1:y2, x1:x2] &= mask[y1-dy:y2-dy, x1-dx:x2-dx]
    return out

# ----
# スイッチ
# ----
def desc(p: Param):
    current = memphis_preserv['shapes']
    apd_num = len(APPENDS)
    # SHAPES:Standard, APPENDS:Others
    cur_shapes = True if SHAPES[0] in current else False
    cur_apds = []
    for i in range(apd_num):
        cur_apds.append(True if APPENDS[i] in current else False)

    sl_w = 0
    sl_h = min(max(len(SHAPES),3),10)
    shape_list = ''
    for x in SHAPES:
        item = f'({x[0]}, {x[1]})\n'
        sl_w = len(item) if sl_w < len(item) else sl_w
        shape_list = shape_list + item

    al_w = 0
    for i in range(apd_num):
        item = f'({APPENDS[i][0]}, {APPENDS[i][1]})'
        al_w = len(item)+2 if al_w < len(item) else al_w
    list_w = max(sl_w, al_w)

    sha_lo = [[sg.Column(
        layout=[[sg.Checkbox('Standard shapes', default=cur_shapes,
                             key='-sha-', group_id='shape')],
                [sg.Text('', expand_y=True, size=(16,1))]]),
               sg.Multiline(shape_list, text_align='right', expand_x=True,
                        size=(list_w,sl_h))],
              ]

    al_h = max(len(APPENDS),3)
    if al_w*2 < list_w or apd_num >= 5:
        fold = True
        al_w = max(al_w, list_w // 2)
        al_h = max(int(len(APPENDS)/2+0.5),3)
    else:
        fold = False
        
    appends_items = []
    for i in range(apd_num):
        item = f'({APPENDS[i][0]}, {APPENDS[i][1]})'
        appends_items.append(sg.Checkbox(item, cur_apds[i], group_id='shape',
                                         key=f'-apd{i:02d}-'))

    apd_lo = [[sg.Text('Append shapes', expand_x=True)]]
    if fold:
        left = []
        right = []
        lines = int(apd_num/2+0.5)
        for i in range(lines):        
            left.append([appends_items[i]])
            if i+lines >= apd_num:
                right.append([sg.Text('',expand_x=True)])
                # print(APPENDS[i])
                break
            right.append([appends_items[i+lines]])
            # print(APPENDS[i],APPENDS[i+lines])

        apd_lo.append([sg.Column(layout=left),
                       sg.Column(layout=right)])
    else:        
        for x in appends_items:
            apd_lo.append([x])
    
    lo = [[sg.Frame('', layout=sha_lo, relief='groove')],
          [sg.Frame('', layout=apd_lo, relief='groove')],
          [sg.Text('', key='-msg-', expand_x=True),
           sg.Button('Cancel', key='-can-'),
           sg.Button('Ok', key='-ok-')],
          ]

    wn = sg.Window('Choose pattern-groups', layout=lo, modal=True)
    while True:
        ev, va = wn.read()
        
        if ev == '-can-' or ev == sg.WINDOW_CLOSED:
            result = None
            break
        elif ev == '-ok-':
            result = va['shape']
            if result != []:
                break
            wn['-msg-'].update('Choice at least one!', text_color='#ff0000')
        else:
            wn['-msg-'].update('')

    wn.close()
    if result is None:
        return

    new_shapes = []
    if '-sha-' in result:
        new_shapes.extend(SHAPES)
    for i in range(apd_num):
        if f'-apd{i:02d}-' in result:
            new_shapes.append(APPENDS[i])

    if current == new_shapes:
        return
    
    memphis_preserv['shapes'] = new_shapes
    # print(memphis_preserv['shapes'])
    return generate(p)


# ----
# 画像生成
# ----
def dilate(mask: np.ndarray, delta: int):
    # mask: bool 2D  delta幅の縁取りをつける(余白)
    k = 2 * delta + 1
    padded = np.pad(mask.astype(np.uint8), delta)
    H, W = mask.shape

    # 2D 畳み込みを einsum で高速化
    # 近傍の合計が 0 でなければ True
    out = np.zeros_like(mask, dtype=bool)
    for y in range(H):
        block = padded[y:y+k]  # (k, W+k-1)
        # block と kernel の畳み込みを行方向にまとめて計算
        s = np.convolve(block.sum(axis=0),
                        np.ones(k, dtype=np.uint8), mode='valid')
        out[y] = s > 0
    return out


def slidewin(matrix, radius):
    # 元配列の周囲に0で埋めた領域を足して配列の端で破綻しないようにする
    P = np.pad(matrix, pad_width=radius//2, mode='constant', constant_values=0)
    # スライディングウィンドウで近傍をくくる
    win = sliding_window_view(P, (radius,radius))
    # winは、Pの各セルに対応する [r,r] の配列の配列 [w,h,r,r] 
    # 各r,r のsumを取る → [w,h] の配列になる
    S = win.sum(axis=(2,3))

    return S

def generate(p: Param):
    ow, oh = p.width, p.height
    pat_size_min = p.pwidth*AA
    pat_size_max = int(pat_size_min * 1.3)
    shift = pat_size_min // 3
    delta = p.pdepth*AA
    num = p.pheight
    tint = p.color_jitter
    w, h = int(ow+p.pwidth*1.3+p.pdepth*3)*AA,\
           int(oh+p.pwidth*1.3+p.pdepth*3)*AA
    
    retry_count = ABANDON
    colors = COLORS
    color_num = len(colors)

    # shapesは文字列なので、実際には FN[name]()で呼出し
    if len(memphis_preserv['shapes']) == 0:
        memphis_preserv['shapes'].extend(SHAPES)
    shapes = memphis_preserv['shapes']
    shape_num = len(shapes)
    
    base = Image.new('RGBA', (w,h), color=0)

    # 占有マップ(grid)
    grid_w = w // (pat_size_min + delta)
    grid_h = h // (pat_size_min + delta)

    occ = np.zeros((h, w), dtype=bool)  # 占有マップ(bitmap)
    gocc = np.zeros((grid_w,grid_h),dtype=bool)

    rng = np.random.default_rng()
    rmap = rng.random((num,8))
    pat_diff = pat_size_max-pat_size_min
    
    for x in range(num):
        if (x%10) == 0:
            print(f'{int((num-x)/10)} ', end='')
        
        S = slidewin(gocc, 5)
        mask = (gocc == 0)
        if not mask.any():
            print('\nAll cells are occupied.  ', end='')
            break

        # 重み付け配置
        weights = np.zeros_like(S, dtype=float)
        weights[mask] = 1/(S[mask] + 1)+0.1
        prob = weights/weights.sum()

        # 偏差配置
        #mean = S[mask].mean()
        #std = S[mask].std()
        #if std == 0:
        #    T = np.full_like(S, 50, dtype=float)
        #else:
        #    T = np.zeros_like(S, dtype=float)
        #    T[mask] = 50 + 10*(S[mask]-mean)/std
        #    
        #prob = (T.max() - T) + 1
        #prob[~mask] = 0
        #prob = prob/prob.sum()

        prob_flat = prob.ravel()
        idx_flat = np.random.choice(len(prob_flat), p=prob_flat)
        px, py = divmod(idx_flat,grid_h)
        gocc[px, py] = 1

        px = px*(pat_size_min+delta) + int(rmap[x][1]*delta*3 - delta*1.5)
        py = py*(pat_size_min+delta) + int(rmap[x][2]*delta*3 - delta*1.5)

        s = int(rmap[x][0]*pat_diff+pat_size_min)
        pa = rmap[x][3] * np.pi * 2
        ps = shapes[int(rmap[x][4]*shape_num)]
        sc = rmap[x][5]*0.3+0.7
        pc = int(rmap[x][6]*color_num)
        pc2 = (pc+int(rmap[x][7]*color_num)) % color_num
        if pc2 == pc:
            pc2 = (pc2+1) % color_num

        offset = np.array([0, shift])  # ローカル座標
        R = np.array([[np.cos(pa), -np.sin(pa)],
                      [np.sin(pa), np.cos(pa)]])
        ox, oy = R @ offset

        pat1 = FN[ps[0]](int(s*sc), colors[pc])
        pat1 = pat1.rotate(np.rad2deg(pa), expand=True)
        p1w, p1h = pat1.size
        p1x = px - p1w//2
        p1y = py - p1h//2
        alpha1 = np.array(pat1.split()[3]) > 0
        alpha1_d = dilate(alpha1, delta)  # 占有範囲

        y10,y11 = p1y, p1y+p1h
        x10, x11 = p1x, p1x+p1w

        if ps[1] is not None:
            pat2 = FN[ps[1]](s, colors[pc2])
            pat2 = pat2.rotate(np.rad2deg(pa), expand=True)
            p2w, p2h = pat2.size
            p2x = int(px+ox - p2w/2)
            p2y = int(py+oy - p2h/2)
            alpha2 = np.array(pat2.split()[3]) > 0
            alpha2_d = dilate(alpha2, delta)  # 占有範囲

            y20, y21 = p2y, p2y+p2h
            x20, x21 = p2x, p2x+p2w
        else:
            pat2 = None

        if y10 < 0 or x10 < 0 or y11 > h or x11 > w:
            continue
        try:
            if np.any(occ[y10:y11, x10:x11] & alpha1_d):
                continue
        except ValueError:
            # Broadcast Error -> ignore
            continue
        
        if ps[1] is not None:
            if y20 < 0 or x20 < 0 or y21 > h or x21 > w:
                continue
            try:
                if np.any(occ[y20:y21, x20:x21] & alpha2_d):
                    continue
            except ValueError:
                # Broadcast Error -> ignore
                continue
                
        base.paste(pat1, (p1x,p1y), pat1)
        try:
            occ[y10:y11, x10:x11] |= alpha1_d
        except ValueError:
            # Broadcast Error -> ignore
            pass

        if ps[1] is not None:
            base.paste(pat2, (p2x,p2y), pat2)
            try:
                occ[y20:y21, x20:x21] |= alpha2_d
            except ValueError:
                # Broadcast Error -> ignore
                pass

    print('Done.')
    base = base.resize((w//AA, h//AA), resample=Image.LANCZOS)
    ofsx, ofsy = int((w/AA-ow)/2), int((h/AA-oh)/2)
    base = base.crop((ofsx,ofsy,ow+ofsx, oh+ofsy))
    base = sat_attenate(base, tint)

    img = vertical_gradient_rgb(ow, oh, p.color1, p.color2)
    img.paste(base, (0,0), base)

    return img

if __name__ == '__main__':
    p = Param()
    p = default_param(p)
    
    p.width = WIDTH
    p.height = HEIGHT

    memphis_preserv['shapes']=SHAPES
    memphis_preserv['shapes'].extend(APPENDS)
    
    img = generate(p)
    img.show()
