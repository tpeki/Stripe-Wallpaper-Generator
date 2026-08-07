from wall_common import *
import TkEasyGUI as sg
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
import copy
import os.path as pa
import filedialog as fdi
import inspect

lines_preserv = {'shade':{'shift':2, 'alpha':40, 'blur':5,},
                 'radial':{'exclude':240, 'freq':120, 'duty':0.3},
                 'stripe':{'exclude':0, 'pitch':20, 'duty':0.3, 'angle':0},
                 }
Default_Stripe_Color = (192,192,192)

File_types = [('PNG','*.png'),('JPG','*.jpg'),('Any','*.*'),]
FN = {}  # 登録先辞書
    
def intro(efxlist: EfxModules, module_name):
    efxlist.add_module(module_name, 'ストライプを上書き',
                       {'mask': list(FN.keys()),
                        'proc': ['add_stripe',
                                 ]
                        })
    # proc: [(<function>, <usable_subs>),...]
    return module_name


# 保存パラメータがあれば返す
# =========================
def prevset(name, value, funcname, lo=None, hi=None):
    """global辞書の値を取得 name=保存名 value=デフォルト値 funcname=グループ名"""
    retv = lines_preserv.get(funcname, {}).get(name, value)
    
    if lo is not None:
        retv = max(lo, retv)
    if hi is not None:
        retv = min(retv, hi)
    
    return retv


def storehist(name, value, funcname):
    """global辞書に値を保存 name=保存名 funcname=グループ名"""
    if lines_preserv.get(funcname,None) is None:
        lines_preserv[funcname] = {}
    lines_preserv[funcname][name] = value
    return


# 関数登録用デコレータ
def reg(*, display=None):
    """使用例： @reg(display="<Menu String>")
    FN{} に関数情報をすべて登録
    FN.keys()で登録関数名を取得
    FN[name]['func']() で登録関数を実行
    """
    def decorator(func):
        # 関数名
        name = func.__name__

        # 引数情報
        sig = inspect.signature(func)
        params = sig.parameters

        # デフォルト値辞書
        defaults = {
            p.name: p.default
            for p in params.values()
            if p.default is not inspect._empty
        }

        # docstring を description として使う
        description = (func.__doc__ or "").strip()

        # display が指定されていなければ関数名を使う
        disp = display or name

        # 辞書にまとめて登録
        FN[name] = {
            "func": func,
            "display": disp,
            "description": description,
            "defaults": defaults,
            "args": list(params.keys())[2:],
        }

        return func
    return decorator

# MASK functions
@reg(display="Simple Stripes")
def stripe(W, H, cx=None, cy=None, exclude=0, pitch=20, duty=0.4, angle=0.0):
    """W,H: 画像サイズ  cx,cy: 中心位置
    exclude: 非描画半径  pitch:周期(px.)  duty: 白黒比  angle: 角度(水平=90)
    """
    cx = prevset('cx', cx, 'stripe')
    cy = prevset('cx', cx, 'stripe')
    exclude = prevset('exclude', exclude, 'stripe')
    pitch = prevset('pitch', pitch, 'stripe')
    duty = prevset('duty', duty, 'stripe')
    angle = prevset('angle', angle, 'stripe')
    
    if cx is None: cx = W/2
    if cy is None: cy = H/2
    angle = np.deg2rad(angle)

    # グリッド
    y, x = np.ogrid[:H, :W]
    dx = x - cx
    dy = y - cy

    # 回転後の座標系で「縦ストライプ」を作る
    rot = dx * np.cos(angle) + dy * np.sin(angle)
    phase = (rot / pitch) % 1.0  # 周期化
    stripe = (phase < duty)

    if isinstance(exclude, (tuple, list)):
        rx, ry = exclude
        ellipse = (dx / rx) ** 2 + (dy / ry) ** 2 >= 1.0
        mask = stripe & ellipse
        
    elif exclude > 0:
        r = np.sqrt(dx * dx + dy * dy)
        
        mask = stripe & (r >= exclude)
    else:
        mask = stripe

    return Image.fromarray((mask*255).astype(np.uint8), 'L')


