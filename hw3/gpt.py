import os
import requests
import json
import logging
import time
from datetime import datetime

from config import LOGS_PATH, GPT_MODEL, MAX_MODEL_TOKENS, MODEL_TEMPERATURE

TOKEN_PATH = 'creds/gpt_token.json'
FOLDER_ID_PATH = 'creds/gpt_folder_id.txt'

logging.basicConfig(filename=LOGS_PATH, level=logging.DEBUG,
                    format="%(asctime)s %(message)s", filemode="w")


token = ''

with open(FOLDER_ID_PATH, 'r') as f:
    folder_id = f.read().strip()


# # Подсчитывает количество токенов в сессии
# def count_tokens_in_dialogue(messages: sqlite3.Row) -> int:
#     # token = get_creds()
#     headers = {
#         'Authorization': f'Bearer {token}',
#         'Content-Type': 'application/json'
#     }
#     data = {
#        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
#        "maxTokens": MAX_MODEL_TOKENS,
#        "messages": []
#     }
#
#     for row in messages:
#         data["messages"].append(
#             {
#                 "role": row["role"],
#                 "text": row["content"]
#             }
#         )
#
#     return len(
#         requests.post(
#             "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
#             json=data,
#             headers=headers
#         ).json()["tokens"]
#     )


# Подсчитывает количество токенов в тексте
def count_tokens(text: str) -> int:
    token = get_creds()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json={"modelUri": f"gpt://{folder_id}/yandexgpt/latest", "text": text},
            headers=headers
        ).json()['tokens']
    )


def create_new_token():
    """Создание нового токена"""
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}

    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            # Добавляем время истечения токена к текущему времени
            token_data['expires_at'] = time.time() + token_data['expires_in']
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Token created")
        else:
            logging.error(f"Failed to retrieve token. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred while retrieving token: {e}")


def get_creds():
    """Получение токена и folder_id из yandex cloud command line interface"""
    try:
        with open(TOKEN_PATH, 'r') as f:
            d = json.load(f)
            expiration = d['expires_at']
        if expiration < time.time():
            create_new_token()
    except:
        create_new_token()

    with open(TOKEN_PATH, 'r') as f:
        d = json.load(f)
        token = d["access_token"]

    return token


def create_prompt(subject, prompt_by_level) -> str:
    """Создание промпта для YaGPT"""

    prompt = f'\nТы бот-помощник, который задает вопросы по такому предмету, как {subject}\n. '
    prompt += prompt_by_level
    prompt += "\nТы задаешь вопросы по предмету, а пользователь пытается на них ответить\n"
    prompt += f"\nЗадай любой вопрос по предмету {subject}, но не давай ответ"

    return prompt


def ask_gpt(collection):
    """Запрос к Yandex GPT"""

    # Получаем токен и folder_id, так как время жизни токена 12 часов
    token = get_creds()

    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        "modelUri": f"gpt://{folder_id}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": MODEL_TEMPERATURE,
            "maxTokens": MAX_MODEL_TOKENS
        },
        "messages": []
    }

    for row in collection:
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logging.debug(f"Response {response.json()} Status code:{response.status_code} Message {response.text}")
            result = f"Status code {response.status_code}. Подробности см. в журнале."
            return result
        result = response.json()['result']['alternatives'][0]['message']['text']
        logging.info(f"Request: {response.request.url}\n"
                     f"Response: {response.status_code}\n"
                     f"Response Body: {response.text}\n"
                     f"Processed Result: {result}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        result = "Произошла непредвиденная ошибка. Подробности см. в журнале."

    return result


if __name__ == '__main__':
    pass
