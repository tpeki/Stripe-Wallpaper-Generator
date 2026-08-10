from wall_common import *
import numpy as np
from PIL import Image
import TkEasyGUI as sg
import filedialog as fdi

# 外部定数
START_COLOR = (100, 100, 230)
END_COLOR = (36, 124, 136)
MID_COLOR = (224, 120, 54)
ANGLE = 90
MIDDLE_POINT1 = 70
MIDDLE_POINT2 = 50

# 内部定数
Scheme = [
    #type 0  /Desc 1     /colors 2/Angle 3 /Mid1 4   /Mid2 5
    ['flat', 'Flat plain'    , 1,   False,  False,    False],  # 0
    ['2gra', '2colors Linear', 2,   True,   True,     False],  # 1
    ['3gra', '3colors Linear', 3,   True,   True,     False],  # 2
    ['2rad', '2colors Radial', 2,   True,   True,     True ],  # 3
    ['shpe', 'Shaped Radial' , 2,   False,  True,     True ],  # 4
    ]
Default_scheme = 2
Cdis = '#f0f0f0'
Csel = '#ffffdd'
Nsel = Cdis
Chdr = '#989898'

# 不揮発変数
gradation_preserv = {'scheme': Default_scheme}

def intro(modlist: Modules, module_name):
    '''module基本情報'''
    modlist.add_module(module_name,
                       '三色染め分け(グラデーション)',
                       {'color1':'始色', 'color2':'終色', 'color3':'中間色',
                        'pwidth':'角度', 'pheight':'中間位置1%',
                        'pdepth':'中間位置2%'})
    return module_name


def default_param(p: Param):
    '''おすすめパラメータ'''
    p.color1.itoc(*START_COLOR)
    p.color2.itoc(*END_COLOR)
    p.color3.itoc(*MID_COLOR)
    p.pwidth = ANGLE
    p.pheight = MIDDLE_POINT1
    p.pdepth = MIDDLE_POINT2
    return p


# 詳細設定
def desc(p):
    colset = []
    for x in range(3):
        bg = getattr(p, f'color{x+1}')
        fg, bg = bg_and_font(bg)
        colset.append([bg, fg])
        
    init_sc = gradation_preserv['scheme']
    if len(Scheme) <= init_sc or init_sc < 0:
        init_sc = 2
    angle = p.pwidth
    mid1 = min(max(p.pheight, 0), 100)  # 中間位置1(相対位置を%で指定)
    mid2 = min(max(p.pdepth, 0), 100)  # 中間位置2(相対位置を%で指定)

    lines =  [scheme_selector(n, colset, True if n == init_sc else False)
              for n in range(len(Scheme))]
    
    lo = [[sg.Text(size=(2,1)),sg.Text(size=(14,1)),
           sg.Text('S Color',size=(6,1)),
           sg.Text('M Color',size=(6,1)),
           sg.Text('E Color',size=(6,1)),
           sg.Text('Angle',  size=(6,1)),
           sg.Text('Mid1',   size=(6,1)),
           sg.Text('Mid2',   size=(6,1)),
           ],
          [sg.Text(size=(2,1)),
           sg.Text('Scheme', size=(14,1), background_color=Chdr,
                   text_color='white'),
           sg.Button(f'{colset[0][0]}', key='-col1-', size=(6,1),
                     text_color=colset[0][1], background_color=colset[0][0]),
           sg.Button(f'{colset[2][0]}', key='-col3-', size=(6,1),
                     text_color=colset[2][1], background_color=colset[2][0]),
           sg.Button(f'{colset[1][0]}', key='-col2-', size=(6,1),
                     text_color=colset[1][1], background_color=colset[1][0]),
           sg.Input(f'{angle}', key='-angl-', size=(6,1)),
           sg.Input(f'{mid1}', key='-mid1-', size=(6,1)),
           sg.Input(f'{mid2}', key='-mid2-', size=(6,1)),
           ],
          *lines,
          [sg.Text('',expand_x=True),
           sg.Button('Cancel', key='-can-', background_color='#ffdddd'),
           sg.Button('Set ok', key='-ok-', background_color='#ddffdd'),
           ]
          ]

    wn = sg.Window('', lo)
    while True:
        ev,va = wn.read()

        if ev in ('-can-', sg.WINDOW_CLOSED):
            ev = '-can-'
            break
        elif ev == '-ok-':
            break
        elif ev.startswith('-col'):
            n = int(ev[4])
            cc = colset[n-1][0]
            nc = sg.popup_color(f'Select Color{n}', cc, format='tuple')
            fdi.flush_ev(wn)
            if nc != cc:
                fg, bg = bg_and_font(nc)
                colset[n-1] = [bg, fg]
                wn[f'-col{n}-'].update(background_color=bg, text_color=fg,
                                      text=f'{bg}')
                for i in range(len(Scheme)):
                    fl = Scheme[i][2] + 1
                    bb = bg if n < fl else Cdis 
                    print(f'-c{n}_s{i}- background={bb} {fl}')
                    wn[f'-c{n}_s{i}-'].update(background_color=bb)
                wn.refresh()

        elif ev.startswith('-sc_'):
            s = ev[4:-1]
            sno = sum(i+1 if x[0] == s else 0 for i,x in enumerate(Scheme))
            scs = sno - 1
            for i in range(len(Scheme)):
                c = Csel if i == scs else Nsel
                wn[f'-sct_s{i}-'].update(background_color=c)
            wn.refresh()

    wn.close()
    if ev == '-ok-':
        s = va['-scheme-']
        if s.startswith('-sc_'):
            s = s[4:-1]
        sno = sum(i+1 if x[0] == s else 0 for i,x in enumerate(Scheme))
        scheme = sno - 1 if sno > 0 else Default_scheme  #
        gradation_preserv['scheme'] = scheme

        #print(va)
        #print(f'{scheme}: {Scheme[scheme][0]}')

        angl = stoi(va['-angl-'], lo=0, hi=360)
        mid1 = stoi(va['-mid1-'], lo=0, hi=100)
        mid2 = stoi(va['-mid2-'], lo=0, hi=100)

        for x in range(3):
            setattr(p, f'color{x+1}', RGBColor(colset[x][0]))
        p.pwidth = angl
        p.pheight = mid1
        p.pdepth = mid2

        return generate(p)
    else:
        return
        


