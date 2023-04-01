"""
This module contains the base class for all game assets and image processing.
"""
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

class GameAsset:
    """
    GameAsset is the base class for all game assets.
    """

    def __init__(self, size=50):
        self.emoji = "💩"
        self.path_to_image = None
        self.size = size
        self.image_directory = "images"

    def process_image(self):
        """
        This method checks the if the directory for the image exists and if the image exists.
        If the directory does not exist, it is created.
        If the image does not exist, it is created.
        :return:
        """
        if not os.path.exists(self.image_directory):
            os.makedirs(self.image_directory)
        self.path_to_image = os.path.join(self.image_directory, f"{self.__str__()}.png")
        if not os.path.exists(self.path_to_image):
            self.create_image()
        # self.create_image()

    def create_image(self):
        """
        This method creates an image from an emoji and saves it to the image directory.
        :return:
        """
        # Use an absolute path for the font
        font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"

        # Set the initial font size
        font_size = 160

        font = ImageFont.truetype(font_path, size=font_size)
        img = Image.new("RGBA", (font_size, font_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Get the size of the emoji and calculate the position to center it in the image
        emoji_width, emoji_height = draw.textsize(self.emoji, font=font)
        position = ((font_size - emoji_width) // 2, (font_size - emoji_height) // 2)

        draw.text(position, self.emoji, font=font)

        # Resize the image to the desired size
        # img = img.resize((self.size, self.size))
        img.save(self.path_to_image, "PNG")
