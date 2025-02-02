from display.display import EInkDisplay
from PIL import Image
import os

if __name__ == "__main__":
    eInkDisplay = EInkDisplay(984, 1304)

    # Load the images saved by render.py
    directory = '/home/pi/inkal/render'
    red_image_path = os.path.join(directory, 'red_image.png')
    black_image_path = os.path.join(directory, 'black_image.png')

    red_image = Image.open(red_image_path)
    black_image = Image.open(black_image_path)

    # Display the images
    eInkDisplay.display(black_image, red_image)