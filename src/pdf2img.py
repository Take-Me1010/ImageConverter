from logging import Logger, getLogger
from typing import List, Optional
from pathlib import Path

import pdf2image
from PIL import Image

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
