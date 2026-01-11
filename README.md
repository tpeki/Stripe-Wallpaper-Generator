# wallpaper.pyw		壁紙用のシンプルなイメージを生成する
V2.0.5  2026/01/11

## 概要
複雑なことはしません。
Wallpaper用の画像を生成します。

## 必要ライブラリ
Pythonのライブラリとして、以下のものを利用します。pipなどでライブラリをインストールして利用してください。 作成時点の各バージョンを()で追記してあります
- pillow  (12.0.0)
- TkEasyGUI  (1.0.40)
- numpy (2.2.6)  一部モジュールで利用

## 利用方法
一式を同じディレクトリに配置し、pythonにパスが通っている環境で wallpaper.pyw スクリプトを起動してください。
上記ライブラリが入っていれば、モジュール(mod_*.py)が読み込まれた後、GUIが表示されます。

- メニュー 
 - File → 表示されている画像のSave、プログラムの終了
 -  modules → moduleの切替え (切替えるとパラメータは初期値に戻ります)
- 画像下のパラメータを適宜変更してください。
- 右下のRedoボタンを押すと、基本色から乱数で振ったタイルパターンを再作成します。
- 右下のSaveボタンを押すと、表示されているパターンをPNGで保存します。
- Quitボタンは、何もせずに終了します。

なお、画像ファイルの幅・高さはFHDサイズ(1920x1080)でスクリプトに埋め込んでいるので、ほかのサイズにしたい場合はスクリプトを直接修正してください。

## コマンドラインパラメータ
```
usage: wallpaper.pyw [-h] [- plugin_dir PLUGI _DIR] [--list_mod les] [--module 
                    [--height HEIGHT] [--color1 COLOR1] [--color2 COLOR2] [--color3 COLOR3] [--jitter1 JITTER1]
                    [--jitter2 JITTER2] [--jitter3 JITTER3] [--pheight PHEIGHT] [--pwidth PWIDTH] [--pdepth PDEPTH]
                    [files ...]

--width w  --height h : 生成画像サイズを指定
--plugin_dir dirname : プラグインの読み込みディレクトリを指定します。デフォルトは実行スクリプトのあるディレクトリです
--list_modules : 組み込まれるモジュール名の一覧を表示します。 でも.pywなので--helpも--list_modulesも表示されません。悲しみ。

 (以下はバッチ実行時のみ有効なコマンドラインパラメータ)
--moduke modulename ： 指定したモジュールを読み込み、バッチ実行します。ファイル指定があればファイル出力、なければ既定のイメージビューアで表示
--color1 #rrggbb : 基本色color1 (同様にcolor2, color3もあり) を指定します。
--jitter1 n : 基本色変化幅jitter1 (同様にjitter2、jitter3) を指定します。
--pwidth n  --pheight n  --pdepth n : パターンの大きさ/再帰次数など、形状変化パラメータを指定します。
※ ただし、モジュールによってどのパラメータをどういう使い方にしているかが異なるため、GUI版でパラメータを変えた際の違いを確認してください。
```
## Turtle Graphics
- タートルグラフィクスっぽいスタックベースのスクリプトを用意しました。
- 基本は数値を積む、コマンドで消費して結果を積む、という動きになります。
-コマンド一覧は mod_turtle の中にコメントで入れてあります。

## モジュール
- chevron: ギザギザボーダー
- hexmap: グラデ六角タイル
- hexmaze: 森の六角迷路
- hilbert: ヒルベルト曲線
- packingbubble: グラデーション円
- peano: ペアノ曲線
- penrose: ペンローズタイル
- stripe: 縦ストライプ・モダン
- turtle: タートルコマンド描画
- waves: 青海波

## 謝辞
作成にあたり、Google Geminiに生成部分のコーディングなど大幅に支援いただきました。
Microsoftさん、Windowsスポットライトのあまりの鬱陶しさにこんなツールを作るモチベーションが湧きました。
KujiraHandさん、使いやすくて柔軟なTkEasyGUIをありがとう。これがなければGUI化は考えませんでした。




