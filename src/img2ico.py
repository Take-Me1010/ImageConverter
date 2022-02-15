"""
画像を正方形で切り出してicoにするスクリプト

ref: https://www.pytry3g.com/entry/pillow
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


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
