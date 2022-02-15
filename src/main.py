
from logging import getLogger, INFO

logger = getLogger("imgconv")
logger.setLevel(INFO)

from cliparser import parse
from pdf2img import convert_pdf2image
from img2ico import convert_img2ico

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