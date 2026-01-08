'''wallpaper generator 共通クラス＆関数'''
from dataclasses import dataclass
from PIL import Image, ImageDraw
import random
import numpy as np
import os.path as pa
import colorsys

def clip8(x: int):
    '''clip8(x) -> {x | 0 <= x <= 255}に制限する'''
    return min(255, max(x, 0))


class RGBColor:
    '''色を格納するクラス'''
    def __init__(self, *args):
        self.r, self.g, self.b = self._parse(args)

    @staticmethod
    def _parse(args):
        # RGBColors((r,g,b))
        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            r,g,b = args[0][:3]

        # RGBColors(r,g,b)
        elif len(args) >= 3:
            r,g,b = args[:3]

        # RGBColors('#rrggbb')
        elif len(args) == 1 and isinstance(args[0], str) and len(args[0]) >= 6:
            s = args[0]
            if s.startswith('#'):
                s = s[1:]
            r,g,b = (int(s[i*2:i*2+2], 16) for i in range(3))

        else:
            raise ValueError('Invalid color format')
            
        if not all(isinstance(x, int) for x in (r,g,b)):
            raise ValueError('Parameters must be integer')

        return clip8(r), clip8(g), clip8(b)

    def ctox(self):
        return f'#{self.r & 0xff:02x}{self.g & 0xff:02x}{self.b & 0xff:02x}'

    def ctoi(self):
        return self.r & 0xff, self.g & 0xff, self.b & 0xff

    def black(self):
        self.r = 0
        self.g = 0
        self.b = 0
        return self.r, self.g, self.b

    def xtoc(self, s: str):
        if len(s) < 6:
            raise ValueError('Invalid color format')
        if s.startswith('#'):
            s = s[1:]
        self.r, self.g, self.b = (int(s[i*2+1:i*2+3], 16) & 0xff for i in range(3))
        return self.r, self.g, self.b
        
    def itoc(self, r, g, b):
        self.r = clip8(r)
        self.g = clip8(g)
        self.b = clip8(b)
        return self.r, self.g, self.b


SAVE_NUM=9

@dataclass
class Param:
    '''モジュールに渡すパラメータ'''
    width: int = 1920
    height: int = 1080
    wwidth: int = 0  # tk makes automatically
    wheight: int = 0
    wposx: int = 0  # tk locates automatically
    wposy: int = 0
    color1: RGBColor = RGBColor(220,214,96)
    color2: RGBColor = RGBColor(0,0,0)
    color3: RGBColor = RGBColor(0,0,0)
    color_jitter:int = 48  # 色ゆらぎ(主色)
    sub_jitter: int = 27  # 色ゆらぎ(パターン)
    sub_jitter2: int = 0  # 色ゆらぎ(パターン2)
    pwidth: int = 17
    pheight: int = 140
    pdepth: int = 0
    pattern: str = ''  # module名
    savefile: str = ''

    def file_name(self):
        if len(self.savefile) < 1:
            self.savefile = self.pattern+'.png'
        base = pa.splitext(self.savefile)[0]
        if pa.exists(self.savefile):
            for i in range(SAVE_NUM-1):
                if not pa.exists(f'{base}{i}.png'):
                    break
                elif i == SAVE_NUM-2:
                    print('Already saved enough...')
            fname = f'{base}{i}.png'
            self.savefile = fname
        return self.savefile

PARAMVALS = ['color1', 'color2', 'color3',
             'color_jitter', 'sub_jitter', 'sub_jitter2',
             'pwidth', 'pheight', 'pdepth']

# プラグインのspec()で、モジュール名、説明、利用パラメータを返すように
# して、それをModulesに保存
# モジュールファイル名は mod_ で始めるが、モジュール名はmod_なし
# 利用パラメータリストは、利用するパラメータ名のリスト(入っているものは利用)
#  (例) mod_gui['stripe'] = ['color1', 'color_jitter', 'pwidth', ...]
class Modules:
    '''プラグインモジュール情報'''
    def __init__(self):
        self.modules = []
        self.mod_desc = {}
        self.mod_gui = {}

    def add_module(self, module_name: str, module_desc: str,
                   using_gui_list):
        if module_name.startswith('mod_'):
            module_name = module_name.split('mod_')[1]
        if module_name not in self.modules:
            self.modules.append(module_name)
            self.mod＿desc[module_name] = module_desc
            self.mod_gui[module_name] = using_gui_list


def is_param(x:str):
    return x in PARAMVALS


# 背景パターン
def rgb_random_jitter(color: RGBColor, jitter):
    '''(R,G,B)に対してそれぞれ±jitterの幅でランダムに変化'''
    rgb = color.ctoi()
    rgb = tuple(clip8((c + random.randint(-jitter, jitter))) for c in rgb)
    return RGBColor(rgb)


