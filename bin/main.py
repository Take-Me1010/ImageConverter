import pdf2image
import argparse
from PIL import ImageDraw, Image, ImageFilter
from typing import NamedTuple, Optional, List
from pathlib import Path
from logging import getLogger, INFO, Logger


class Args(NamedTuple):
    input: Path
    output: Path
    dpi: int
    round: bool
    round_rate: int


def parse() -> Args:
    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=Path, help="pngなどの画像ファイル")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="出力ファイル")
    parser.add_argument("-dpi", "--dpi", type=int, default=150, help="dpiを指定する")
    
    parser.add_argument("--round", action="store_true", help="icoへ変換時、角丸にトリミングを行ってから処理をするか。")
    parser.add_argument("--round-rate", type=int, default=5, help="角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。")

    args = parser.parse_args()

    return args     #type: ignore



def crop_center(img: Image.Image, crop_width: int, crop_height: int) -> Image.Image:
    img_width, img_height = img.size
    return img.crop((
        (img_width - crop_width) // 2,
        (img_height - crop_height) // 2,
        (img_width + crop_width) // 2,
        (img_height + crop_height) // 2
    ))


def crop_max_square(img: Image.Image) -> Image.Image:
    if img.size[0] == img.size[1]:
        return img
    else:
        return crop_center(img, min(img.size), min(img.size))


def get_round_mask(img: Image.Image, r: int = 100) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    rx = r
    ry = r
    filled_color = "#ffffff"
    draw.rectangle(
        (0, ry)+(mask.size[0]-1, mask.size[1]-1-ry), fill=filled_color)
    draw.rectangle(
        (rx, 0)+(mask.size[0]-1-rx, mask.size[1]-1), fill=filled_color)
    draw.pieslice(((0, 0), (rx*2, ry*2)), 180, 270, fill=filled_color)
    draw.pieslice(((0, mask.size[1]-1-ry*2), (rx*2, mask.size[1]-1)), 90, 180, fill=filled_color)
    draw.pieslice(((mask.size[0]-1-rx*2, mask.size[1]-1-ry*2),
                  (mask.size[0]-1, mask.size[1]-1)), 0, 180, fill=filled_color)
    draw.pieslice(((mask.size[0]-1-rx*2, 0),
                  (mask.size[0]-1, ry*2)), 270, 360, fill=filled_color)
    return mask


def get_image_trimmed_round_rectangle(img: Image.Image, radius: int = 100, use_filter: bool = True):
    mask = get_round_mask(img, radius)
    if use_filter:
        mask = mask.filter(ImageFilter.SMOOTH)
    result = img.copy()
    result.putalpha(mask)

    return result


def preprocess(image_input: Path, round: bool, round_rate: int = 5) -> Image.Image:
    img = Image.open(image_input)
    img = crop_max_square(img)

    if round:
        r = img.size[0] // round_rate
        img = get_image_trimmed_round_rectangle(img, radius=r)

    return img

def convert_img2ico(img_input: Path, img_output: Path, round: bool, round_rate: int = 5):
    img = preprocess(img_input, round, round_rate)
    img.save(img_output)


poppler_path = Path(__file__).parent.parent.absolute() / "poppler/bin"

def convert_pdf2image(img_input: Path, img_output: Path, dpi: int, logger: Optional[Logger] = None):
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