from io import BytesIO
from uuid import uuid4

from PIL import Image
from aiohttp import ClientSession
from pydub import AudioSegment


def ogg_to_wav(source: str) -> str:
    dest = source.replace('.ogg', '.wav')
    file = AudioSegment.from_file(source)
    file.export(dest, format='wav')
    return dest


async def load_image(url: str) -> str:
    path = f'image-{uuid4()}.jpg'
    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
    with open(path, 'wb') as f:
        f.write(data)
    return path


def has_transparency(img: Image) -> bool:
    if img.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True
    return False


def convert_image(path: str) -> bytes:
    image = Image.open(path)
    width, height = 512, 512
    image = image.convert("RGBA").resize((width, height))

    pixels_data = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            if pixels_data[x, y] == (255, 255, 255, 255):
                pixels_data[x, y] = (255, 255, 255, 0)

    byte_stream = BytesIO()
    image.save(byte_stream, format='PNG')
    byte_array = byte_stream.getvalue()
    return byte_array
