import telebot
from telebot import types

from config import MAX_SESSIONS, MAX_TOKENS_IN_SESSION, DB_TABLE_PROMPTS_NAME
from database import get_dialogue_for_user, get_value_from_table, is_value_in_table
from keyboard import menu_keyboard
from info import HELP_COMMANDS, PROMPTS


def get_user_session_id(user_id: int) -> int:
    row = get_value_from_table("session_id", user_id)
    return row['session_id']


def send_session_limit_warning(bot: telebot.TeleBot, chat_id: int, session_id: int):
    if session_id >= (MAX_SESSIONS // 2):
        bot.send_message(
            chat_id,
            f'Вы приближаетесь к лимиту сессий. Номер вашей сессии - {session_id}. '
            f'Всего сессий {MAX_SESSIONS}'
        )


def send_session_limit_exceeded_message(bot: telebot.TeleBot, chat_id: int):
    bot.send_message(
        chat_id,
        'К сожалению, Вы израсходовали лимит сессий 😢\n'
        'Приходите позже)',
        reply_markup=menu_keyboard(HELP_COMMANDS + ['/debug'])
    )


def is_sessions_limit(message: types.Message, bot: telebot.TeleBot) -> bool:
    user_id = message.from_user.id

    if not is_value_in_table(DB_TABLE_PROMPTS_NAME, 'user_id', user_id):
        return False

    session_id = get_user_session_id(user_id)

    if session_id >= MAX_SESSIONS:
        send_session_limit_exceeded_message(bot, message.chat.id)
        return True

    send_session_limit_warning(bot, message.chat.id, session_id)
    return False


def is_valid_text(message: types.Message, bot: telebot.TeleBot) -> bool:
    """
    Проверяет, является ли текст сообщения допустимым.
    Возвращает True, если текст встречается в словаре PROMPTS и у пользователя уже установлены текущие предметы или уровни.
    """
    text = message.text

    if text not in PROMPTS:
        bot.send_message(
            message.chat.id,
            "Такого уровня сложности нет 😕\n"
            "Выбери пожалуйста предмет и уровень с помощью кнопок ниже",
            reply_markup=menu_keyboard(HELP_COMMANDS)
        )
        return False
    return True


def get_total_tokens_in_session(user_id: int) -> int:
    row = get_value_from_table('session_id', user_id)
    session = get_dialogue_for_user(user_id, row['session_id'])

    tokens_in_session = 0
    for record in session:
        tokens_in_session += record['tokens']
    return tokens_in_session


def send_token_limit_message(bot: telebot.TeleBot, chat_id: int):
    bot.send_message(
        chat_id,
        'В рамках данной темы вы вышли за лимит вопросов.\n'
        'Можете начать новую сессию, введя help_with',
        reply_markup=menu_keyboard(HELP_COMMANDS)
    )


def send_token_warning_message(bot: telebot.TeleBot, chat_id: int, all_tokens: int):
    bot.send_message(
        chat_id,
        f'Вы приближаетесь к лимиту в {MAX_TOKENS_IN_SESSION} токенов в этой сессии. '
        f'Ваш запрос содержит суммарно {all_tokens} токенов.'
    )


def is_tokens_limit(message: types.Message, message_tokens: int, bot: telebot.TeleBot) -> bool:
    user_id = message.from_user.id
    all_tokens = message_tokens + get_total_tokens_in_session(user_id)

    if all_tokens >= MAX_TOKENS_IN_SESSION:
        send_token_limit_message(bot, message.chat.id)
        return True

    elif all_tokens >= (MAX_TOKENS_IN_SESSION // 2):
        send_token_warning_message(bot, message.chat.id, all_tokens)
        return False

    return False
