'''wallpaper : 壁紙用シンプル画像生成
v1.0.0 2025/12/26 stagger-tiled-stripeのパターン生成スクリプト(単発)版
v2.0.0 2025/12/29 モジュール構成にして、複数のパターン作成に対応
v2.0.1 2026/01/01 コマンドラインオプションを追加 (.pywだとヘルプが出ない)
v2.0.2 2026/01/03 色選択部品の挙動を修正。ペンローズタイルモジュール追加
v2.0.3 2026/01/05 Save asダイアログを表示するようにした。
                  CLIの色指定修正(setattrではstrのまま設定してしまう)

協力：Google Gemini; モジュールのアルゴリズム作成支援(numpy使う手があったなんて)
謝辞：Kujira Handさん; TkEasyGUIがなければGUIアプリにしようと思いませんでした
      Microsoft: 鬱陶しいWindowsスポットライトが作成の原動力になりました
'''

import importlib.util as impl
import sys
import os.path as pa
import argparse
import glob
from PIL import Image, ImageDraw
import random
from wall_common import *
import TkEasyGUI as sg
import tkinter as tk
from tkinter import filedialog
import threading
import queue

DEFAULT_MODULE = 'stripe'
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
SAVE_NUM = 3

def search_modules(modlist: Modules, plugin_dir):
    modules = {}

    if plugin_dir is None:
        plugin_dir = pa.dirname(__file__)  # directory part
    plugin_pat = 'mod_*.py'  # filename pattern
    
    for modf in glob.glob(plugin_pat, root_dir=plugin_dir):
        modname = pa.splitext(modf)[0]
        if modname.startswith('mod_'):
            modname = modname[4:]
        
        # print(modf, '---', modname)
        spec = impl.spec_from_file_location(modname, modf)
        module = impl.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)

        if hasattr(module, 'intro'):
            fn = getattr(module, 'intro')
            print( 'module: ', fn(modlist, modname))
            # print(f'Load {modname}')
            modules[modname] = module

    return modules


# モジュールファイルで作成必要なAPI関数
#
#    def intro(modlist: Modules, module_name):
#        modlist.add_module(module_name, 'ストライプ(タイル)',
#                           ['color1', 'color_jitter', 'pwidth', 'pheight',
#                            'sub_jitter'])
#        return module_name
#
#    def default_param(p: Param):  パラメータは例。
#        p.color1.itoc( BASE_R, BASE_G, BASE_B)
#        p.pwidth = STRIPE_WIDTH
#        p.pheight = TILE_HEIGHT
#        p.color_jitter = DIFF_STRIPE
#        p.sub_jitter = DIFF_TILE
#        return p
#
#    def generate(p: Param):  実際の画像描画
#        width = p.width
#        height = p.height
#        base_r, base_g, base_b = p.color1.ctoi()
#        image = Image.new("RGB", (width, height),
#                          color=(base_r, base_g, base_b))
#        return image
#
# モジュールの呼び出し方
# (1) モジュールを検索登録する
# modlist = Modules()
# p = Param()
# m = search_modules(modlist, plugin_dir)
#
# (2) モジュールの関数を呼び出す
# modlist.modules == [module-name1, module-name2, ...] : 導入したモジュール名
# modlist.mod_gui[module-name] : モジュールで利用するGUI項目、入ってるものだけ表示
# m[module-name].default_param(p) : おすすめ初期パラメータを設定
# image = m[module-name].generate(p)  : 画像を生成