def scheme_selector(sno, cols, default):
    sc = Scheme[sno]
    cpat = [[cols[0][0],Cdis,Cdis],
            [cols[0][0],Cdis,cols[1][0]],
            [cols[0][0],cols[2][0],cols[1][0]]]
    if 0< sc[2] < 4:
        cpat = cpat[sc[2]-1]
    else:
        cpat = [Cdis,Cdis,Cdis]
    
    line = [sg.Radio('', group_id='-scheme-', key=f'-sc_{sc[0]}-',
                     default=default),  #enable_events=True
            sg.Text(f'{sc[1]}', size=(14,1), key=f'-sct_s{sno}-',
                    background_color=Csel if default else Nsel),
            sg.Button('',key=f'-c1_s{sno}-', size=(6,1),
                      text_color=Cdis, background_color=cpat[0]),
            sg.Button('',key=f'-c3_s{sno}-', size=(6,1),
                      text_color=Cdis, background_color=cpat[1]),
            sg.Button('',key=f'-c2_s{sno}-', size=(6,1),
                      text_color=Cdis, background_color=cpat[2]),
            sg.Text('○' if sc[3] else '×', key=f'-angl_s{sno}-', size=(6,1)),
            sg.Text('○' if sc[4] else '×', key=f'-midl_s{sno}-', size=(6,1)),
            sg.Text('○' if sc[5] else '×', key=f'-mid2_s{sno}-', size=(6,1)),
            ]
    return line
    

