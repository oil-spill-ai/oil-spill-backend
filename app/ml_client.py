import os
from PIL import Image, ImageDraw


def run_mock_model(folder_path: str):
    # Заглушка — рисует красный прямоугольник на каждой картинке
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(folder_path, filename)
            image = Image.open(path)
            draw = ImageDraw.Draw(image)
            width, height = image.size
            draw.rectangle([width//4, height//4, width*3//4, height*3//4], outline="red", width=5)
            image.save(path)
