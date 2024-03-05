import logging
import os.path
import sqlite3
from datetime import datetime

import telebot
from telebot import types

from config import TOKEN, LOGS_PATH, DB_TABLE_PROMPTS_NAME
from gpt import count_tokens, ask_gpt, create_prompt
from info import SUBJECTS, PROMPTS, GREETING_TEXT, HELP_COMMANDS, ALL_COMMANDS, DEV_COMMANDS
from validators import is_sessions_limit, is_tokens_limit, is_valid_text
from database import (
    prepare_db,
    get_dialogue_for_user,
    add_record_to_table,
    get_value_from_table,
    is_value_in_table,
    count_all_tokens_from_db
)
from keyboard import menu_keyboard


logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s", filemode="w"
)

# Создаём бота
bot = telebot.TeleBot(TOKEN)

current_levels = {}
current_subjects = {}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        GREETING_TEXT,
        reply_markup=menu_keyboard(HELP_COMMANDS + DEV_COMMANDS)
    )


@bot.message_handler(commands=['debug'])
def send_logs(message):
    if os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, "rb") as f:
            bot.send_document(message.chat.id, f, reply_markup=menu_keyboard(HELP_COMMANDS + DEV_COMMANDS))
    else:
        bot.send_message(message.chat.id, f"Файл {LOGS_PATH} не найден :(")


@bot.message_handler(commands=['all_tokens'])
def send_tokens(message):
    try:
        all_tokens = count_all_tokens_from_db()
        bot.send_message(
            message.chat.id,
            f'За все время использования бота\n'
            f'Израсходовано токенов - {all_tokens}',
            reply_markup=menu_keyboard(HELP_COMMANDS + DEV_COMMANDS)
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f'Произошла ошибка при получении информации о токенах: {e}'
        )
        logging.debug(f'Произошла ошибка при получении информации о токенах: {e}')


# Обработчик команды /help_with
@bot.message_handler(commands=["help_with_maths", "help_with_history"])
def solve_task(message: types.Message):
    if is_sessions_limit(message, bot):
        return

    user_id: int = message.from_user.id
    subject: str = message.text.split('/help_with_')[1].upper()
    translated_subject: str = SUBJECTS.get(subject)
    current_subjects[user_id]: str = translated_subject

    difficulty_levels: list = list(PROMPTS.keys())

    msg = bot.send_message(
        message.chat.id,
        "Выбери свой уровень знаний:\n"
        "beginner - начинающий\n"
        "intermediate - средний\n"
        "advanced - продвинутый",
        reply_markup=menu_keyboard(difficulty_levels)
    )

    if msg.text not in ALL_COMMANDS:
        bot.register_next_step_handler(msg, get_question)


@bot.message_handler(content_types=['text'])
def answer_handler(message: types.Message):
    user_id: int = message.from_user.id
    user_answer: str = message.text

    if user_answer in HELP_COMMANDS:
        solve_task(message)
        return

    tokens: int = count_tokens(user_answer)

    if is_tokens_limit(message, tokens, bot):
        return

    row: sqlite3.Row = get_value_from_table('session_id', user_id)

    add_record_to_table(
        user_id,
        'user',
        user_answer,
        datetime.now(),
        tokens,
        row['session_id']
    )

    bot.send_message(message.chat.id, "Генерирую ответ...")

    collection: sqlite3.Row = get_dialogue_for_user(user_id, row['session_id'])
    gpt_text: str = ask_gpt(collection)
    tokens: int = count_tokens(gpt_text)

    if is_tokens_limit(message, tokens, bot):
        return

    add_record_to_table(
        user_id,
        'assistant',
        gpt_text,
        datetime.now(),
        tokens,
        row['session_id']
    )

    bot.send_message(message.chat.id, gpt_text, reply_markup=menu_keyboard(HELP_COMMANDS + DEV_COMMANDS))


# Обработчик для генерирования вопроса
@bot.message_handler(content_types=['text'])
def get_question(message: types.Message):
    if not is_valid_text(message, bot):
        return

    try:
        user_id: int = message.from_user.id
        subject: str = current_subjects[user_id]
        prompt_by_level: str = PROMPTS[message.text]
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f'При получении данных произошла ошибка, попробуйте заново /start'
        )
        logging.debug(f'При получении уровня и предметов пользователя произошла ошибка {e}')
        return

    bot.send_message(message.chat.id, "Генерирую вопрос...")

    system_prompt: str = create_prompt(subject, prompt_by_level)
    tokens: int = count_tokens(system_prompt)

    session_id = 1
    if is_value_in_table(DB_TABLE_PROMPTS_NAME, 'user_id', user_id):
        row: sqlite3.Row = get_value_from_table('session_id', user_id)
        session_id = row['session_id'] + 1

    add_record_to_table(
        user_id,
        'system',
        system_prompt,
        datetime.now(),
        tokens,
        session_id
    )

    session: sqlite3.Row = get_dialogue_for_user(user_id, session_id)
    gpt_text: str = ask_gpt(session)
    tokens: int = count_tokens(gpt_text)

    add_record_to_table(
        user_id,
        'assistant',
        gpt_text,
        datetime.now(),
        tokens,
        session_id
    )

    if gpt_text is None:
        bot.send_message(
            message.chat.id,
            "Не могу получить ответ от GPT :(",
            reply_markup=menu_keyboard(HELP_COMMANDS)
        )

    elif gpt_text == "":
        bot.send_message(
            message.chat.id,
            "Не могу сформулировать решение :(",
            reply_markup=menu_keyboard(HELP_COMMANDS)
        )
        logging.info(f"TELEGRAM BOT: Input: {message.text}\nOutput: Error: нейросеть вернула пустую строку")

    else:
        bot.send_message(message.chat.id, gpt_text)
        bot.register_next_step_handler(message, answer_handler)


# Создаём базы данных или подключаемся к существующей
prepare_db(True)
bot.infinity_polling()
