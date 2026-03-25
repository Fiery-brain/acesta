import re

from django.conf import settings
from g4f import Client
from g4f.errors import MissingAuthError as g4fMissingAuthError
from g4f.errors import RateLimitError as g4fRateLimitError
from g4f.errors import ResponseError as g4fResponseError
from g4f.errors import ResponseStatusError as g4fResponseStatusError
from g4f.errors import RetryProviderError as g4fRetryProviderError
from g4f.errors import TimeoutError as g4fTimeoutError
from openai import APIConnectionError
from openai import APIError
from openai import AuthenticationError
from openai import OpenAI
from openai import RateLimitError

from acesta.base.decorators import fallback_chain


def timesince_accusatifier(timesince_str):
    """
    Returns timesince in the accusative case
    :param timesince_str: str
    :return: str
    """
    return timesince_str.replace("неделя", "неделю").replace("минута", "минуту")


def timesince_cutter(timesince_str):
    """
    Returns timesince in cut down format
    :param timesince_str: str
    :return: str
    """
    return timesince_str.split(",")[0]


def request_gpt(question, is_g4f: bool = False):
    """
    Returns response from GPT
    :param question: str
    :param is_g4f: bool
    :return: str
    """
    result = ""

    if not is_g4f:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": question}],
                stream=False,
            )
            result = response.choices[0].message.content

        except (
            AuthenticationError,
            RateLimitError,
            APIConnectionError,
            APIError,
            Exception,
        ):
            pass

    else:

        @fallback_chain(
            settings.LLM_MODELS,
            settings.LLM_PROVIDERS,
            settings.LLM_MAX_RETRIES,
            settings.LLM_BASE_DELAY,
        )
        def _get_recommendations(
            question: str, model: str, provider: str = None
        ) -> str:
            """
            Returns a recommendation
            :param question: str
            :param kwargs: dict
            :return: str
            """

            def get_ai_recommendations(question):
                client = Client()
                try:
                    result = (
                        client.chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"{question}. {settings.RECOMMENDATION_RULES}",
                                }
                            ],
                            web_search=False,
                            provider=provider,
                        )
                        .choices[0]
                        .message.content
                    )
                    result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL)

                except (
                    g4fTimeoutError,
                    g4fResponseError,
                    g4fRateLimitError,
                    g4fResponseStatusError,
                    g4fRetryProviderError,
                    g4fMissingAuthError,
                    RuntimeError,
                ) as e:
                    print(e)
                    raise e

                return (
                    result
                    if all(
                        err not in result
                        for err in [
                            "request limit",
                            "request error",
                            "premium",
                            "upgrade",
                        ]
                    )
                    else ""
                )

            return get_ai_recommendations(question)

        result = _get_recommendations(question)

    return result
