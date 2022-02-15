"""
CLIのパーサー部分を記述したモジュール。
"""
from typing import NamedTuple
import argparse
from pathlib import Path


class Args(NamedTuple):
    """パーサーで取得した変数を補間するための、仮のタイプ定義。

    """
    input: Path
    output: Path
    dpi: int
    round: bool
    round_rate: int


def parse() -> Args:
    """ コマンドラインをパースした結果を返す """
    parser = argparse.ArgumentParser()

    parser.add_argument("input", type=Path, help="pngなどの画像ファイル")
    parser.add_argument("-o", "--output", type=Path, required=True,
                        help="出力ファイル")
    parser.add_argument("-dpi", "--dpi", type=int, default=150, help="dpiを指定する")

    parser.add_argument("--round", action="store_true", help="icoへ変換時、角丸にトリミングを行ってから処理をするか。")
    parser.add_argument("--round-rate", type=int, default=5, help="角丸にトリミングする際の、サイズに対する半径の比。大きいと半径は小さくなる。2でピッタリな円になる。")

    args = parser.parse_args()

    return args  # type: ignore