@reg(display="Radial Stripes")
def radial(W, H, cx=None, cy=None, exclude=240, freq=120, duty=0.3):
    """W,H : 画像サイズ  cx,cy : 中心位置
    exclude: 中心の非描画半径  freq: 周期  duty: 白黒比(0..1,1=全白)"""

    cx = prevset('cx', cx, 'radial')
    cy = prevset('cx', cx, 'radial')
    exclude = prevset('exclude', exclude, 'radial')
    freq = prevset('freq', freq, 'radial')
    duty = prevset('duty', duty, 'radial')
    
    if cx is None: cx = W/2
    if cy is None: cy = H/2

    y, x = np.ogrid[:H, :W]
    dx = x - cx
    dy = y - cy

    # 角度（0〜2π）
    theta = np.arctan2(dy, dx)
    theta = (theta + np.pi) / (2*np.pi)  # 0〜1 に正規化

    # 角度方向のストライプ (角度 0〜1 をpitch freqとみなして周期化)
    stripe_phase = (theta * freq) % 1.0
    stripe = (stripe_phase < duty)

    if isinstance(exclude, (tuple, list)):
        rx, ry = exclude
        ellipse = (dx / rx) ** 2 + (dy / ry) ** 2 >= 1.0
        mask = stripe & ellipse
        
    elif exclude > 0:
        r = np.sqrt(dx * dx + dy * dy)
        
        mask = stripe & (r >= exclude)
    else:
        mask = stripe

    return Image.fromarray((mask*255).astype(np.uint8), 'L')


# PROC functions
# maskを貼る(numpy版)
def add_stripe(baseimg, mask, stripeimg, shift=2, alpha=40, blur=5,
                   W=1920, H=1080):
    # shift = 30  影のシフト量(pixel)
    # alpha = 90  影の透過度(0-255)
    # blur = 8    影のぼかし半径(pixel)


    W, H = baseimg.size

    if isinstance(mask, None | str):
        if mask in FN.keys():
            mask = FN[mask]['func'](W, H)
        else:
            mask = FN[next(iter(FN))]['func'](W, H)

    # 影
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, alpha), mask=mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    shadow_np = np.array(shadow.convert("RGBA"))
    shifted_np = np.roll(shadow_np, shift=(shift, shift), axis=(0, 1))
    shadow = Image.fromarray(shifted_np, mode="RGBA")

    stripes = Image.new('RGBA', (W,H), (0,0,0,0))
    stripes.paste(stripeimg, (0,0), mask)

    # 合成
    result = baseimg
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, stripes)
    
    return result


def plain_image(W, H, base=(192,192,192), baseadd=(64,64,64), contrast=0.0):
    c = []
    for i in range(3):
        c.append(clip8(base[i]))
        if c[i] < 255 and baseadd[i] > 0:
            c[i] = clip8(np.random.randint(c[i], base[i]+baseadd[i]))
    img = Image.new('RGBA', (W, H), color=tuple(c))

    fg = np.array(img, dtype=np.float32)
    factor = swirl_marble(W,H, swirl=8, contrast=contrast)
    res = (fg * factor[...,None]).astype(np.uint8)
        
    return Image.fromarray(res, mode='RGBA')


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
        if val is None:
            val = ''
        wd = 8 if param == 'exclude' else 4
        lo.append(sg.Input(f'{val}', key=f'-{mask_name}_{param}-', width=wd))

    return lo

def scan_va(va, mask_name):
    args = FN[mask_name]['defaults']
    pre = f'-{mask_name}_'
    for param in args.keys():
        if f'-{mask_name}_{param}-' in va:
            val = va[f'-{mask_name}_{param}-']
            if ',' in val and param == 'exclude':
                rx, ry = val.split(',')
                rx = stoi(rx)
                ry = stoi(ry)
                val = [rx,ry]
                print(f'exclude! <- {val}')
            elif val == 'None' or val == '':
                val = None
                print(f'{param} <- None')
            else:
                val = stoi(val)
                print(f'{param} <- {val}')
            storehist(param, val, mask_name)
    return

    
def getto(va, name, default, lo=None, hi=None):
    key = f'-s_{name}-'
    pv = lines_preserv['shade'].get(name, default)
    
    try:
        v = va[key]
    except KeyError:
        v = ''
        
    retv = stoi(v, default)
    
    if lo:
        retv = max(lo, retv)
    if hi:
        retv = min(retv, hi)

    lines_preserv['shade'][name] = retv
    return retv


