import pdf2image
import argparse
from typing import Any, NamedTuple, Dict, List
from pathlib import Path
from PIL import ImageDraw, ImageFilter, UnidentifiedImageError, Image
from logging import INFO, getLogger
"""
CLIのパーサー部分を記述したモジュール。
"""


class Args(NamedTuple):
    """パーサーで取得した変数を補間するための、仮のタイプ定義。

    """
    inputs: List[str]
    output: Path
    dpi: int
    crop: bool
    round: bool
    round_rate: int


def parse() -> Args:
    """ コマンドラインをパースした結果を返す """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--inputs", required=True, nargs="+", help="pngなどの画像ファイル")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="出力ファイル/ディレクトリ")
    parser.add_argument("-dpi", "--dpi", type=int, default=150, help="dpiを指定する")

    parser.add_argument("--crop", action="store_true", help="画像を正方形に加工するか。")
    parser.add_argument("--round", action="store_true", help="icoへ変換時、角丸にトリミングを行ってから処理をするか。")
    parser.add_argument("--round-rate", type=int, default=5, help="角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。")

    args: Args = parser.parse_args()        # type: ignore

    return args
"""
CLI本体を定義する。
"""



logger = getLogger("imgconv")
logger.setLevel(INFO)


POPPLER_PATH = Path(__file__).parent.parent.absolute() / "poppler/bin"


class Preprocessor:
    def __init__(self, *, do_crop_center: bool = False, do_round: bool = False, round_rate: int = 5) -> None:
        self.do_crop_center = do_crop_center
        self.do_round = do_round
        self.round_rate = round_rate

    def preprocess(self, image_path: Path) -> Image.Image:
        """前処理を行った画像を返す

        Args:
            image_path (Path): 入力画像のパル

        Raises:
            UnidentifiedImageError: openに失敗した時

        Returns:
            Image.Image: 前処理された画像
        """
        try:
            image = Image.open(image_path)

        except UnidentifiedImageError as err:
            logger.error(f"Could not open the image file: {image_path}")
            logger.exception(err)
            raise UnidentifiedImageError from err

        if self.do_crop_center:
            image = self.crop_max_square(image)

        if self.do_round:
            r = image.size[0] // self.round_rate
            image = self.get_image_trimmed_round_rectangle(image, radius=r)

        return image

    def crop_center(self, image: Image.Image, crop_width: int, crop_height: int) -> Image.Image:
        """画像の中心から指定したサイズで切り出す

        Args:
            image (Image.Image): 入力画像
            crop_width (int): 切り出す幅
            crop_height (int): 切り出す高さ

        Returns:
            Image.Image: 指定したサイズで中心から切り抜いた画像

        Note:
            - [Python, Pillowで画像の一部をトリミング（切り出し/切り抜き）](https://note.nkmk.me/python-pillow-image-crop-trimming/)
        """
        img_width, img_height = image.size
        return image.crop((
            (img_width - crop_width) // 2,
            (img_height - crop_height) // 2,
            (img_width + crop_width) // 2,
            (img_height + crop_height) // 2
        ))

    def crop_max_square(self, image: Image.Image) -> Image.Image:
        """画像からできるだけ大きな正方形を中心から切り出す

        Args:
            image (Image.Image): 入力画像

        Returns:
            Image.Image: 正方形の画像。

        Note:
            - [Python, Pillowで正方形・円形のサムネイル画像を一括作成](https://note.nkmk.me/python-pillow-square-circle-thumbnail/)
        """
        if image.size[0] == image.size[1]:
            return image
        else:
            return self.crop_center(image, min(image.size), min(image.size))

    def get_round_mask(self, image: Image.Image, r: int = 100) -> Image.Image:
        """角丸四角のマスクを生成して返す

        Args:
            image (Image.Image): 入力画像
            r (int, optional): 角丸部分の半径. Defaults to 100.

        Returns:
            Image.Image: マスク

        Note:
            - [Pillowを使用して角丸四角を描画する](http://kyle-in-jp.blogspot.com/2019/06/pillow.html?m=1)
        """
        mask = Image.new("L", image.size, 0)
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

    def get_image_trimmed_round_rectangle(
            self,
            image: Image.Image,
            radius: int = 100,
            use_filter: bool = True) -> Image.Image:
        """丸四角でトリミングされた画像を返す

        Args:
            image (Image.Image): 入力画像
            radius (int, optional): 各丸の半径. Defaults to 100.
            use_filter (bool, optional): フィルタをかけるかどうか. Defaults to True.

        Returns:
            Image.Image: 各丸四角でトリミングされた画像
        """
        mask = self.get_round_mask(image, radius)
        if use_filter:
            mask = mask.filter(ImageFilter.SMOOTH)
        result = image.copy()
        result.putalpha(mask)

        return result


