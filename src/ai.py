import logging

import openai


class AI:
    MODEL = 'text-davinci-003'

    def __init__(self, api_key: str):
        openai.api_key = api_key

    async def complete(
            self, text: str,
            max_tokens: int = 1500,
            temperature: float = 0.6,
    ) -> str:
        response = await openai.Completion.acreate(
            model=self.MODEL,
            prompt=text,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        completion = response['choices'][0]['text']
        logging.info(f'ChatGPT completion:\n{completion}')
        return completion

    @staticmethod
    async def image(request: str) -> str:
        response = await openai.Image.acreate(
            prompt=request,
            n=1,
            size='512x512'
        )
        return response['data'][0]['url']

    @staticmethod
    async def image_variation(byte_array: bytes) -> str:
        response = await openai.Image.acreate_variation(
            image=byte_array,
            n=1,
            size="512x512"
        )
        return response['data'][0]['url']

    @staticmethod
    async def image_edit(byte_array: bytes, text: str) -> str:
        response = await openai.Image.acreate_edit(
            image=byte_array,
            prompt=text,
            n=1,
            size="512x512"
        )
        return response['data'][0]['url']
