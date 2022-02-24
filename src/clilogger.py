
from typing import Optional, Union
import logging


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
