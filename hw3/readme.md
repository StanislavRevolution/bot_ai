# Проект Бота на основе YaGPT

Этот проект представляет собой чат-бота, который использует нейросеть YaGPT для взаимодействия с пользователем и помощи в подготовке к таким предметам как история и математика.

## Инструкции по установке

1. Установите зависимости, перечисленные в файле `requirements.txt`, выполнив следующую команду в терминале:

    ```bash
    pip install -r requirements.txt
    ```

2. В папке `creds` создайте файл `folder_id.txt`, в котором укажите ID вашего каталога на Yandex Cloud.

3. Для работы бота и получения токена необходим сервисный аккаунт на Yandex Cloud. Убедитесь, что на сервере, с которого запускается бот, есть необходимые права для получения токена.

4. Добавьте токен вашего бота в config.py 

## Запуск бота

Для запуска бота выполните скрипт `bot.py`.

## Локальные тесты

Для локальных тестов вы можете закомментировать строку `get_creds()` в файле `ask_gpt.py` и явно указать токен в начале файла, создав новую переменную.

## Дополнительная информация

Этот бот создан с использованием нейросети YaGPT, которая предоставляет возможность генерации текста на русском языке. Он разработан для помощи в подготовке к предметам история и математика, однако его функциональность может быть расширена для работы с другими предметами или задачами.

## Обратная связь и вклад

Если у вас есть предложения, вопросы или обратная связь по поводу этого проекта, пожалуйста, свяжитесь с нами. Мы приветствуем ваши идеи и вклад в улучшение бота.