def layout(modlist):
    menudef = [['File', ['Save', 'Exit']],
                ['Module', modlist.modules],
                ]
    
    color_column_layout = [[sg.Text('Base Color:', key='-color1-0',
                                    size=(8,1)),
                            sg.Text('0,0,0', key='-color1-1',
                                    size=(9,1)),
                            sg.Button('...', key='-color1-2')
                            ],
                           [sg.Text('Second Color:', key='-color2-0',
                                    size=(8,1)),
                            sg.Text('0,0,0', key='-color2-1',
                                    size=(9,1)),
                            sg.Button('...', key='-color2-2')
                            ],
                           [sg.Text('Third Color:', key='-color3-0',
                                    size=(8,1)),
                            sg.Text('0,0,0', key='-color3-1',
                                    size=(9,1)),
                            sg.Button('...', key='-color3-2')
                            ]]
    jitter_column_layout = [[sg.Text('Color Mod1:', key='-color_jitter-0',
                                    size=(10,1)),
                             sg.Input('0', key='-color_jitter-1',
                                    enable_events=True, size=(3,1))],
                            [sg.Text('Color Mod2:', key='-sub_jitter-0',
                                    size=(10,1)),
                             sg.Input('0', key='-sub_jitter-1',
                                    enable_events=True, size=(3,1))],
                            [sg.Text('Color Mod3:', key='-sub_jitter2-0',
                                    size=(10,1)),
                             sg.Input('0', key='-sub_jitter2-1',
                                    enable_events=True, size=(3,1))],
                            ]
    pattern_column_layout = [[sg.Text('Pattern1:', key='-pwidth-0',
                                    size=(10,1)),
                             sg.Input('0', key='-pwidth-1',
                                    enable_events=True, size=(3,1))],
                            [sg.Text('Pattern2:', key='-pheight-0',
                                    size=(10,1)),
                             sg.Input('0', key='-pheight-1',
                                    enable_events=True, size=(3,1))],
                            [sg.Text('Pattern3:', key='-pdepth-0',
                                    size=(10,1)),
                             sg.Input('0', key='-pdepth-1',
                                    enable_events=True, size=(3,1))],
                            ]
    file_and_button_column = [[sg.Text('File Name:', text_color='#0022ff'),
                               sg.Text('', expand_x=True, key='-fname-')],
                              [sg.Text('')],
                              [sg.Text('', expand_x=True),
                               sg.Button('Redo', key='-redo-',
                                         background_color='#ffffdd'),
                               sg.Button('Save', key='-ok-',
                                         background_color='#ddffdd'),
                               sg.Text('　'),
                               sg.Button('Quit', key='-done-',
                                         background_color='#ffdddd'),
                               ]
                              ]
    layout = [[sg.Menu(menudef, key='-mnu-')],
              [sg.Text('', key='-modname-'), sg.Text(' '),
               sg.Text('', key='-moddesc-', expand_x=True)],
              [sg.Text('',expand_x=True),
               sg.Image(key='-img-', background_color="#7f7f7f",
                    size=(480,270), enable_events=True),
               sg.Text('',expand_x=True)],
              [sg.Column(layout=color_column_layout),
               sg.Column(layout=jitter_column_layout),
               sg.Column(layout=pattern_column_layout, expand_x=True),
               sg.Column(layout=file_and_button_column)]
              ]

    return layout


def hide_param(window, param):
    for x in range(3):
        k = f'-{param}-{x}'
        try:
            window[k].set_disabled(True)
            window[k].update('')
        except KeyError:
            pass
    if param in ('color1', 'color2', 'color3'):
        window[f'-{param}-1'].update(text_color='#000000', bg='#f0f0f0')
        window[f'-{param}-2'].update('  ')        


def show_param(window, param, desc):
    for x in range(3):
        try:
            window[f'-{param}-{x}'].set_disabled(False)
        except KeyError:
            pass
    window[f'-{param}-0'].update(desc)
    if param in ('color1', 'color2', 'color3'):
        window[f'-{param}-2'].update('...')        


def set_module(window, modlist, module_name):
    if module_name not in modlist.modules:
        return False
    window['-modname-'].update(text=module_name)
    window['-moddesc-'].update(text=modlist.mod_desc[module_name])

    for el in PARAMVALS:
        hide_param(window, el)
    
    for el in modlist.mod_gui[module_name].keys():
        desc = modlist.mod_gui[module_name][el]
        # print(f'{module_name} enable; {el} -> {desc}') 
        show_param(window, el, desc)

    window['-fname-'].update(text=module_name)
    return True


