# ImageConverter

画像を変換するコマンドラインツール

## 環境

必須なものは以下。

```
ImageConverter
├─dist
│  └─imgconv
│    └─main.py
└─poppler
```

- Python 3.9
  - 多分3.6とかでも動く。
- PDFを画像に変換するする場合には、popplerが必要です。popplerのフォルダをdistと同じ階層に置いてください。
  - [Windows版](https://github.com/oschwartz10612/poppler-windows)など。


`pip install -r requirements.txt`

開発はpipenvで作成した仮想環境で行っています。詳しくは[CONTRIBUTION.md](CONTRIBUTION.md)にて。

## 使い方

`pip install https://github.com/Take-Me1010/ImageConverter.git`とすれば、簡単に導入できます。成功すると、以下のようにヘルプが表示されると思います。

```
> imgconv -h
usage: imgconv [-h] -i INPUTS [INPUTS ...] -o OUTPUT [-dpi DPI] [--crop] [--round] [--round-rate ROUND_RATE]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTS [INPUTS ...], --inputs INPUTS [INPUTS ...]
                        pngなどの画像ファイル
  -o OUTPUT, --output OUTPUT
                        出力ファイル/ディレクトリ. 特殊変数として ${stem}, ${dir}を使って指定できる。
  -dpi DPI, --dpi DPI   dpiを指定する
  --crop                画像を正方形に加工するか。
  --round               icoへ変換時、角丸にトリミングを行ってから処理をするか。
  --round-rate ROUND_RATE
                        角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。
```

`pip install`でモジュールを汚したくない場合、次節で述べる、エイリアスなどを設定して対応してください。

### Windows (Power Shell)

1. profileを開いて

```ps1
notepad $profile
# or code $profile
```

2. 以下の文言を追加。

```ps1
function imgconv() {
    python -u path/to/imageConverter/dist/main.py $args
}
```

### Linux系統

profileに上記のようなエイリアスを登録してください。

## 機能紹介

現在

- 画像の拡張子を変換する
- pdfから画像へ変換する

を実装しています。

### 画像を変換する

PDF以外を入力画像に指定した場合です。

- `--crop`オプションを指定すると正方形にトリミングされます。
- `--round`オプションを指定すると、角丸正方形でトリミングします。

```
imgconv .\example\hakase4_laugh.png --crop -o .\example\hakase4_laugh.ico
```

Before <---> After

![example/hakase4_laugh.png](example/hakase4_laugh.png)![example/hakase4_laugh.ico](example/hakase4_laugh.ico)

(画像: いらすとや)


```
imgconv .\example\single_color.jpg --crop --round -o .\example\single_color.ico
```

Before <---> After

![](example/single_color.jpg)    ![](example/single_color.ico)

この半径はオプション引数で変更できます。デフォルメでは5になっています。
--round-rateが2の時、円になります。数字が大きいと小さな半径になります。
なお半径の計算式は正方形の長さ`size`を`round-rate`で割る、つまり`r = size // round_rate`です。

```
imgconv .\example\single_color.jpg --round --round-rate 2 -o .\example\single_color_rate_2.ico
```

![](example/single_color_rate_2.ico)

`--round-rate 10`の場合は以下。

![](example/single_color_rate_10.ico)


### glob形式による入力・出力名の指定


`*.py`などの、`pathlib.Path.glob`に対応した入力を受け付けています。
また、特殊変数として`${stem}, ${dir}`を使うことができます。

`${stem}`は変換する対象のファイルの、拡張子を除いた名前です。
また、`${dir}`は変換する対象のファイルが存在するフォルダです。
全く同じフォルダに、拡張子だけ変えて保存するには`-o '${dir}/${stem}.png'`のように出力を指定します。

```
imgconv -i .\example\*.jpg -o '.\example\${stem}_round5.png' --crop --round --round-rate 5
```

Before <---> After

![](./example/single_color.jpg)
![](./example/single_color_round5.png)



※パワーシェルなどでは$は予約語なので、`''`で囲む必要があります。
