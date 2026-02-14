import numpy as np
from PIL import Image, ImageDraw
import TkEasyGUI as sg
from wall_common import *

# --- 定数設定 ---
DONUTS_ENABLE = 1  # 0:OFF 1: ON
PATTERN_SIZE = 80
TRIALS = 70
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

SHAPES = [('triangle_solid', 'triangle_hollow'),
          ('triangle_hollow', 'triangle_hollow'),
          ('square_solid', 'square_hollow'),
          ('square_hollow', 'square_hollow'),
          ('circle_solid', 'circle_hollow'),
          ('circle_solid', 'circle_lattice'),
          ('circle_hollow', 'circle_hollow'),
          ('square_dot', None),
          ('chevron_line', None),
          ]

DONUTS = [('pon_de_ring', None),
          ('donuts', None),
          ]

APPENDS = [('crown_solid', 'crown_hollow'),
           ('medal', None),
           ]

FN = {}

menphis_preserv = {
    'shapes': [],
    }

# module基本情報
def intro(modlist: Modules, module_name):
    modlist.add_module(module_name, 'メンフィス (重いがトライ数70ぐらいを推奨)',
                       {'color1':'背景色', 'color2':'背景色2',
                        'color_jitter':'彩度', 'sub_jitter':'Donuts(1:ON)',
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
    p.sub_jitter = DONUTS_ENABLE
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

    md.polygon((0,dy, dx,0, size,dy), fill=0, outline=color,
               width=LINE_WIDTH)
    return mask

@register
def square_solid(size: int, color: tuple):
    mask = Image.new('RGBA', (size,size), color)
    return mask

@register
def square_hollow(size: int, color: tuple):
    mask = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(mask)

    md.rectangle((LINE_WIDTH, LINE_WIDTH, size-LINE_WIDTH, size-LINE_WIDTH),
                 fill=0, outline=color, width=LINE_WIDTH)
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

    md.circle((r,r), r-LINE_WIDTH, fill=0, outline=color, width=LINE_WIDTH)
    return mask

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

    mask = Image.new('L', (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.circle((r,r), r, fill=255)

    ci = Image.new('RGBA', (size, size), 0)
    md = ImageDraw.Draw(ci)
    
    for x in range(line_count):
        xx = x*space+space//2
        md.line([(0, xx),(size,xx)], fill=color, width=LINE_WIDTH)
        md.line([(xx, 0),(xx, size)], fill=color, width=LINE_WIDTH)

    image = Image.new('RGBA', (size, size), 0)
    image.paste(ci, (0,0), mask)

    return image


@register
def chevron_line(size: int, color: tuple):
    pat_w = int(size*1.5)
    peaks = 4
    band_width = max(size//40,2)*AA
    space = int((size-band_width)/(peaks+1)/2)
    r = band_width // 2
    
    image = Image.new('RGBA', (size,size), 0)
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

    image = Image.new('RGBA', (size,size), 0)
    md = ImageDraw.Draw(image)
    md.polygon([(LINE_WIDTH,y1),(x1,y2),(x2,y1),(x3,y2),(size-LINE_WIDTH,y1),
                (size-LINE_WIDTH,y3),(LINE_WIDTH,y3),(LINE_WIDTH,y1)],
               outline=color, width=LINE_WIDTH)

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
    
# ----
# スイッチ
# ----
def desc(p: Param):
    current = menphis_preserv['shapes']
    # SHAPES:Standard, DONUTS:Donuts, APPENDS:Others
    cur_shapes = True if SHAPES[0] in current else False
    cur_donuts = True if DONUTS[0] in current else False
    cur_appends = True if APPENDS[0] in current else False

    shape_list = ''
    sl_w = 0
    sl_h = min(max(len(SHAPES),3),10)
    for x in SHAPES:
        item = f'({x[0]}, {x[1]})\n'
        sl_w = len(item) if sl_w < len(item) else sl_w
        shape_list = shape_list + item
    donuts_list = ''
    dl_w = 0
    dl_h = min(max(len(DONUTS),3),10)
    for x in DONUTS:
        item = f'({x[0]}, {x[1]})\n'
        dl_w = len(item) if dl_w < len(item) else dl_w
        donuts_list = donuts_list + item
    appends_list = ''
    al_w = 0
    al_h = min(max(len(APPENDS),3),10)
    for x in APPENDS:
        item = f'({x[0]}, {x[1]})\n'
        al_w = len(item) if al_w < len(item) else al_w
        appends_list = appends_list + item
    list_w = max(sl_w, dl_w, al_w)

    sha_lo = [[sg.Column(
        layout=[[sg.Checkbox('Standard shapes', default=cur_shapes,
                             key='-sha-', group_id='shape')],
                [sg.Text('', expand_y=True, size=(16,1))]]),
               sg.Multiline(shape_list, text_align='right', expand_x=True,
                        size=(list_w,sl_h))],
              ]
    don_lo = [[sg.Column(
        layout=[[sg.Checkbox('Donuts', default=cur_donuts,
                             key='-don-', group_id='shape')],
                [sg.Text('', expand_y=True, size=(16,1))]]),
               sg.Multiline(donuts_list, text_align='right', expand_x=True,
                        size=(list_w,dl_h))],
              ]
    apd_lo = [[sg.Column(
        layout=[[sg.Checkbox('Append shapes', default=cur_appends,
                             key='-apd-', group_id='shape')],
                [sg.Text('', expand_y=True, size=(16,1))]]),
               sg.Multiline(appends_list, text_align='right', expand_x=True,
                        size=(list_w,al_h))],
              ]
    
    

    lo = [[sg.Frame('', layout=sha_lo, relief='groove')],
          [sg.Frame('', layout=don_lo, relief='groove')],
          [sg.Frame('', layout=apd_lo, relief='groove')],
          [sg.Text('', key='-msg-', expand_x=True),
           sg.Button('Cancel', key='-can-'),
           sg.Button('Ok', key='-ok-')],
          ]

    wn = sg.Window('Choose pattern-groups', layout=lo)
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
    if '-don-' in result:
        new_shapes.extend(DONUTS)
    if '-apd-' in result:
        new_shapes.extend(APPENDS)

    menphis_preserv['shapes'] = new_shapes
    return


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


def generate(p: Param):
    ow, oh = p.width, p.height
    w, h = int(ow*1.2)*AA, int(oh*1.2)*AA
    pat_size_min = p.pwidth*AA
    pat_size_max = int(pat_size_min * 1.3)
    shift = pat_size_min // 3
    delta = p.pdepth*AA
    num = p.pheight
    tint = p.color_jitter
    
    retry_count = ABANDON
    colors = COLORS
    color_num = len(colors)

    # shapesは文字列なので、実際には FN[name]()で呼出し
    if len(menphis_preserv['shapes']) == 0:
        menphis_preserv['shapes'].extend(SHAPES)
        if p.sub_jitter:
            menphis_preserv['shapes'].extend(DONUTS)
    shapes = menphis_preserv['shapes']
    shape_num = len(shapes)
    
    base = Image.new('RGBA', (w,h), color=0)
    occ = np.zeros((h, w), dtype=bool)  # 占有マップ

    rng = np.random.default_rng()
    rmap = rng.random((num,8))
    pat_diff = pat_size_max-pat_size_min

    # print('Retry Max=',retry_count)
    waste = 0

    for x in range(num):
        if (x%10) == 0:
            print(f'{int((num-x)/10)} ', end='')
        
        et = 0
        while True:
            et += 1
            if et > retry_count:
                break
            
            s = int(rmap[x][0]*pat_diff+pat_size_min)
            px = int(rmap[x][1] * w)
            py = int(rmap[x][2] * h)
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
            if np.any(occ[y10:y11, x10:x11] & alpha1_d):
                continue
            
            if ps[1] is not None:
                if y20 < 0 or x20 < 0 or y21 > h or x21 > w:
                    continue
                if np.any(occ[y20:y21, x20:x21] & alpha2_d):
                    continue

            break
        
        if et <= retry_count:
            # print('retry=', et)
            base.paste(pat1, (p1x,p1y), pat1)
            occ[y10:y11, x10:x11] |= alpha1_d

            if pat2 is not None:
                base.paste(pat2, (p2x,p2y), pat2)
                occ[y20:y21, x20:x21] |= alpha2_d
        else:
            waste += 1
            # print('wasted.')

    print('')
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
    img = generate(p)
    img.show()