def efx(image, p: Param):
    global lines_preserv
    
    dcpy = copy.deepcopy(lines_preserv)
    preview_size = (640,360)
    MASKS = {FN[_]['display']: _ for _ in FN.keys()}

    W, H = p.width, p.height
    if image is None:
        fgimg = plain_image(W,H)
    else:
        fgimg = image.convert('RGBA')
        if fgimg.size != (W,H):
            fgimg = init_fgimg.resize((W,H), resample=Image.LANCZOS)

    # default Bacic Params
    shift = lines_preserv['shade']['shift']
    alpha = lines_preserv['shade']['alpha']
    blur = lines_preserv['shade']['blur']
    bgmenu = ['FG', 'BG', 'File', 'Plain']
    bgind = ['*frontimage*', '*internal*', '*file*', '*plain*']

    base = Default_Stripe_Color
    addv = clip8(255 - max(base))
    swirlcont = 0

    init_bgimg = p.bg(W,H)
    if init_bgimg is None:
        bgfile = bgind[3]
        bgmode = 'Plain'
        bgimg = plain_image(W,H, base=base, baseadd=(addv,addv,addv),
                            contrast=swirlcont)
    else:
        bgfile = bgind[1]
        bgmode = 'BG'
        bgimg = init_bgimg
 
    file_image = None
    fgc, bgc = bg_and_font(base)
     
    # UI panel                
    menu_lo = []
    for i, x in enumerate(FN.keys()):
        menu_lo.append(mask_line(x, True if i == 0 else False))

    bgset = [[sg.Combo(bgmenu, default_value=bgmode, key='-bgsel-',
                       width=5, readonly=True, enable_events=True),
              sg.Text(' Plain: '),
              sg.Button('BaseColor', key='-bgc-', text_color=fgc,
                        background_color=bgc),
              sg.Text('Jitter'), sg.Input(f'{clip8(255-max(*base))}',
                                          key='-badd-', width=4),
              sg.Text('Contrast%'), sg.Input(f'{swirlcont}',
                                             key='-bcont-', width=4),
              sg.Text(' ', expand_x=True),
              ],
             [sg.Checkbox('Swap FG/BG', default=False, key='-swap-'),
              sg.Text(' File:'),
              sg.Button('Select', key='-file1-', background_color='#ffffdd'),
              sg.Text(bgfile, key='-fn1-'),
              ]]
    buttonset = [[sg.Text('', expand_y=True)],
                 [sg.Text(' '*4, expand_x=True),
                  sg.Button('Test', key='-test-'),
                  sg.Button('Ok', key='-ok-', background_color='#ddffdd'),
                  sg.Button('Cancel', key='-can-', background_color='#ffdddd'),
                  ]]

    lo = [[sg.Frame(title='Flavor Type', layout=menu_lo,
                    relief='ridge', expand_x=True)],
          [sg.Image(size=preview_size, key='-timg-')],
          [sg.Frame('Stripes', layout=bgset, relief='ridge'),
           sg.Column(buttonset),],
           ]
           
    src_path = None
    mask_name = next(iter(FN))

    sample = add_stripe(fgimg, mask_name, bgimg) 
   
    wn = sg.Window('Add Flavor', layout=lo)
    
    while True:
        wn['-timg-'].update(data=sample)
        
        ev, va = wn.read()

        if ev == sg.WINDOW_CLOSED or ev == '-can-':
            sample = image
            shade_preserv = dcpy
            break
        elif ev == '-ok-':
            break
        elif ev == '-file1-':
            src_path = fdi.get_openfile(fdi.sanitize_filename(bgfile),
                                        filetypes=File_types)
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

        if '-item-' in va:
            if va['-item-'] in FN:
                mask_name = va['-item-']
                
        scan_va(va, mask_name)
        shift = getto(va, 'shift', shift, 0)
        alpha = getto(va, 'alpha', alpha, 0, 255)
        blur = getto(va, 'blur', blur, 0)

        if va['-bgsel-'] == 'Plain' and bgmode != 'Plain':
            # print('Plain selected')
            bgmode = 'Plain'
            wn['-fn1-'].update(bgind[3])
            addv = stoi(va['-badd-'])
            contrast = min(max(0,stoi(va['-bcont-'])),100)
            bgimg = plain_image(W, H, base=base, baseadd=(addv,addv,addv),
                                contrast=contrast/100)
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
                wn['-fn1-'].update(bgind[1])
                bgimg = init_bgimg
        elif va['-bgsel-'] == 'FG':  # and bgmode != 'FG':
            # print('FG selected')
            bgmode = 'FG'
            wn['-fn1-'].update(bgind[0])
            bgimg = fgimg.copy()

        wn['-bgsel-'].update(bgmode)
                
        if va['-swap-']:
              bg = fgimg
              fg = bgimg
        else:
              fg = fgimg
              bg = bgimg

        sample = add_stripe(fg, mask_name, bg, shift=shift, alpha=alpha,
                                blur=blur)
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
