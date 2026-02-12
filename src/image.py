from pathlib import Path
import structlog

from src.core.config import settings
from PIL import Image, ImageDraw, ImageFont


LOGGER = structlog.get_logger(__file__)


class ImageTextComposer:

    VERTICAL_PADDING = 1
    MAX_ALLOWED_LINES = 5
    MIN_FONT_SIZE = 10
    MAX_FONT_SIZE = 50

    def __init__(self, font_path: str | Path = settings.IMPACT_FONT_PATH) -> None:
        self.font_path = Path(font_path)
        self.base_image: Image.Image | None = None
        self.canvas: Image.Image | None = None

    def load_base_image(self, image_path: str | Path) -> None:
        path = Path(image_path)
        if not path.exists():
            LOGGER.error(f"Path doesn't exist", path=path)
            return
        self.base_image = Image.open(path)

    def _create_canvas(self, bottom_height: int) -> None:
        if self.base_image is None:
            LOGGER.error("Base image not loaded. Call load_base_image() first")
            raise ValueError("Base image not loaded. Call load_base_image() first")
        self.canvas = Image.new(
            "RGB",
            (self.base_image.width, self.base_image.height + bottom_height)
        )
        self.canvas.paste(self.base_image)

    @staticmethod
    def _line_height(font: ImageFont.FreeTypeFont) -> int:
        ascent, descent = font.getmetrics()
        return ascent + descent

    @staticmethod
    def _wrap_text_to_width(
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> list[str]:
        """
        Wrap text to fit within max_width. Break words character by character if necessary.
        """
        words = text.split()
        lines = []
        current_line = []
        current_width = 0.0

        for word in words:
            word_width = font.getlength(word)
            # Break long word character by character
            if word_width > max_width:
                for char in word:
                    char_width = font.getlength(char)
                    if current_width + char_width <= max_width:
                        current_line.append(char)
                        current_width += char_width
                    else:
                        lines.append("".join(current_line))
                        current_line = [char]
                        current_width = char_width
            else:
                space_width = font.getlength(" ") if current_line else 0
                if current_width + space_width + word_width <= max_width:
                    if current_line:
                        current_line.append(" ")
                        current_width += space_width
                    current_line.append(word)
                    current_width += word_width
                else:
                    lines.append("".join(current_line))
                    current_line = [word]
                    current_width = word_width

        if current_line:
            lines.append("".join(current_line))
        return lines

    def _optimal_font_for_lines(
        self,
        text: str,
        max_width: int,
        max_allowed_lines: int
    ) -> tuple[ImageFont.FreeTypeFont, list[str]]:
        """
        Binary search for the largest font size that fits the text within the
        maximum allowed number of lines.
        """
        best_font = None
        best_lines = []
        low, high = self.MIN_FONT_SIZE, self.MAX_FONT_SIZE

        while low <= high:
            mid = (low + high) // 2
            try:
                font = ImageFont.truetype(str(self.font_path), mid)
            except OSError:
                high = mid - 1
                continue

            lines = self._wrap_text_to_width(text, font, max_width)
            if len(lines) <= max_allowed_lines:
                best_font = font
                best_lines = lines
                low = mid + 1
            else:
                high = mid - 1

        # Fallback to minimal font if nothing fits
        if best_font is None:
            best_font = ImageFont.truetype(str(self.font_path), self.MIN_FONT_SIZE)
            best_lines = self._wrap_text_to_width(text, best_font, max_width)

        return best_font, best_lines

    @staticmethod
    def _draw_text_lines(
        draw: ImageDraw.ImageDraw,
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        start_y: int
    ) -> None:
        """Draw each line of text starting at start_y with proper line spacing."""
        y = start_y
        lh = ImageTextComposer._line_height(font)
        for line in lines:
            draw.text((0, y), line, font=font, fill="white")
            y += lh

    def compose(
        self,
        *,
        text: str,
        input_path: str | Path,
        output_path: str | Path
    ) -> None:
        self.load_base_image(input_path)

        if self.base_image is None:
            raise Exception("Base image is None")

        max_width = self.base_image.width
        font, lines = self._optimal_font_for_lines(
            text,
            max_width,
            self.MAX_ALLOWED_LINES
        )

        line_height = self._line_height(font)
        strip_height = len(lines) * line_height + 2 * self.VERTICAL_PADDING
        self._create_canvas(strip_height)

        if self.canvas is None:
            raise Exception("Canvas is None")

        draw = ImageDraw.Draw(self.canvas)
        text_y = self.base_image.height + self.VERTICAL_PADDING
        self._draw_text_lines(draw, lines, font, text_y)

        output_path = Path(output_path)
        self.canvas.save(str(output_path))
        LOGGER.info("Image with text saved", output_path=output_path)


def main():
    """For testing shiiet"""
    composer = ImageTextComposer(font_path=settings.IMPACT_FONT_PATH)
    composer.compose(text="Hello world", input_path=settings.FRAME_OUTPUT_PATH, output_path="output_image.jpg")


if __name__ == '__main__':
    main()