def connvert_by_pillow(image: Image.Image, img_output: Path):
    """pillowを用いて画像を変換する

    Args:
        img_input (Image.Image): 入力画像
        img_output (Path): 出力画像名
    """
    try:
        image.save(img_output)

    except (ValueError, OSError) as err:
        logger.error("failed to convert!")
        logger.exception(err)


def convert_pdf(img_input: Path, img_output: Path, options: Dict[str, Any]) -> List[Image.Image]:
    """PDFを入力画像として変換する

    Args:
        img_input (Path): 入力画像
        img_output (Path): 出力画像パス
        options (Dict[str, Any]): options for pdf2image.convert_from_path

    Returns:
        List[Image.Image]: images converted from pdf
    """
    pages: List[Image.Image] = pdf2image.convert_from_path(
        img_input, **options, poppler_path=POPPLER_PATH)
    if len(pages) == 1:
        pages[0].save(img_output)

    else:
        out_folder = img_output.with_name(img_output.stem)
        fmt_out = img_output.suffix
        logger.warning(f"{img_input} has more than 2 pages, so outputs will be in {out_folder}")
        out_folder.mkdir(exist_ok=True)

        for i, page in enumerate(pages):
            page.save(out_folder / f"{i}{fmt_out}")

    return pages


def convert(img_input: Path, img_output: Path, preprocessor: Preprocessor, pdf2image_options: Dict[str, Any]):
    """画像・PDFを変換する

    Args:
        img_input (Path): 入力画像
        img_output (Path): 出力画像パス
        preprocessor (Preprocessor): 前処理用インスタンス
        pdf2image_options (Dict[str, Any]): pdf2imageに渡すオプション
    """
    input_format = img_input.suffix
    # output_format = img_output.suffix

    pillow_permit_extensions = [
        ".bmp",
        ".eps",
        ".gif",
        ".icns",
        ".ico",
        ".im",
        ".jpeg",
        ".msp",
        ".pcx",
        ".png",
        ".sgi",
        ".xbm"
    ]

    if input_format == ".pdf":
        convert_pdf(img_input, img_output, pdf2image_options)

    elif input_format in pillow_permit_extensions:
        image = preprocessor.preprocess(img_input)
        connvert_by_pillow(image, img_output)

    else:
        logger.error(f"The extension {input_format} is not permitted now...")

    logger.info(f"successfully converted {img_input} into {img_output}")


def resolve_output_file_path(img_input: Path, out: Path) -> Path:
    """outの形式に応じて、出力先のパスを返す

    Args:
        img_input (Path): 入力画像
        out (Path): 出力先の情報(ファイルorディレクトリ)

    Returns:
        Path: 出力画像のパス
    """
    if out.is_file():
        return out
    else:
        return out / img_input.name


def main():
    args = parse()

    img_inputs = args.inputs
    out = args.output

    preprocessor = Preprocessor(do_crop_center=args.crop, do_round=args.round, round_rate=args.round_rate)
    pdf2image_options = {"dpi": args.dpi}

    for pattern in img_inputs:
        for img_input in Path.cwd().glob(pattern):
            img_output = resolve_output_file_path(img_input, out)
            convert(img_input, img_output, preprocessor, pdf2image_options)


if __name__ == '__main__':
    main()
