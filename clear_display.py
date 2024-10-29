from display.display import EInkDisplay
from PIL import Image


if __name__ == "__main__":
    eInkDisplay = EInkDisplay(984, 1304)

    black_image = Image.new("1", (1304, 984), 255)
    red_image = Image.new("1", (1304, 984), 255)
    eInkDisplay.display(black_image, red_image)

