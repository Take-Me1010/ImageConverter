import pefile
import pdf2image
import argparse
import io
import logging
import struct
from PIL import ImageFilter, UnidentifiedImageError, ImageDraw, Image
from typing import Any, NamedTuple, Union, List, Optional, Dict
from pathlib import Path



def from_rgb(r: int, g: int, b: int) -> str:
    """ RGBでターミナルで使える文字色を返す """
    return f"\033[38;2;{r};{g};{b}m"


def bg_from_rgb(r: int, g: int, b: int) -> str:
    """ RGBでターミナルで使える背景色を返す """
    return f"\033[48;2;{r};{g};{b}m"


class Colors:
    """色の名前空間

    Reference
        - https://www.nomuramath.com/kv8wr0mp/
        - https://kaworu.jpn.org/kaworu/2018-05-19-1.php
    """
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    COLOR_DEFAULT = '\033[39m'  # 文字色をデフォルトに戻す
    BG_BLACK = '\033[40m'  # (背景)黒
    BG_RED = '\033[41m'  # (背景)赤
    BG_GREEN = '\033[42m'  # (背景)緑
    BG_YELLOW = '\033[43m'  # (背景)黄
    BG_BLUE = '\033[44m'  # (背景)青
    BG_MAGENTA = '\033[45m'  # (背景)マゼンタ
    BG_CYAN = '\033[46m'  # (背景)シアン
    BG_WHITE = '\033[47m'  # (背景)白
    BG_DEFAULT = '\033[49m'  # 背景色をデフォルトに戻す

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERSE = '\033[07m'
    END = '\033[0m'

    ORANGE = from_rgb(255, 165, 0)


class ColorizedStreamFormatter(logging.Formatter):
    """色を付けてログ出力するためのフォーマッター

    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style="%") -> None:
        if fmt is not None:
            fmt = fmt.replace("%(name)s", Colors.CYAN + "%(name)s" + Colors.END)
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def format(self, record: logging.LogRecord) -> str:
        fmt = self._style._fmt
        new_levelname = {
            "DEBUG": Colors.ORANGE,
            "INFO": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "CRITICAL": Colors.BOLD + Colors.RED
        }[record.levelname] + "%(levelname)s" + Colors.END

        fmt = fmt.replace("%(levelname)s", new_levelname)

        self._style._fmt = fmt
        return super().format(record)


class Logger(logging.Logger):
    """CLI用のLogger

    """

    def __init__(self, name: str, level: Union[str, int] = logging.INFO) -> None:
        super().__init__(name)

        format_string: str = '[%(name)s] [%(levelname)s] %(message)s'

        stream_handler = logging.StreamHandler()
        formatter = ColorizedStreamFormatter(format_string)
        stream_handler.setFormatter(formatter)
        self.addHandler(stream_handler)
        self.setLevel(level)
"""
CLIのパーサー部分を記述したモジュール。
"""


class Args(NamedTuple):
    """パーサーで取得した変数を補間するための、仮のタイプ定義。

    """
    inputs: List[str]
    output: str
    dpi: int
    crop: bool
    round: bool
    round_rate: int


def parse(*args, **kwargs) -> Args:
    """ コマンドラインをパースした結果を返す """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--inputs", required=True, nargs="+", help="pngなどの画像ファイル")
    parser.add_argument("-o", "--output", required=True,
                        help="出力ファイル/ディレクトリ. 特殊変数として ${stem}, ${dir}を使って指定できる。")
    parser.add_argument("-dpi", "--dpi", type=int, default=150, help="dpiを指定する")

    parser.add_argument("--crop", action="store_true", help="画像を正方形に加工するか。")
    parser.add_argument("--round", action="store_true", help="icoへ変換時、角丸にトリミングを行ってから処理をするか。")
    parser.add_argument("--round-rate", type=int, default=5, help="角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。")

    namespace: Args = parser.parse_args(*args, **kwargs)        # type: ignore

    return namespace
"""
Windows PE EXE icon extractor.
TODO: resolve linting error

The MIT License (MIT)
Copyright (c) 2022 Take-Me1010

The class IconExtractor is based on https://github.com/jlu5/icoextract .
I change logger (before: global variable) into its class attribute.
I use this module to implement the feature to extract an ico file from an exe file.

Copyright (c) 2015-2016 Fadhil Mandaga
Copyright (c) 2019 James Lu <james@overdrivenetworks.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