def bg_and_font(color):
    if isinstance(color,str):
        rgb = to_rgb(color)
    elif isinstance(color, RGBColor):
        rgb = color.ctoi()

    l = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])/255
    # ガンマ補正なし,閾値0.89が一般的らしいがおじさんの目にやさしく閾値を低く
    if l > 0.70:
        f = '#000000'
    else:
        f = '#ffffff'
    return f, rgb_string(rgb)


def set_param(window, param, mod_gui):
    for elem in PARAMVALS:
        if elem in mod_gui:
            if elem in ('color1','color2','color3'):
                colr = getattr(param, elem)
                fg,bg = bg_and_font(colr)
                r,g,b = colr.ctoi()
                window[f'-{elem}-1'].update(f'{r},{g},{b}',
                                            text_color=fg, bg=bg)
            else:
                try:
                    window[f'-{elem}-1'].update(getattr(param,elem))
                except KeyError:
                    pass
        else:
            hide_param(window, elem)
            
    window['-fname-'].update(param.file_name())
    window.refresh()


def get_savefile(fname):
    root = tk.Tk()
    root.withdraw()

    filename = filedialog.asksaveasfilename(
        title='Save File',
        initialdir='.',
        initialfile=fname,
        filetypes=[("PNG files", "*.png")]
    )

    return filename


def set_window_geom(param:Param, window: sg.Window):
    param.wwidth, param.wheight = window.get_location()
    param.wposx, param.wposy = window.get_size()
    

result_q = queue.Queue()

def long_task(param, modules, modname):
    image = modules[modname].generate(param)
    result_q.put(image)


def get_image_thread(window, param, modules, modname):
    progress = sg.Window('', [[sg.Text('Wait...', text_align='center',
                                       size=(20,10), 
                                       background_color='#f0e070')]],
                         modal=True, no_titlebar=True, grab_anywhere=True,
                         padding_x=5, padding_y=10,
                         element_justification='c', finalize=True)
    threading.Thread(
        target=long_task,
        args=(param,modules,modname),
        daemon=True).start()
    while True:
        pev, pva = progress.read(timeout=50)
        if pev is None:
            image = None
            break
        elif  not result_q.empty():
            image = result_q.get()
            break
    progress.close()
    return image


def gui_main(modlist: Modules, m, param: Param):
    '''gui_main(modlist:Modules, dict-module_funcs, p:Parameter)
        GUI動作メイン処理
    '''
    lo = layout(modlist)
    wn = sg.Window('Wallpaper Factory', layout=lo)
    set_window_geom(param, wn)

    modname = DEFAULT_MODULE
    if set_module(wn, modlist, modname):
        m[modname].default_param(param)
        param.pattern = modname
        set_param(wn, param, modlist.mod_gui[modname])

    image = m[modname].generate(param)
    wn['-img-'].update(data=image)

    print('-- main loop --')
    while True:
        ev, va = wn.read()
        set_window_geom(param, wn)
        # print(ev, isinstance(ev, str), va)

        if ev == sg.WINDOW_CLOSED or ev == 'Exit' or ev == '-done-':
            break
        elif ev == 'Save' or ev == '-ok-':
            base=param.pattern
            fname = param.file_name()
            fname = get_savefile(fname)
            image.save(fname)
            param.savefile = fname
            wn['-fname-'].update(pa.basename(param.savefile))
            continue
        elif ev == '-redo-':
            image = get_image_thread(wn, param, m, modname)
            if image is not None:
                wn['-img-'].update(data=image)
            else:
                print("DON'T CLOSE DIALOGUE")
            continue
        elif ev in modlist.modules:
            modname = ev
            set_module(wn, modlist, modname)
            param.pattern = modname
            param.savefile = ''
            m[ev].default_param(param)
            set_param(wn,param, modlist.mod_gui[modname])

            image = get_image_thread(wn, param, m, modname)
            if image is not None:
                wn['-img-'].update(data=image)
            else:
                print("DON'T CLOSE DIALOGUE")
            continue
        elif ev in ('-color1-2', '-color2-2', '-color3-2'):
            s = getattr(param, ev[1:-2]).ctox().upper()
            new_color = sg.popup_color(default_color=s)
            if new_color.upper() != s:
                setattr(param, ev[1:-2], RGBColor(new_color))
                fg,bg = bg_and_font(new_color)
                r,g,b = to_rgb(bg)
                wn[ev[:-1]+'1'].update(f'{r},{g},{b}',text_color=fg,
                                       background=bg)
            continue            
        elif ev == '-img-' and va['event_type'] == 'mousedown':
            # print('-img-', ev, va)
            if hasattr(m[modname], 'desc'):
                retv = m[modname].desc(param)
                if isinstance(retv, Image.Image):
                    image = retv
                    wn['-img-'].update(data=image)
                # 返り値がimg型なら、imgを更新するというのはどうか
        elif isinstance(ev, str):
            widg = ev[1:-2]
            # print( widg )
            if not is_param(widg):
                continue
            try:
                s = int(wn[ev].get(),10)
            except ValueError:
                s = 0
            if hasattr(param, widg):
                t = int(getattr(param, widg))
                if s != t:
                    setattr(param, widg, s)
            else:
                print('has no attr', ev, 'as', widg)

    wn.close()
    return


