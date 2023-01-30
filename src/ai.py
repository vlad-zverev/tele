import logging

import openai


class AI:
	MODEL = 'text-davinci-003'

	def __init__(self, api_key: str):
		openai.api_key = api_key

	async def complete(
			self, text: str,
			max_tokens: int = 1000,
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
