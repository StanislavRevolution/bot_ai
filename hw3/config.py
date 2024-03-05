LOGS_PATH = 'logs.txt'

DB_DIR = 'db'
DB_NAME = 'gpt_helper.db'
DB_TABLE_PROMPTS_NAME = 'prompts'

TOKEN = ""
# Модель, которую используем
GPT_MODEL = 'yandexgpt'
# Ограничение на выход модели в токенах
MAX_MODEL_TOKENS = 1000
# Креативность GPT (от 0 до 1)
MODEL_TEMPERATURE = 0.6

# Каждому пользователю даем 3 сеанса общения, каждый сеанс это новый help_with
MAX_SESSIONS = 3
# Каждому пользователю выдаем 1500 токенов на 1 сеанс общения
MAX_TOKENS_IN_SESSION = 1500
