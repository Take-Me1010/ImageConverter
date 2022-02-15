# ImageConverter

画像を変換するコマンドラインツール

## 環境

- Python 3.9
- poppler が必要です。binフォルダを含むpopplerフォルダをbin, srcと同じ階層に置いてください。
  - [Windows版](https://github.com/oschwartz10612/poppler-windows)など。

`pip install -r requirements.txt`

開発はpipenvで作成した仮想環境で行っています。

## 使い方

`pip install https://github.com/Take-Me1010/ImageConverter.git`で多分大丈夫。

`imgconv -h`としてうまくいけばおｋ。わざわざ`pip install`で汚したくない場合は直接動作させるようにエイリアスを設定しよう。

### Windows (Power Shell)

1. profileを開いて

```ps1
notepad $profile
# or code $profile
```

2. 以下の文言を追加。

```ps1
function imgconv() {
    python -u path/to/imageConverter/bin/main.py $args
}
```

## 機能紹介

現在
- 画像をicoに変換する
- pdfから画像へ変換する
を実装しています。

### 画像をicoに変換する

Before <---> After

![example/hakase4_laugh.png](example/hakase4_laugh.png)![example/hakase4_laugh.ico](example/hakase4_laugh.ico)

(画像: いらすとや)

事前に正方形にトリミングしておくと良いかもしれません。


また、出力を各丸四角にすることができます。

```
imgconv .\example\single_color.jpg --round -o .\example\single_color.ico
```

Before <---> After

![](example/single_color.jpg)    ![](example/single_color.ico)

この半径はオプション引数で変更できます。
--round-rateが2の時、円になります。数字が大きいと小さな半径になります。
なお半径の計算式は正方形の長さ`size`を`round-rate`で割る、つまり`r = size // round_rate`です。

```
imgconv .\example\single_color.jpg --round --round-rate 2 -o .\example\single_color_rate_2.ico
```

![](example/single_color_rate_2.ico)

`--round-rate 10`の場合は以下。

![](example/single_color_rate_10.ico)

