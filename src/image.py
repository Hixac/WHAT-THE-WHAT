from pathlib import Path

import structlog
from PIL import Image, ImageDraw, ImageFont

from src.core.config import settings


LOGGER = structlog.get_logger(__file__)


# I didn't write a shit here
class ImageTextComposer:
    """Compose multi-line text onto an image's bottom strip with optimal font size."""

    # Constants
    BOTTOM_STRIP_HEIGHT = 100
    MIN_FONT_SIZE = 1
    MAX_FONT_SIZE = 200

    def __init__(self, *, font_path: Path) -> None:
        """
        Initialize the composer with the path to the TrueType font file.

        Args:
            font_path: Path to the .ttf font file.
        """
        self.font_path = font_path
        self.base_image: Image.Image | None = None
        self.canvas: Image.Image | None = None

    def load_base_image(self, image_path: Path) -> None:
        """
        Load the base image from the given path. Exit if not found.

        Args:
            image_path: Path to the input image file.
        """
        try:
            self.base_image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Error: {image_path} not found. Please check file path.")
            exit(1)

    def _create_canvas(self) -> None:
        """Create a new canvas with extra bottom strip and paste the base image on top."""
        if self.base_image is None:
            raise ValueError("Base image not loaded. Call load_base_image() first.")

        self.canvas = Image.new(
            "RGB",
            (self.base_image.width, self.base_image.height + self.BOTTOM_STRIP_HEIGHT)
        )
        self.canvas.paste(self.base_image)

    @staticmethod
    def _line_height(font: ImageFont.FreeTypeFont) -> int:
        """Calculate total line height (ascent + descent) for a given font."""
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

        Args:
            text: Input text.
            font: Loaded font object.
            max_width: Maximum allowed width in pixels.

        Returns:
            List of wrapped lines.
        """
        words = text.split()
        lines = []
        current_line = []
        current_width = 0.0

        for word in words:
            word_width = font.getlength(word)

            # If word itself exceeds max_width, break it character by character
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

    def _calculate_optimal_font(
        self,
        text: str,
        max_width: int,
        max_height: int
    ) -> tuple[ImageFont.FreeTypeFont, list[str]]:
        """
        Binary search for the largest font size that fits the text in the given area.

        Args:
            text: Text to be rendered.
            max_width: Maximum width in pixels.
            max_height: Maximum height in pixels.

        Returns:
            A tuple containing the optimal font object and the list of wrapped lines.
        """
        best_font = None
        best_lines = []
        low, high = self.MIN_FONT_SIZE, self.MAX_FONT_SIZE

        while low <= high:
            mid = (low + high) // 2
            try:
                font = ImageFont.truetype(self.font_path, mid)
            except OSError:
                high = mid - 1
                continue

            lh = self._line_height(font)
            if lh <= 0:
                high = mid - 1
                continue

            max_lines = max_height // lh
            if max_lines == 0:
                high = mid - 1
                continue

            lines = self._wrap_text_to_width(text, font, max_width)
            if len(lines) <= max_lines:
                best_font = font
                best_lines = lines
                low = mid + 1
            else:
                high = mid - 1

        # Fallback to minimal font if nothing fitted
        if best_font is None:
            best_font = ImageFont.truetype(self.font_path, self.MIN_FONT_SIZE)
            best_lines = self._wrap_text_to_width(text, best_font, max_width)

        return best_font, best_lines

    @staticmethod
    def _draw_text_lines(
        draw: ImageDraw.ImageDraw,
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        start_y: int
    ) -> None:
        """
        Draw each line of text starting at start_y with proper line spacing.

        Args:
            draw: ImageDraw object.
            lines: List of text lines.
            font: Font to use.
            start_y: Y-coordinate for the first line.
        """
        y = start_y
        lh = ImageTextComposer._line_height(font)
        for line in lines:
            draw.text((0, y), line, font=font, fill="white")
            y += lh

    def compose(self, *, text: str, input_path: Path, output_path: Path) -> None:
        """
        Full composition pipeline: load image, add text, save result.

        Args:
            input_path: Path to the input image file.
            output_path: Path where the output image will be saved.
        """
        # Load base image
        self.load_base_image(input_path)

        # Create canvas with bottom strip
        self._create_canvas()

        # Define text area dimensions
        max_width = self.base_image.width
        max_height = self.BOTTOM_STRIP_HEIGHT

        # Compute optimal font and wrapped lines
        font, lines = self._calculate_optimal_font(
            text,
            max_width,
            max_height
        )

        if self.canvas is None or self.base_image is None:
            LOGGER.error("Canvas or BaseImage is None for some funny reason")
            raise Exception("Canvas or BaseImage is None for some funny reason")

        # Draw text onto the bottom strip
        draw = ImageDraw.Draw(self.canvas)
        self._draw_text_lines(draw, lines, font, self.base_image.height)

        # Save result
        self.canvas.save(output_path)
        LOGGER.info("Image saved successfully", path=output_path)
