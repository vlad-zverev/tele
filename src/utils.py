import shutil

from pydub import AudioSegment
from aiohttp import ClientSession
from uuid import uuid4


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
