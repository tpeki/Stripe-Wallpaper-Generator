import numpy as np
from PIL import Image
from wall_common import *

# ストライプ設定
STRIPE_WIDTH = 40
BASE1 = (220, 180, 0)  # 基本色1
BASE2 = (160, 160, 240)  # 基本色2
DIFF_STRIPE = 8  # 色の揺らぎ

# module基本情報
def intro(modlist: Modules, module_name):
    modlist.add_module(module_name, 'ギザギザ模様(Chevlon)',
                       {'color1':'線色1', 'color2':'線色2',
                        'color_jitter':'色差分', 'pwidth':'線幅'})
    return module_name


# おすすめパラメータ
def default_param(p: Param):
    p.color1.itoc(*BASE1)
    p.color2.itoc(*BASE2)
    p.pwidth = STRIPE_WIDTH
    p.color_jitter = DIFF_STRIPE
    return p

def generate(p: Param):
# def chevlon(width, height, swidth, color1, color2, jitter_width):
    # 座標グリッド生成
    width = p.width
    height = p.height
    swidth = p.pwidth
    eps = p.color_jitter

    y, x = np.mgrid[0:height, 0:width]

    # 三角波
    period = swidth*2
    tri_x = np.abs((x % period) - swidth)

    # 赤・白マスク（同じ幅）
    v = tri_x + y
    t = v % period
    red_mask = t < swidth

    # 三角波ライン単位の色揺らぎ
    band = v // period
    max_band = band.max() + 1

    rng = np.random.default_rng()
    jitter_table = rng.integers(-eps, eps+1, size=(max_band, 3),
                                dtype=np.int16)

    # 各ピクセルに対応する揺らぎ
    jitter = jitter_table[band]

    base1 = np.array(p.color1.ctoi(), dtype=np.int16)
    base2 = np.array(p.color2.ctoi(), dtype=np.int16)

    # -------------------------
    # 色合成
    img_array = np.empty((height, width, 3), dtype=np.int16)

    img_array[red_mask] = base1 + jitter[red_mask]
    img_array[~red_mask] = base2 + jitter[~red_mask]

    # clamp
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)

    # -------------------------
    # Bitmap生成
    # -------------------------
    img = Image.fromarray(img_array, "RGB")
    
    return img

if __name__ == '__main__':
    p = Param()
    p = default_param(p)
    p.width = 1920
    p.height = 1080
    image = generate(p)
    image.show()
