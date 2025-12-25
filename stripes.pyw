from PIL import Image, ImageDraw
import random
import TkEasyGUI as sg

# --- 定数設定 ---
COUNT = 10  # 生成枚数
IMAGE_WIDTH = 1920  # 生成サイズ横
IMAGE_HEIGHT = 1080  # 生成サイズ縦
BASE_COLOR_R, BASE_COLOR_G, BASE_COLOR_B = 239, 168, 62  # 基本色
STRIPE_WIDTH = 17  # タイルの幅
STRIPE_HEIGHT = 140  # タイルの高さ
COLOR_DIFF_STRIPE = 48  # ストライプ毎の色の最大変化幅
COLOR_DIFF_TILE = 27  # タイル毎の色の最大変化幅

BASE_NAME = 'Staggered_Tiles'

def generate_staggered_tiled_pattern(width, height, base_color_hex,
                                     stripe_width, stripe_height):
    """
    指定されたパラメータに基づいて、列ごとにY座標がランダムにずれたタイル状の画像を生成します。

    Args:
        width (int): 画像の幅。
        height (int): 画像の高さ。
        base_color_hex (str): RGB基本色の16進数文字列。
        stripe_width (int): タイルの幅。
        stripe_height (int): タイルの高さ。
    """
    
    # 基本色の16進数をRGB値（0-255）に変換
    if base_color_hex.startswith('#'):
        base_color_hex = base_color_hex[1:]
    
    base_color_r = int(base_color_hex[0:2], 16)
    base_color_g = int(base_color_hex[2:4], 16)
    base_color_b = int(base_color_hex[4:6], 16)
    eps = COLOR_DIFF_STRIPE
    zeta = COLOR_DIFF_TILE
    
    orig_height = height
    height = height + stripe_height
    
    image = Image.new("RGB", (width, height),
                      color=(base_color_r, base_color_g, base_color_b))
    draw = ImageDraw.Draw(image)

    last_y_offset = 0
    granurality = min(5, stripe_height/10)
    y_rand_max = int(stripe_height/granurality)

    # 各列の処理
    for x in range(0, width, stripe_width):
        # 列ごとにランダムなYオフセットを決定
        # タイル高さの範囲内でランダムにずらす
        while True:
            column_y_offset = random.randint(0, y_rand_max) * granurality
            if column_y_offset != last_y_offset:
                break
        last_y_offset = column_y_offset
        
        # この列全体で使用する基本色からの変化量を決定
        # 列全体で色が統一されるように調整
        color_offset_r = random.randint(-eps, eps)
        color_offset_g = random.randint(-eps, eps)
        color_offset_b = random.randint(-eps, eps)

        # この列のタイルを描画
        # オフセットを考慮してY座標を計算
        start_y = column_y_offset - stripe_height * (column_y_offset // stripe_height)
        
        while start_y < height:
            # 各タイル固有の色を生成（基本色＋列オフセット＋微調整）
            tile_color_r = max(0, min(255, base_color_r + color_offset_r +
                                      random.randint(-zeta, zeta)))
            tile_color_g = max(0, min(255, base_color_g + color_offset_g +
                                      random.randint(-zeta, zeta)))
            tile_color_b = max(0, min(255, base_color_b + color_offset_b +
                                      random.randint(-zeta, zeta)))

            end_y = start_y + stripe_height
            
            # 画像の境界内で描画領域をクリップ
            draw_start_y = max(0, start_y)
            draw_end_y = min(height, end_y)
            draw_end_x = min(width, x + stripe_width)

            if draw_end_y > draw_start_y and draw_end_x > x:
                 draw.rectangle([x, draw_start_y, draw_end_x, draw_end_y], fill=(tile_color_r, tile_color_g, tile_color_b))
            
            start_y += stripe_height # 次のタイルへ
        
    image = image.crop((0, stripe_height, width, height))
    return image


# スクリプトの実行
if __name__ == "__main__":
    file_name = BASE_NAME + '.png'
    prime_r = BASE_COLOR_R
    prime_g = BASE_COLOR_G
    prime_b = BASE_COLOR_B

    lo = [[sg.Image(key='-img-', background_color=(128,128,128),
                    size=(480,270), resize_type='fit_both')],
          [sg.Text('Prime = #'+
                   f'{prime_r:02x}{prime_g:02x}{prime_b:02x}'),
           sg.ColorBrowse('Change', key='-prime-', enable_events=True),
           sg.Text(f'File Name = {file_name}'),sg.Text('', expand_x=True),
           sg.Text('#------', key='-base-'),
           sg.Button('Redo', key='-no-'),
           sg.Button('Quit', key='-can-'),
           sg.Button('Save', key='-ok-')]]
    
    wn = sg.Window('Wallpaper generator (Stripe)', layout=lo,
                   resizeable=True)

    while True:

        rr = min(prime_r + random.randint(0, COLOR_DIFF_TILE), 255)
        gg = min(prime_g + random.randint(0, COLOR_DIFF_TILE), 255)
        bb = min(prime_b + random.randint(0, COLOR_DIFF_TILE), 255)
        
        base_color = f'#{rr:02x}{gg:02x}{bb:02x}'
        image = generate_staggered_tiled_pattern(
            IMAGE_WIDTH,
            IMAGE_HEIGHT,
            base_color,
            STRIPE_WIDTH,
            STRIPE_HEIGHT
        )

        wn['-base-'].update(text=base_color)
        wn['-img-'].update(data=image)
        wn.refresh()

        ev, va = wn.read()
        if ev == '-can-':
            break
        elif ev == '-ok-':
            image.save(file_name)
            print(f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}のPNG画像が '{file_name}' として生成されました。")
            break
        elif ev == '-prime-':
            prime_hex = va['event'][1:]
            prime_r = int(prime_hex[0:2], 16)
            prime_g = int(prime_hex[2:4], 16)
            prime_b = int(prime_hex[4:6], 16)
            # print(ev, va, '\n', f'#{prime_r:02x}{prime_g:02x}{prime_b:02x}')

    wn.close()
    