def args_set(parser):
    parser.add_argument('--plugin_dir', help='プラグインフォルダ')
    parser.add_argument('--list_modules',action='store_true',
                       help='モジュールリスト表示')
    parser.add_argument('--module', help='モジュールを起動')
    parser.add_argument('--width', type=int, help='生成画像幅')
    parser.add_argument('--height', type=int, help='生成画像高')
    parser.add_argument('--color1', help='基本色指定')
    parser.add_argument('--color2', help='追加色指定2')
    parser.add_argument('--color3', help='追加色指定3')
    parser.add_argument('--jitter1', type=int, help='変動パラメータ1')
    parser.add_argument('--jitter2', type=int, help='変動パラメータ2')
    parser.add_argument('--jitter3', type=int, help='変動パラメータ3')
    parser.add_argument('--pheight', type=int, help='パターン設定1')
    parser.add_argument('--pwidth', type=int, help='パターン設定2')
    parser.add_argument('--pdepth', type=int, help='パターン設定3')
    parser.add_argument('files', nargs='*')
    
                   
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='壁紙ジェネレータ')
    args_set(parser)
    args = parser.parse_args()    
    
    modlist = Modules()
    m = search_modules(modlist, args.plugin_dir)
    # print(modlist, '\n=========')

    param = Param()
    
    param.width = IMAGE_WIDTH if args.width is None else args.width 
    param.height = IMAGE_HEIGHT if args.height is None else args.height

    if args.list_modules:
        print('Modules available:')
        for x in modlist.modules:
            print(f'{x}: {modlist.mod_desc[x]}')            
    elif args.module is None:
        gui_main(modlist, m, param)
    else:
        m[args.module].default_param(param)
        for name in ['jitter1', 'jitter2', 'jitter3',
                     'pwidth', 'pheight', 'pdepth']:
            v = getattr(args, name, None)
            if v is not None:
                setattr(param, name, v)
        for name in ['color1', 'color2', 'color3']:
            v = getattr(args, name, None)
            if v is not None:
                setattr(param, name, RGBColor(v))  # strのままじゃ駄目

        img = m[args.module].generate(param)
        print(f'Generated {args.module}')
        if isinstance(args.files, list):
            if len(args.files) == 0:
                img.show()
                exit()
            else:
                f = args.files[0]
        else:
            f = args.files 
        if pa.splitext(f)[1] != '.png':
            f = pa.splitext(f)[0]+'.png'
        img.save(f)
        print(f'Image saved in {f}')
                
                
        


