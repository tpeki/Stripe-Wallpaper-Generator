from PIL import Image, ImageDraw, ImageFont
import random
import TkEasyGUI as sg
from wall_common import *

# --- 定数設定 ---
PEN_COLOR = (0x40, 0xff, 0xff)  # ペン色
BG_COLOR = (0x88, 0x88, 0x88)  # 背景色
PEN_WIDTH = 40  # ペン幅
PEN_STEP = 10
BACK_JITTER = 50  # 背景色の最大変化幅
INTRCTV = 1

#CMD = '200,100J2R10FR5F255,255,0C200,400J2H10FR5F'
CMD = '65z130,210jfrfr2frfr2frfr2flflf2l4f'\
      'ulfrfd2l4frfr2frfr4frfr2frf'\
      'u2h6fn3fdfrfr2frfr2frfr2flflf2l4f'\
      'u2h2fn3fdrfr2frfr2frfr2frfr4frfr2frf'\
      '200,670j52p255,127,64c2h"Hope your year is "'\
      '250,800j"filled with many "248,64,64c"happy "255,127,64c"moments!"'\
      '1600,950j5p4z255,255,88c2h4f4r2f2l6fu2l4fdn6f2r2frfrfrfr2f'\
      'u3l3fl2fdn6fu4r3fd3l3fu4r3fd2l3f'

tur_preserve = {'cmd': ''}

# module基本情報
def intro(modlist: Modules, module_name):
    modlist.add_module(module_name, '年賀(似非タートル)',
                       {'color1':'ペン色','color2':'背景基本色',
                        'color_jitter':'背景色変化',
                        'pwidth':'ペン幅', 'pheight':'ステップ幅',
                        'pdepth':'対話型=0'})
    return module_name


# おすすめパラメータ
def default_param(p: Param):
    p.color1.itoc(*PEN_COLOR)
    p.color2.itoc(*BG_COLOR)
    p.color_jitter = BACK_JITTER
    p.pwidth = PEN_WIDTH
    p.pheight = PEN_STEP
    p.pdepth = INTRCTV

    return p


def desc(p: Param):
    posx = p.wwidth
    posy = p.wheight + p.wposy

    layout=[[sg.Multiline(tur_preserve['cmd'], readonly=True,
                          text_color='#000000', background_color='#f0eea0',
                          text_align='left', size=(60,10), expand_x=True)],
            [sg.Text('',expand_x=True), sg.Button('Close',key='-d_close-'),
             sg.Text('',expand_x=True)]]
    sdialog = sg.Window('Command String', layout=layout,
                        location=(posx,posy), padding_x=0, padding_y=0,
                        grab_anywhere=True)

    while True:
        ev,va = sdialog.read()
        if ev == '-d_close-':
            break
    sdialog.close()

    return None


'''
TURTLEコマンド
n     F    スタック先頭の数値だけn歩前進 スタックに値が無ければ1歩
n     L/R  スタック先頭の数値だけCCW/CWに回頭 ただし1単位=45度、
           スタックに値が無ければ1とみなす
-     U/D  ペンアップ／ダウン
r,g,b C    スタック先頭3値でペン色を変更
n     P    スタック先頭の値でペン太さ(ピクセル)を変更
x,y   J    スタック先頭2値で絶対座標に移動
-     N    タートルの方向を北(方向0)に変更(初期値)
n     H    タートルの方向をスタック先頭の値にする(0..7)
n     ]    スタック先頭の値をコピーして積む
-     [    スタック先頭の値を捨てる
-     X    スタック先頭の2値を入れ替える
n     ,    nをスタック先頭に積む(数値の後に文字が来たらスタックに積むので実は何もしない)
-     W    現在の座標をスタック先頭にX,Yで積む
n     Z    セルサイズをn×nピクセルにする
n     S    スタック先頭をレジスタ番号とし、次値を#nに(値はスタックに残る)
n     Q    レジスタ#nの値をスタックにPUSH
x,y   +/-/*///^ 四則演算・べき乗
x     ~    符号反転
-     ".." クォート間の文字をカーソル位置に挿入
'''

