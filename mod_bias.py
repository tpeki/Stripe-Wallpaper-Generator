import numpy as np
from PIL import Image
from wall_common import *

# ===== 定数 =====
COLOR1 = (0xa0, 0xee, 0xff)
COLOR2 = (0xa7, 0xf8, 0xd0)
COLOR3 = (0xd6, 0x88, 0xe3)
C_JITTER = 20
S_JITTER = 40

BAND_WIDTH = 60      # 帯の幅（px）
ANGLE_DEG = 40       # 0～180（度）
# ================

# module基本情報
def intro(modlist: Modules, module_name):
    modlist.add_module(module_name, 'バイアス',
                       {'color1':'線色1', 'color2':'線色2',
                        'color3':'線色3',
                        'color_jitter':'色差分', 'sub_jitter':'彩度変更(%)',
                        'pwidth':'線幅', 'pheight':'勾配(0-180)'})
    return module_name

# おすすめパラメータ
def default_param(p: Param):
    p.color1.itoc(*COLOR1)
    p.color2.itoc(*COLOR2)
    p.color3.itoc(*COLOR3)
    p.color_jitter = C_JITTER
    p.sub_jitter = S_JITTER
    p.pwidth = BAND_WIDTH
    p.pheight = ANGLE_DEG
    return p

# バイアス生成
def generate(p: Param):
    w = p.width
    h = p.height
    cjit = p.color_jitter
    sjit = p.sub_jitter / 100
    color1 = brightness(rgb_random_jitter(p.color1, cjit), s=sjit)
    color2 = brightness(rgb_random_jitter(p.color2, cjit), s=sjit)
    color3 = brightness(rgb_random_jitter(p.color3, cjit), s=sjit)
    bandwidth = p.pwidth
    angle = p.pheight

    c1 = color1.ctoi()
    c2 = color2.ctoi()
    c3 = color3.ctoi()
    
    # 座標グリッド
    y, x = np.mgrid[0:h, 0:w]

    # 角度（ラジアン）
    theta = np.deg2rad(angle)

    # 帯に垂直な方向への射影
    s = x * np.cos(theta) + y * np.sin(theta)

    # 色インデックス（0,1,2）
    idx = ((s // bandwidth) % 3).astype(np.int32)

    # 色テーブルを NumPy 配列に
    color_table = np.array([c1, c2, c3], dtype=np.uint8)

    # インデックスで一発変換（H×W×3）
    img_np = color_table[idx]
    img = Image.fromarray(img_np, "RGB")

    return img


# テスト
if __name__ == '__main__':
    p = Param()
    p = default_param(p)
    p.width = 1920
    p.height = 1080
    img = generate(p)
    
    img.show("stripe.png")

