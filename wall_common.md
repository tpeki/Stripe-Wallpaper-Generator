# 共通関数

# ■ wall_common.py

## RGBColor： 色格納クラス (Alphaなし)

### attribute：  r,g, b

  赤、緑、青の色成分情報  r,g,bは各8bit数値

### 初期化:

 - color = RGBColor(r,g,b) もしくは RGBColor((r,g,b))
   r,g,bをattributeに設定
 - color = RGBColor('#rrggbb') もしくは RGBColor('rrggbb')
     rr,gg,bbを16進2桁の数値とみなしてr,g,bに設定

### メンバ関数：

 - ctox()
     色を16進文字列表記('#rrggbb')に変換する
 - ctoi()
     色を数値(r,g,b)に変換する
 - black()
     黒
 - xtoc(str)
     16進文字列表記をRGBColorに代入する
 - itoc(r,g,b)
     3数値をRGBColorに代入する

## 色関連関数

- clip8(x)
   xを8bit数値に制限する(0<= x <=255)
- rgb_random_jitter(color: RGBColor,  jitter: int)
   color の各値を jitter の幅でランダムに変化させたRGBColor を返す
- rated_jitter(color: RGBColor,  jitter_r: int)
    jitter_r(0<= jitter_r <=100) の範囲のランダムな割合で color の各値を変化させたRGBColor を返す
     各色を１つの変化量で変えるため、色合いの変化が生じない
- brightness(color: RGBColor, f:float =1.0, h:float =0.0, s:float =1.0, bg:RGBCo9lor =None)
   HSL空間で色を調整する。 f：明度、h:色合い、s=彩度 で、それぞれ0~1の間の実数。
    (0,0,0)以下になってしまった場合に、bgが指定されていればbgを返す
- rgb_lerp(c1: list, c2: list, t: float )
  c1(3値tuple)とc2(3値tuple)の各値を t:(1-t)でブレンドしたtupleを返す
- rgb_string((r,g,b)) 、 rgb_string([r,g,b]) もしくは rgb_string(s:str)
  - 色指定パラメータを'#rrggbb' の16進文字列色指定にして返す

- to_rgb((r,g,b)) 、 to_rgb([r,g,b])または to_rgb(s:str)
  - 色指定パラメータをr,g,b の数値にして返す


## Param： パラメータ引数クラス

### attribute

- width, height  生成画像のサイズ
- color1 ～ color3  利用色設定 RGBColor
- color_jitter, sub_jitter, sub_jitter2  主に色変動のためのパラメータ 数値 
- pwidth, pheight, pdepth  主に生成パターン要素のサイズのためのパラメータ 数値
- wwidth,wheight,wposx,wposy  メインウィンドウのサイズと位置
- pattern  現在アクティブなモジュール名
- savefile  画像の保存ファイル名 (モジュール名＋0~9のサフィックスを自動付与)

### 初期値設定

- 各モジュールの default_param(p) 関数でモジュールに合わせたデフォルトパラメータを設定

### 関連関数

- is_param(x:str)

  xがGUIで設定可能なパラメータ名であればTrue

## Modules： モジュール情報クラス

### attribute

- modules: list  読み込んだモジュールの名称
- mod_desc: dictionary of str  読み込んだモジュールの説明文
- mod_gui: dictionary of dictionary  読み込んだモジュールで利用するGUI項目と項目の説明文

### 使い方

- modlist = Modues()
  - 空のモジュールリストを生成
- m = search_modules(modlist, args.plugin_dir)
  - mがモジュール本体のlistを持つインスタンス
  - コマンドラインで --plugin_dir=<dir> としてpluginの検索場所を指定することも可
  - modliistは読みこんだモジュールに関する情報を保持するModulesインスタンス