# 三色リニアグラデーション
def tricolor(W, H, color1, color2, color3, mid, angle):
    """
    3色を指定した比率で経由するグラデーションを生成する。
    :param mid: color3が配置される位置(%)
    """
    angle_rad = np.deg2rad(angle)
    y, x = np.ogrid[:H, :W]
    
    # 投影距離の計算
    projection = x * np.cos(angle_rad) + y * np.sin(angle_rad)
    
    # 0.0 ～ 1.0 に正規化
    p_min, p_max = projection.min(), projection.max()
    norm_projection = (projection - p_min) / (p_max - p_min)
    
    result = np.zeros((H, W, 3), dtype=np.uint8)
    
    # 補間ポイントの定義 xp: 投影比率 [0.0, midポイント, 1.0]
    xp = [0.0, mid / 100.0, 1.0]
    
    for i in range(3):
        # 各色の成分を取り出し、補間に使う
        fp = [color1[i], color3[i], color2[i]]
        result[..., i] = np.interp(norm_projection, xp, fp)
        
    return Image.fromarray(result, 'RGB')


def radial(W, H, color1, color2, mid1=None, mid2=None, angle=90):
    if mid1 is None:
        cx = W / 2
    else:
        mid1 = min(max(mid1, 0), 100)
        cx = int(W*mid1/100)
    if mid2 is None:
        cy = H / 2
    else:
        mid2 = min(max(mid2, 0), 100)
        cy = int(H*mid2/100)

    angle_rad = np.deg2rad(angle-90)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    y, x = np.ogrid[:H, :W]

    dx = x - cx
    dy = y - cy

    rx = (dx*cos_a + dy*sin_a) / (W / 2)
    ry = (-dx*sin_a + dy*cos_a) / (H / 2)

    d = np.clip(np.sqrt(rx * rx + ry * ry), 0.0, 1.0)

    c1 = np.asarray(color1)
    c2 = np.asarray(color2)

    result = c2 + (c1 - c2) * d[..., None]

    return Image.fromarray(np.round(result).astype(np.uint8), 'RGB')


def shaped(W, H, color1, color2, mid1=None, mid2=None):
    if mid1 is None:
        cx = W / 2
    else:
        mid1 = min(max(mid1, 0), 100)
        cx = int(W*mid1/100)
    if mid2 is None:
        cy = H / 2
    else:
        mid2 = min(max(mid2, 0), 100)
        cy = int(H*mid2/100)

    y, x = np.ogrid[:H, :W]

    dx = np.abs(x - cx)
    dy = np.abs(y - cy)

    rx = max(cx, W - 1 - cx)
    ry = max(cy, H - 1 - cy)

    # Lp距離
    p = 6
    d = (
        (dx / rx) ** p +
        (dy / ry) ** p
    ) ** (1 / p)

    # 外周を1にする
    edge = (
        (rx / rx) ** p +
        (ry / ry) ** p
    ) ** (1 / p)

    d /= edge
    d = np.clip(d, 0.0, 1.0)

    c1 = np.asarray(color1, dtype=float)
    c2 = np.asarray(color2, dtype=float)

    result = c2 + (c1 - c2) * d[..., None]

    return Image.fromarray(np.round(result).astype(np.uint8), 'RGB')


# wallpaper 共通エントリ
def generate(p: Param):
    """指定した角度で2～3色のグラデーション画像を生成する。"""

    width, height = p.width, p.height
    color1 = p.color1.ctoi()
    color2 = p.color2.ctoi()
    color3 = p.color3.ctoi()
    angle = p.pwidth  # degree(整数)を指定
    mid1 = min(max(p.pheight, 0), 100)  # 中間色位置(相対位置を%で指定)
    mid2 = min(max(p.pdepth, 0), 100)  # 中間色位置(相対位置を%で指定)

    scheme = gradation_preserv['scheme']
    if scheme < 0 or len(Scheme) <= scheme:
        scheme = Default_scheme
    
    if scheme == 1:
        # 2色グラデは、color1,color2とcolor1,2の平均値の3色グラデで代替
        c3 = list(clip8((color1[i]+color2[i])/2) for i in range(3))
        return tricolor(width, height, color1, color2, c3, mid1, angle)
    elif scheme == 2:
        return tricolor(width, height, color1, color2, color3, mid1, angle)
    elif scheme == 3:
        return radial(width, height, color1, color2, mid1, mid2,  angle)
    elif scheme == 4:
        return shaped(width, height, color1, color2, mid1, mid2)
    else:
        return Image.new('RGB', (width, height), color1)


if __name__ == '__main__':
    p = Param()
    p.width = 1920
    p.height = 1080
    p = default_param(p)
    img = generate(p)
    img.show()