def brightness(color: RGBColor, f=1.0, bg=None):
    '''brightness(RGBColor, float) -> RGBColor
        darken if f < 1.0, lighten if f > 1.0
    '''
    crgb = color.ctoi()
    r_norm, g_norm, b_norm = [c / 255.0 for c in crgb]
    h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
    
    new_l = max(0.0, min(1.0, l*f))
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, new_l, s)

    if r_new+g_new+b_new <= 0.0:
        if bg is not None:
            return bg
        else:
            return RGBColor(0,0,0) if bg is None else bg

    return RGBColor(round(r_new * 255),
                    round(g_new * 255),
                    round(b_new * 255))

def rgb_lerp(c1, c2, t):
    ''' RGB値の線形補完 c1,c2=tuple(r,g,b), t=比率(0..1)'''
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_diagonal_gradient_rgb(draw, width, height,
                               c1: RGBColor, c2: RGBColor):
    '''斜めグラデーションで塗りつぶし (超遅い)
    draw: PIL.ImageDraw
    c1,c2: RGBColor
    '''
    max_d = width + height
    cc1 = c1.ctoi()
    cc2 = c2.ctoi()

    for y in range(height):
        for x in range(width):
            t = (x + y) / max_d
            color = rgb_lerp(cc1, cc2, t)
            draw.point((x, y), fill=color)


def draw_horizontal_gradient_rgb(draw, width, height,
                                 c1: RGBColor, c2: RGBColor):
    '''縦グラデーションで塗りつぶし
    draw: PIL.ImageDraw
    c1,c2: RGBColor
    '''
    max_d = height
    cc1 = c1.ctoi()
    cc2 = c2.ctoi()
    pen = 10
    tick = int(pen/2)-1

    for y in range(int(height/pen)):
            t = y*pen/max_d
            color = rgb_lerp(cc1, cc2, t)
            draw.line((0, y*pen+tick, width-1, y*pen+tick),
                      fill=color, width=pen)
            

def diagonal_gradient_rgb_np(width, height, color1:RGBColor, color2:RGBColor):
    '''
    NumPy で高速に斜めグラデーションを作る
    color1, color2: RGBColor ctoi() -> (r,g,b)
    return: PIL.Image
    '''
    # 座標グリッド
    y, x = np.mgrid[0:height, 0:width]

    # 正規化パラメータ t
    t = (x + y) / (width + height)

    # RGB を配列化
    c1 = color1.ctoi()
    c2 = color2.ctoi()
    
    c1 = np.array(c1, dtype=np.float32)
    c2 = np.array(c2, dtype=np.float32)

    # 線形補完（ブロードキャスト）
    img = c1 + (c2 - c1) * t[..., None]

    return Image.fromarray(img.astype(np.uint8), 'RGB')


# グラデーション背景の生成テンプレ
# [Diagonal]
#   bg_start = rgb_random_jitter(bg_color, jitter)
#   bg_end   = rgb_random_jitter(bg_color, jitter)
#   image = diagonal_gradient_rgb_np(width, height,
#                                    bg_start, bg_end)
#   draw = ImageDraw.Draw(image)
#
# [Horizontal]
#
#   image = Image.new("RGB", canvas_size)
#   draw = ImageDraw.Draw(image)
#
#   bg_start = rgb_random_jitter(bg_color, jitter)
#   bg_end   = rgb_random_jitter(bg_color, jitter)
#
#   draw_horizontal_gradient_rgb(draw, canvas_size[0], canvas_size[1],
#                              bg_start, bg_end)
#


def rgb_string(*args):
    '''R,G,Bの数値を16進文字列にする'''
    if len(args) == 1 and isinstance(args[0], (tuple, list)):
        r,g,b = args[0][:3]
    elif len(args) == 3:
        r,g,b = args
    else:
        raise ValueError('Parameter will be 3 int or 1 tuple')
    
    if not all(isinstance(x, int) for x in (r,g,b)):
        raise ValueError('Parameters must be integer')
    
    r = clip8(r)
    g = clip8(g)
    b = clip8(b)
    return f'#{r:02x}{g:02x}{b:02x}'


def to_rgb(value):
    '''(r,g,b)もしくは'#rrggbb'を受け取って、r,g,bを返す'''
    if isinstance(value, tuple):
        if len(value) < 3:
            raise ValueError('Tuple too short')
        r,g,b = value[:3]
        if all(isinstance(x, int) for x in (r,g,b)):
            return clip8(r), clip8(g), clip8(b)
        else:
            raise ValueError('Tuple has not integer')
    if isinstance(value, str) and len(value) >= 6:
        if value[0] == '#':
            value = value[1:]
        try:
            rgb = [int(value[i*2:i*2+2], 16) for i in range(3)]
            return tuple(rgb)
        except ValueError:
            raise ValueError('Hexadecimal is not correct')
    raise ValueError('Invalid format')
            