GRPICONDIRENTRY_FORMAT = ('GRPICONDIRENTRY',
                          ('B,Width', 'B,Height', 'B,ColorCount', 'B,Reserved',
                           'H,Planes', 'H,BitCount', 'I,BytesInRes', 'H,ID'))
GRPICONDIR_FORMAT = ('GRPICONDIR', ('H,Reserved', 'H,Type', 'H,Count'))


class IconExtractorError(Exception):
    pass


class NoIconsAvailableError(IconExtractorError):
    pass


class InvalidIconDefinitionError(IconExtractorError):
    pass


class IconExtractor():
    """IconExtractor from exe file.

    This class is fully based on great repo https://github.com/jlu5/icoextract

    """

    def __init__(self, filename: str, logger: logging.Logger):
        self.filename = filename
        self.logger = logger
        # Use fast loading and explicitly load the RESOURCE directory entry. This saves a LOT of time
        # on larger files
        self._pe = pefile.PE(filename, fast_load=True)
        self._pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])

        if not hasattr(self._pe, 'DIRECTORY_ENTRY_RESOURCE'):
            raise NoIconsAvailableError(f"{filename} has no resources")

        # Reverse the list of entries before making the mapping so that earlier values take precedence
        # When an executable includes multiple icon resources, we should use only the first one.
        resources = {rsrc.id: rsrc for rsrc in reversed(self._pe.DIRECTORY_ENTRY_RESOURCE.entries)}

        self.groupiconres = resources.get(pefile.RESOURCE_TYPE["RT_GROUP_ICON"])
        if not self.groupiconres:
            raise NoIconsAvailableError(f"{filename} has no group icon resources")
        self.rticonres = resources.get(pefile.RESOURCE_TYPE["RT_ICON"])

    def list_group_icons(self):
        """
        Returns a list of group icon entries.
        """
        return [(e.struct.Name, e.struct.OffsetToData)
                for e in self.groupiconres.directory.entries]

    def _get_group_icon_entries(self, num=0):
        """
        Returns the group icon entries for the specified group icon in the executable.
        """
        groupicon = self.groupiconres.directory.entries[num]
        if groupicon.struct.DataIsDirectory:
            # Select the first language from subfolders as needed.
            groupicon = groupicon.directory.entries[0]

        # Read the data pointed to by the group icon directory (GRPICONDIR) struct.
        rva = groupicon.data.struct.OffsetToData
        size = groupicon.data.struct.Size
        data = self._pe.get_data(rva, size)
        file_offset = self._pe.get_offset_from_rva(rva)

        grp_icon_dir = self._pe.__unpack_data__(GRPICONDIR_FORMAT, data, file_offset)
        self.logger.debug(grp_icon_dir)

        if grp_icon_dir.Reserved:
            raise InvalidIconDefinitionError(
                "Invalid group icon definition (got Reserved=%s instead of 0)" % hex(
                    grp_icon_dir.Reserved))

        # For each group icon entry (GRPICONDIRENTRY) that immediately follows, read its data and save it.
        grp_icons = []
        icon_offset = grp_icon_dir.sizeof()
        for idx in range(grp_icon_dir.Count):
            grp_icon = self._pe.__unpack_data__(GRPICONDIRENTRY_FORMAT, data[icon_offset:], file_offset + icon_offset)
            icon_offset += grp_icon.sizeof()
            grp_icons.append(grp_icon)
            self.logger.debug("Got logical group icon %s", grp_icon)

        return grp_icons

    def _get_icon_data(self, icon_ids):
        """
        Return a list of raw icon images corresponding to the icon IDs given.
        """
        icons = []
        icon_entry_lists = {icon_entry_list.id: icon_entry_list for icon_entry_list in self.rticonres.directory.entries}
        for icon_id in icon_ids:
            icon_entry_list = icon_entry_lists[icon_id]

            icon_entry = icon_entry_list.directory.entries[0]  # Select first language
            rva = icon_entry.data.struct.OffsetToData
            size = icon_entry.data.struct.Size
            data = self._pe.get_data(rva, size)
            self.logger.debug(f"Exported icon with ID {icon_entry_list.id}: {icon_entry.struct}")
            icons.append(data)
        return icons

    def _write_ico(self, fd, num=0):
        """
        Writes ICO data to a file descriptor.
        """
        group_icons = self._get_group_icon_entries(num=num)
        icon_images = self._get_icon_data([g.ID for g in group_icons])
        icons = list(zip(group_icons, icon_images))
        assert len(group_icons) == len(icon_images)
        fd.write(b"\x00\x00")  # 2 reserved bytes
        fd.write(struct.pack("<H", 1))  # 0x1 (little endian) specifying that this is an .ICO image
        fd.write(struct.pack("<H", len(icons)))  # number of images

        dataoffset = 6 + (len(icons) * 16)
        # First pass: write the icon dir entries
        for datapair in icons:
            group_icon, icon_data = datapair
            # Elements in ICONDIRENTRY and GRPICONDIRENTRY are all the same
            # except the last value, which is an ID in GRPICONDIRENTRY and
            # the offset from the beginning of the file in ICONDIRENTRY.
            fd.write(group_icon.__pack__()[:12])
            fd.write(struct.pack("<I", dataoffset))
            dataoffset += len(icon_data)  # Increase offset for next image

        # Second pass: write the icon data
        for datapair in icons:
            group_icon, icon_data = datapair
            fd.write(icon_data)

    def export_icon(self, fname, num=0):
        """
        Writes ICO data containing the program icon of the input executable.
        """
        with open(fname, 'wb') as f:
            self._write_ico(f, num=num)

    def get_icon(self, num=0):
        """
        Returns ICO data as a BytesIO() instance, containing the program icon of the input executable.
        """
        f = io.BytesIO()
        self._write_ico(f, num=num)
        return f
