import pdf2image
import argparse
from PIL import ImageFilter, ImageDraw, Image
from logging import Logger, getLogger, INFO
from typing import List, Optional, NamedTuple
from pathlib import Path
"""
CLIのパーサー部分を記述したモジュール。
"""


class Args(NamedTuple):
    """パーサーで取得した変数を補間するための、仮のタイプ定義。

    """
    input: Path
    output: Path
    dpi: int
    round: bool
    round_rate: int


def parse() -> Args:
    """ コマンドラインをパースした結果を返す

    """
    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=Path, help="pngなどの画像ファイル")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="出力ファイル")
    parser.add_argument("-dpi", "--dpi", type=int, default=150, help="dpiを指定する")

    parser.add_argument("--round", action="store_true", help="icoへ変換時、角丸にトリミングを行ってから処理をするか。")
    parser.add_argument("--round-rate", type=int, default=5, help="角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。")

    args = parser.parse_args()

    return args  # type: ignore
"""
画像を正方形で切り出してicoにするスクリプト

ref: https://www.pytry3g.com/entry/pillow
"""



def crop_center(img: Image.Image, crop_width: int, crop_height: int) -> Image.Image:
    """画像の中心から指定したサイズで切り出す

    Args:
        img (Image.Image): 元画像
        crop_width (int): 切り出す幅
        crop_height (int): 切り出す高さ

    Returns:
        Image.Image: 指定したサイズで中心から切り抜いた画像

    Note:
        - [Python, Pillowで画像の一部をトリミング（切り出し/切り抜き）](https://note.nkmk.me/python-pillow-image-crop-trimming/)
    """
    img_width, img_height = img.size
    return img.crop((
        (img_width - crop_width) // 2,
        (img_height - crop_height) // 2,
        (img_width + crop_width) // 2,
        (img_height + crop_height) // 2
    ))


def crop_max_square(img: Image.Image) -> Image.Image:
    """画像からできるだけ大きな正方形を中心から切り出す

    Args:
        img (Image.Image): 元画像

    Returns:
        Image.Image: 正方形の画像。

    Note:
        - [Python, Pillowで正方形・円形のサムネイル画像を一括作成](https://note.nkmk.me/python-pillow-square-circle-thumbnail/)
    """
    if img.size[0] == img.size[1]:
        return img
    else:
        return crop_center(img, min(img.size), min(img.size))


def get_round_mask(img: Image.Image, r: int = 100) -> Image.Image:
    """角丸四角のマスクを生成して返す

    Args:
        img (Image.Image): 元画像
        r (int, optional): 角丸部分の半径. Defaults to 100.

    Returns:
        Image.Image: マスク

    Note:
        - [Pillowを使用して角丸四角を描画する](http://kyle-in-jp.blogspot.com/2019/06/pillow.html?m=1)
    """
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)

    filled_color = "#ffffff"
    draw.rectangle(
        (0, r) + (mask.size[0] - 1, mask.size[1] - 1 - r), fill=filled_color)
    draw.rectangle(
        (r, 0) + (mask.size[0] - 1 - r, mask.size[1] - 1), fill=filled_color)
    draw.pieslice(((0, 0), (r * 2, r * 2)), 180, 270, fill=filled_color)
    draw.pieslice(((0, mask.size[1] - 1 - r * 2), (r * 2, mask.size[1] - 1)), 90, 180, fill=filled_color)
    draw.pieslice(((mask.size[0] - 1 - r * 2, mask.size[1] - 1 - r * 2),
                  (mask.size[0] - 1, mask.size[1] - 1)), 0, 180, fill=filled_color)
    draw.pieslice(((mask.size[0] - 1 - r * 2, 0),
                  (mask.size[0] - 1, r * 2)), 270, 360, fill=filled_color)
    return mask


def get_image_trimmed_round_rectangle(img: Image.Image, radius: int = 100, use_filter: bool = True):
    """丸四角でトリミングされた画像を返す

    Args:
        img (Image.Image): 元画像
        radius (int, optional): 各丸の半径. Defaults to 100.
        use_filter (bool, optional): フィルタをかけるかどうか. Defaults to True.

    Returns:
        Image.Image: 各丸四角でトリミングされた画像
    """
    mask = get_round_mask(img, radius)
    if use_filter:
        mask = mask.filter(ImageFilter.SMOOTH)
    result = img.copy()
    result.putalpha(mask)

    return result


def preprocess(image_input: Path, do_round: bool, round_rate: int = 5) -> Image.Image:
    """前処理で中心を正方形にくり抜く。

    Args:
        image_input (Path): 入力画像
        do_round (bool): 角を丸めるかどうか
        round_rate (int, optional): どの程度の大きさの角丸にするか. Defaults to 5.

    Returns:
        Image.Image: 正方形画像
    """
    img = Image.open(image_input)
    img = crop_max_square(img)

    if do_round:
        r = img.size[0] // round_rate
        img = get_image_trimmed_round_rectangle(img, radius=r)

    return img


def convert_img2ico(img_input: Path, img_output: Path, do_round: bool, round_rate: int = 5):
    """画像をicoに変換する

    Args:
        img_input (Path):入力画像
        img_output (Path): 出力先
        do_round (bool): 角を丸めるかどうか
        round_rate (int, optional): どの程度の大きさの角丸にするか. Defaults to 5.
    """
    img = preprocess(img_input, do_round, round_rate)
    img.save(img_output)
"""
PDFを画像に変換する。

popplerの導入が必須。

ImageConverter/
    |- poppler/
    |   |- bin/
    |
    |- src/
    |   |- pdf2img.py
    ...

となるように配置する。
TODO: パスを自由に指定できるようにする
"""


poppler_path = Path(__file__).parent.parent.absolute() / "poppler/bin"


def convert_pdf2image(img_input: Path, img_output: Path, dpi: int, logger: Optional[Logger] = None):
    """PDFを画像に変換して保存する

    Args:
        img_input (Path): 入力画像
        img_output (Path): 出力先。
        dpi (int): DPIを指定する。
        logger (Optional[Logger], optional): 親Logger. Defaults to None.
    """
    output_format = img_output.suffix
    logger = logger or getLogger(__name__)

    pages: List[Image.Image] = pdf2image.convert_from_path(img_input, dpi, poppler_path=poppler_path)
    if len(pages) == 1:
        pages[0].save(img_output)

    else:
        logger.warn(f"{img_input}が2ページ以上なので、ページごとに分割されて出力されます。")
        folder = img_output.parent
        stem = img_output.stem
        for i, page in enumerate(pages):
            page.save(f"{folder}/{stem}_{i}", output_format)
"""
CLI本体を定義する。
"""


logger = getLogger("imgconv")
logger.setLevel(INFO)


def main():
    args = parse()

    img_input = args.input
    img_output = args.output

    input_format = img_input.suffix
    output_format = img_output.suffix

    if input_format == ".pdf":
        logger.info("pdfを変換します。")
        convert_pdf2image(img_input, img_output, args.dpi, logger=logger)

    elif output_format == ".ico":
        logger.info("icoへ変換します。")
        convert_img2ico(img_input, img_output, args.round, args.round_rate)

    else:
        logger.error(f"拡張子{input_format}は対応している拡張子ではありません。")


if __name__ == '__main__':
    main()
