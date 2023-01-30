from pydub import AudioSegment


def ogg_to_wav(source: str) -> str:
    dest = source.replace('.ogg', '.wav')
    file = AudioSegment.from_file(source)
    file.export(dest, format='wav')
    return dest