"""
CLI本体を定義する。
"""



logger = Logger("imgconv")

POPPLER_PATH = Path(__file__).parent.parent.absolute() / "poppler/bin"


class Preprocessor:
    """前処理を行うクラス

    """

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


def convert_by_pillow(image: Image.Image, img_output: Path):
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
        ".jfif",
        ".jpg",
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
        convert_by_pillow(image, img_output)

    else:
        logger.error(f"The extension {input_format} is not permitted now...")

    logger.info(f"successfully converted {img_input} into {img_output}")


def extract_icon(img_input: Path, img_output: Path, num: int = 0):
    """exeからiconを取り出す

    Args:
        img_input (Path): 入力ファイル(.exe)
        img_output (Path): 出力ファイル名(.ico)
        num (int, optional): 何番目のiconを出力するか. Defaults to 0.
    """
    if img_output.suffix != ".ico":
        logger.error(f"IconExtractor do not support {img_output.suffix} now...")
        logger.warning(f"failed to extract {img_input} into {img_output}.")
        return

    try:
        IconExtractor(str(img_input), logger).export_icon(img_output, num)
    except IconExtractorError as err:
        logger.error(f"during extracting {img_input} into {img_output}, encountered an error: {err}")
        logger.warning("failed to extract.")
    else:
        logger.info(f"successfully extract {img_input} into {img_output}")


def resolve_output_file_path(img_input: Path, out: str) -> Path:
    """outの形式に応じて、出力先のパスを返す

    Args:
        img_input (Path): 入力画像
        out (str): 出力先の情報(ファイルorディレクトリ), ${name}などを含む可能性がある。

    Returns:
        Path: 出力画像のパス
    """
    out = out.replace("${stem}", img_input.stem)
    out = out.replace("${dir}", str(img_input.parent))

    img_output = Path(out)

    if img_output.is_dir():
        raise ValueError("format of the output name is invalid.")

    return img_output


def get_img_inputs_from_user_inputs(inputs: List[str]):
    """ 入力されたファイルを順にイテレーションする """
    for pattern in inputs:
        logger.debug(pattern)
        if Path(pattern).is_absolute():
            yield Path(pattern)

        else:
            for img_input in Path.cwd().glob(pattern):
                yield img_input


def main():
    """ エントリーポイント """
    args = parse()

    img_inputs = args.inputs
    out = args.output

    preprocessor = Preprocessor(do_crop_center=args.crop, do_round=args.round, round_rate=args.round_rate)
    pdf2image_options = {"dpi": args.dpi}

    for img_input in get_img_inputs_from_user_inputs(img_inputs):
        img_output = resolve_output_file_path(img_input, out)
        if img_input.suffix == ".exe":
            extract_icon(img_input, img_output)

        else:
            convert(img_input, img_output, preprocessor, pdf2image_options)


if __name__ == '__main__':
    main()