- モジュールで画像を生成する： **generate(p)**
  - モジュール内でこの関数を定義すること。
    モジュールとしての呼び出しは <u>m[<モジュール名>].generate(p)</u>
  - メインプログラムから自動的に呼び出す。内部のdescから呼ぶ場合もあり
  - modlist.modulesで利用できるモジュール名を確認
  - 引数はParameterクラスで渡す
  - 戻り値はImage.Image
- モジュール情報を取得する： **intro(modlist: Modules, module_name)**
  - モジュール内でこの関数を用意すること。
  - メインプログラムから自動的に呼び出される。
  - モジュールの説明文、GUIエレメント設定を取得する
- モジュールの追加パラメータ画面を呼び出す：**desc(p)**
  - モジュール内でこの関数を用意すること。
  - サンプルイメージをクリックした場合、各モジュール内にdesc()が存在すれば呼び出す
  - 各モジュール内で保持する内部パラメータは、<モジュール名>_preserv という名称のdictionaryを用いる
  - パラメータの内容はできるだけ変更せず本体プログラムに戻す
  - desc()内でパラメータを変更した結果をサンプル表示に反映する場合は、descの戻り値にImage.Imageを渡す(端的に言えば return generate(p) とする)
  - desc()内でparamの内容に変更を与える場合、mod_tartanのdesc()を参考に(ファイルロード時に色設定を読み込むようにしており、color1～color3を書き戻している)
- モジュールのデフォルトパラメータを設定：**default_param(p)**
  - モジュール内でこの関数を用意すること。
  - メインプログラムから自動的に呼び出される。
  - 各モジュールに合わせたパラメータをpに設定して返す
- モジュールの説明文： modlist.mod_desc[<モジュール名>]
  - 各モジュールの desc() 関数で返した説明文を保持.
- モジュールで利用するGUI要素： modlist.mod_gui[<モジュール名>]
  - {<要素名>: <説明文>} として利用するGUI要素と、そのキャプションを返す
  - <要素名>はGUI要素名で固定だが、jitterやgeometyは単なる数値なので、generate内でどう使ってもよい
  - <説明文>はgenerate()内でどう使われるかを端的に記載

## 背景画像生成：

- vertical_gradient_rgb(width, height, cstart:RGBColor, cend:RGBColor)
  - 垂直グラデーション画像を生成
  - 戻り値は image.Image
- horizontal_gradient_rgb(width, height, cstart:RGBColor, cend:RGBColor):
  - 水平グラデーション画像を生成
  - 方向以外はverticalと同様
- diagonal_gradient_rgb(width, height, color1:RGBColor, color2:RGBColor):
  - 左上から右下への斜めのグラデーション画像を生成

## その他

- get_pos(event_str:str)

  - TkEasyGUIで eg.Image(enable_events=True) とした場合のマウスイベントのイベント文字列から、座標情報を取り出す

  - event, value = window.read() とした時に、Imageエレメント window['-image-']のイベントとしてマウスイベントが検出された場合の例

  - ```
    layout=[[eg.Image(size=(300,300),key='-img-', enable_events=True)]]
    window = eg.Window('',layout=layout)
    ...
    while True:
      event, value = window.read()
      if event == '-img-' and value['event-type']=='mousedown':
      	x, y = get_pos(str(value['event']))
    ```

  - x,yはimage内の相対座標であることに注意



# ■ filedialog.py

- PySimpleGUI,TkEasyGUIとも、デフォルトファイル名の指定ができないため、簡易ファイルダイアログを作成
- get_openfile(filename: str, filetypes: list of tuple)
  - デフォルトファイル名をfilenameとして、ファイルオープンダイアログを呼び出す
  - filetypesが省略された場合は [('PNG', '*.png'), ] をファイルタイプとする
  - 選択されたファイル名を返す。read用のダイアログのため、存在しないファイルの場合は空文字列''を返す
- get_savefile(filename: str, filetypes: list of tuple)
  - save先の選択なのでファイル名が存在しないファイルだった場合にエラーにならない