DIR = [(0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]
REGISTER_SIZE = 10
STACK_SIZE = 32
MAX_PEN_WIDTH = 200
Opcode = ['+', '-', '*', '/', '^']  # 二項演算子
Unary = ['~']  # 単項演算子

class Turtle:
    def __init__(self, dir=0, pen_down=True, size=PEN_WIDTH, step=PEN_STEP,
                 color=RGBColor(PEN_COLOR), x=0, y=0):
        self.dir = dir
        self.pen = pen_down
        self.width = size
        self.color = color
        self.step = step
        self.x = x
        self.y = y
        
        self.lastx = x
        self.lasty = y
        self.register = [0]*REGISTER_SIZE
        self.stack = [0] * STACK_SIZE
        self.sp = -1

    def pop_stack(self, default=0):
        if self.sp < 0:
            return default
        val = self.stack[self.sp]
        self.sp -= 1
        return val

    def push_stack(self,n):
        if self.sp < STACK_SIZE - 1:
            self.sp += 1
            self.stack[self.sp] = n

    def show_stack(self, n):
        val = {}
        val['sp'] = self.sp
        s = []
        if n > STACK_SIZE:
            n = STACK_SIZE
        for i in range(STACK_SIZE):
            s.append(self.stack[i])

        val['stack'] = s
        val['x'] = self.x
        val['y'] = self.y
        val['dir'] = self.dir
        val['pen'] = self.color.ctox() + f' Size={self.width}'
        
        return val
            
        
    def forward(self, draw):
        p = self.pop_stack(1)  # スタックが空なら1
        distance = self.step*p
        self.lastx = self.x
        self.lasty = self.y
        self.x = self.x + DIR[self.dir][0]*distance
        self.y = self.y + DIR[self.dir][1]*distance
        # print(f'Turtle.Forward: ({self.lastx},{self.lasty}) to Dir={self.dir}/{DIR[self.dir]}, Stack={p}, Step={self.step}, Distance={distance}')
        # print(f'   Pendown={self.pen}, New coord = ({self.x},{self.y})')
        if self.pen:
            r = self.width // 2
            c = self.color.ctoi()
            draw.line((self.lastx,self.lasty, self.x,self.y),
                      width=self.width, fill=c)
            draw.circle((self.lastx, self.lasty), r,  fill=c)
            draw.circle((self.x, self.y), r,  fill=c)
            
    
    def right(self):
        p = self.pop_stack(1)  # スタックが空なら1
        self.dir = (self.dir + p) % 8
        # print(f'Turtle.Right: result={self.dir}')

    def left(self):
        p = self.pop_stack(1)  # スタックが空なら1    
        self.dir = (self.dir - p) % 8
        # print(f'Turtle.Left: result={self.dir}')
        
    def north(self):
        self.dir = 0

    def head(self):
        p = self.pop_stack()    
        self.dir = p % 8

    def set_color(self):
        b = self.pop_stack()
        g = self.pop_stack()
        r = self.pop_stack()
        self.color = RGBColor(r,g,b)

    def pen_up(self):
        self.pen = False

    def pen_down(self):
        self.pen = True

    def pen_width(self):
        p = self.pop_stack(10)  # スタックが空なら10
        if p < MAX_PEN_WIDTH:
            self.width = p

    def jump(self):
        y = self.pop_stack()
        x = self.pop_stack()
        self.last_x = self.x
        self.last_y = self.y
        self.x = x
        self.y = y

    def where(self):
        x = self.x
        y = self.y
        self.push_stack(x)
        self.push_stack(y)

    def dup(self):
        x = self.pop_stack()
        self.push_stack(x)
        self.push_stack(x)

    def drop(self):
        self.pop_stack()

    def exchange(self):
        x = self.pop_stack()
        y = self.pop_stack()
        self.push_stack(x)
        self.push_stack(y)

    def zoom(self):
        x = self.pop_stack()
        self.step = x

    def store(self):
        n = self.pop_stack()
        x = self.pop_stack()  # スタックに元の値は残さない
        if 0 <= n < REGISTER_SIZE:
            self.register[n] = x
        # print(f'Turtle.Store[{n}]: pop {x} into register')

    def restore(self):
        n = self.pop_stack()
        if 0 <= n < REGISTER_SIZE:
            self.push_stack(self.register[n])
        # print(f'Turtle.Retore[{n}]: push {self.register[n]}')

    def calc(self, opcode):
        x = self.pop_stack()
        y = self.pop_stack()
        if opcode == '+':
            self.push_stack(x+y)
        elif opcode == '-':
            self.push_stack(x-y)
        elif opcode == '*':
            self.push_stack(x*y)
        elif opcode == '/':
            self.push_stack(x//y)
        elif opcode == '^':
            if -(2**31)< x**y and x**y < 2**31:
                self.push_stack(x**y)
        else:
             self.push_stack(y)  # do nothing
             self.push_stack(x)

    def unary(self, opcode):
        x = self.pop_stack()
        if opcode == '~':
            self.push_stack(-x)
        else:
            self.push_stack(x)

    def put_text(self, draw, s):
        p = min(64, max(int(self.width*2.4),10))
        font = ImageFont.truetype('meiryob.ttc',p)
        draw.text((self.x, self.y), s, self.color.ctox(), font=font)
        bbox = draw.textbbox((self.x, self.y), s, font=font)
        self.last_x = self.x
        self.last_y = self.y
        self.x = int(bbox[2])
        self.y = self.y  # 高さは変えない
        # print(f'Turtle.put_text: {s}, bbox=({bbox})')
        


# コマンドディスパッチテーブル
Commands = {
    'U': Turtle.pen_up,
    'D': Turtle.pen_down,
    'R': Turtle.right,
    'L': Turtle.left,
    'N': Turtle.north,
    'H': Turtle.head,
    'C': Turtle.set_color,
    'P': Turtle.pen_width,
    'J': Turtle.jump,
    'W': Turtle.where,
    ']': Turtle.dup,
    '[': Turtle.drop,
    'X': Turtle.exchange,
    'Z': Turtle.zoom,
    'S': Turtle.store,
    'Q': Turtle.restore
    }


def turtle_draw(draw, turtle, cmds, verbose=False):
    '''turtle_draw(draw: ImageDraw, turtle: Turtle, cmds: str)'''
    if verbose:
        print(f'Command = {cmds}')
    ptr = 0
    while ptr < len(cmds):
        cur = ptr
        if '0' <= cmds[cur] <= '9':  # 連続数字は数値としてスタックに積む
            while True:
                cur += 1
                if cur >= len(cmds) or not ('0' <= cmds[cur] <= '9'):
                    break
            n = int(cmds[ptr:cur])
            turtle.push_stack(n)
            if verbose:
                print( f'{ptr}: push {n}')
            ptr = cur
        elif cmds[cur] == '"':  # テキスト出力
            while True:
                cur += 1
                if cur >= len(cmds) or cmds[cur] == '"':
                    break
            s = cmds[ptr+1:cur]
            turtle.put_text(draw,s)
            if verbose:
                print( f'{ptr}: Command print("{s}")', turtle.show_stack(3))
            ptr = cur+1
        elif cmds[cur].upper() == 'F':  # Fコマンドだけdrawを渡すので別
            if verbose:
                print( f'{ptr}: Command "F"', turtle.show_stack(3))
            turtle.forward(draw)
            ptr += 1
        elif cmds[cur] in Opcode:  # 二項演算子
            if verbose:
                print( f'{ptr}: Calc "{cmds[cur]}"', turtle.show_stack(3))
            turtle.calc(cmds[cur])
            ptr += 1
        elif cmds[cur] in Unary:  # 単項演算子
            if verbose:
                print( f'{ptr}: Unary "{cmds[cur]}"', turtle.show_stack(3))
            turtle.unary(cmds[cur])
            ptr += 1
        else:  # その他のコマンドはディスパッチテーブルで
            if verbose:
                print( f'{ptr}: Command "{cmds[cur]}"', turtle.show_stack(3))
            try:
                Commands[cmds[cur].upper()](turtle)
            except KeyError:
                pass
            ptr += 1
            
    # interpreter end


def edit_layout():
    test_pane = [sg.Image(key='-t_test-', size=(640,360),
                          background_color='gray')
                 ]
    command_pane = [sg.Multiline(key='-t_cmds-', enable_events=True,
                                 enable_key_events=True, size=(80,10),
                                 text_color='black', background_color='white',
                                 text_align='left',
                                 expand_x=True, expand_y=True)
                    ]
    buttons = [[sg.Text('Pattern No.'),
                sg.Input('1', text_align='right', size=(2,1), key='-t_no-'),
                sg.Text('', expand_x=True),
                sg.Button('Clear', key='-t_clr-'),
                sg.Button('Load', key='-t_ld-'),
                sg.Button('Test', key='-t_tst-'),
                sg.Text(' ', expand_x=True),
                sg.Button('Save', key='-t_sv-')]]
    layout = [test_pane, comand_pane, buttons]                

    return layout


def generate(p: Param):
    """
    指定されたパラメータに基づいて、turtleで画像生成する
    """
    width = p.width
    height = p.height
    pen_color = p.color1
    bg_color = p.color2
    jitter = p.color_jitter
    pen_size = p.pwidth
    pen_step = p.pheight
    start_x = p.width // 2
    start_y = p.height // 2
    intrctv = p.pdepth == 0
    
    turtle = Turtle(size=pen_size, step=pen_step, color=pen_color,
                    x=start_x, y=start_y)

    if intrctv:
        print('Coming soon.')
        # cmd = interactive_dialog(p)
        cmd = CMD
    else:
        cmd = CMD

    # 描画イメージの生成・背景作成
    bg_start = rgb_random_jitter(bg_color, jitter)
    bg_end   = rgb_random_jitter(bg_color, jitter)
    image = diagonal_gradient_rgb(width, height, bg_start, bg_end)
    draw = ImageDraw.Draw(image)
        
    turtle_draw(draw, turtle, cmd, verbose=False)
    tur_preserve['cmd'] = cmd

    return image
    

if __name__ == '__main__':
    p = Param()
    p = default_param(p)
    p.width = 1920
    p.height = 1080
    

    print(f'\n==========\nParameters = {p}\n==========\n')
    
    image = generate(p)
    image.show()

# TODO
#  Gemini先生も言っていたが、繰り返し処理区間の定義"{","}"と、
# 条件判断break"!"を追加したい。
