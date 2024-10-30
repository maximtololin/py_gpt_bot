from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, \
    CallbackQueryHandler, CommandHandler, ContextTypes

from credentials import ChatGPT_TOKEN
from gpt import ChatGptService
from credentials import BOT_TOKEN
from util import load_message, load_prompt, send_text_buttons, send_text, \
    send_image, show_main_menu, Dialog, default_callback_handler

dialog = Dialog()
dialog.mode = None
chat_gpt = ChatGptService(ChatGPT_TOKEN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = 'main'
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Главное меню',
        'random': 'Узнать случайный интересный факт 🧠',
        'gpt': 'Задать вопрос чату GPT 🤖',
        'talk': 'Поговорить с известной личностью 👤',
        'quiz': 'Поучаствовать в квизе ❓',
        'food': 'Узнай рецепт из названия блюда 🍖',
        'enjoy': 'Помогу выбрать чем заняться 💻'
        # Добавить команду в меню можно так:
        # 'command': 'button text'

    })


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ответ на вопрос от ChatGPT
    """
    dialog.mode = 'gpt'
    prompt = load_prompt('gpt')
    message = load_message('gpt')

    chat_gpt.set_prompt(prompt)
    await send_image(update, context, 'gpt')
    await send_text(update, context, message)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Случайный факт от текстовой модели
    """
    prompt = load_prompt('random')
    message = load_message('random')

    await send_image(update, context, 'random')
    answer = await chat_gpt.send_question(prompt, '')
    message = await send_text_buttons(update, context, answer, {
        'more_facts': 'Расскажи еще!',
        'enough_facts': 'Вернуться в  меню'
    })


async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    thinking_message = await send_text(update, context, 'Думаю...')
    answer = await chat_gpt.add_message(user_question)
    await thinking_message.edit_text(answer)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip().lower()
    if user_text == 'стоп':
        dialog.mode = 'main'
        await start(update, context)
    elif dialog.mode in ['cobain', 'hawking', 'nietzsche', 'queen', 'tolkien']:
        user_question = update.message.text
        thinking_message = await send_text(update, context, 'Секундочку...')
        answer = await chat_gpt.add_message(user_question)
        await thinking_message.edit_text(answer)
    elif dialog.mode == 'gpt':
        await gpt_dialog(update, context)
    elif dialog.mode == 'food':
        await handle_food_query(update, context)
    elif dialog.mode in ['movies', 'books']:
        await handle_preferences_query(update, context)
    else:
        await start(update, context)


async def console_print(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображаем сообщения и команды пользователя в консоль
    """
    text = update.message.text
    print(text)


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет сообщения пользователя обратно в чат
    """
    text = update.message.text
    await send_text(update, context, text)


async def random_fact_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'more_facts':
        await random_fact(update, context)
    else:
        dialog.mode = 'main'
        await start(update, context)


async def more_facts(update, context):
    await random_fact(update, context)


async def character_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE, character: str):
    """
    Диалог пользователя с выбранным персонажем
    """
    dialog.mode = character

    prompt = load_prompt(f"talk_{character}")
    chat_gpt.set_prompt(prompt)

    await send_image(update, context, f"talk_{character}")
    message = f"Вы говорите с {character.capitalize()}! Для возврата в меню напишите: стоп"
    await send_text(update, context, message)


async def talk_with_famous_people(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вывод кнопок для выбора персонажа пользователем
    """
    await send_text_buttons(update, context, 'Выбери персонажа для разговора:', {
        'cobain': 'Курт Кобейн',
        'hawking': 'Стивен Хокинг',
        'nietzsche': 'Фридрих Ницше',
        'queen': 'Елизавета II',
        'tolkien': 'Джон Толкин'
    })


async def famous_people_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор персонажа пользователем из кнопок,
    устанавливая соответствующий режим диалога и загружая диалог с выбранным персонажем.
    """
    query = update.callback_query
    await query.answer()

    character = query.data
    await character_dialog(update, context, character)


"""
=======================================================================
Не удалось победить ChatGPT, отвечает только а английском языке в квизе
=======================================================================
"""


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начальный экран квиза: отправка изображения и вывод кнопки с темой "Программирование".
    """
    dialog.mode = 'quiz'
    await send_image(update, context, 'quiz')

    await send_text_buttons(update, context, 'Выберите тему для квиза:', {
        'quiz_prog': 'Программирование'
    })

    context.user_data['quiz_score'] = 0


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатия на кнопку "Программирование". Загружает промт и начинает квиз с первого вопроса.
    """
    query = update.callback_query
    await query.answer()

    prompt = load_prompt('quiz')
    chat_gpt.set_prompt(prompt)

    question = await chat_gpt.send_question("quiz_prog", '')
    await send_text(update, context, question)


async def quiz_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ответа пользователя на вопрос квиза. Проверка правильности и вывод результата.
    """
    user_answer = update.message.text

    result = await chat_gpt.send_question("quiz_prog", user_answer)

    if result.strip().lower() == "правильно!":
        context.user_data['quiz_score'] += 1
        response = f"Правильно! Ваш счёт: {context.user_data['quiz_score']}"
    else:
        correct_answer = result.split('-')[1].strip()
        response = f"Неправильно! Правильный ответ - {correct_answer}. Ваш счёт: {context.user_data['quiz_score']}"

    await send_text_buttons(update, context, response, {
        'quiz_more': 'Задать ещё вопрос'
    })


async def quiz_more_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик запроса пользователя на ещё один вопрос.
    """
    query = update.callback_query
    await query.answer()

    question = await chat_gpt.send_question("quiz_prog", '')
    await send_text(update, context, question)


async def food_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Инициализация режима получения рецепта. Пользователь вводит название блюда, и бот возвращает рецепт.
    """
    dialog.mode = 'food'
    prompt = load_prompt('food')
    chat_gpt.set_prompt(prompt)

    await send_image(update, context, 'food')
    message = "Напишите название блюда, и я подскажу, как его приготовить!"
    await send_text(update, context, message)


async def handle_food_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для получения и отправки рецепта после ввода названия блюда.
    """
    if dialog.mode != 'food':
        return

    user_input = update.message.text.strip()

    if not user_input:
        await update.message.reply_text("Пожалуйста, введите название блюда.")
        return

    prompt_text = load_prompt('food')
    recipe_response = await chat_gpt.send_question(prompt_text, f"Название блюда: {user_input}")

    await update.message.reply_text(recipe_response)


async def enjoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Инициализация рекомендаций: выводит клавиатуру с выбором категорий (Фильмы или Книги).
    """
    dialog.mode = 'enjoy'

    await send_text_buttons(update, context, "Выберите категорию для рекомендаций:", {
        'movies': 'Фильмы 🎬',
        'books': 'Книги 📚'
    })


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик выбора категории: Фильмы или Книги. Запрашивает предпочтения пользователя.
    """
    query = update.callback_query
    await query.answer()

    category = query.data
    dialog.mode = category

    if category == 'movies':
        message = "Какой жанр фильмов вам нравится? Например: комедия, триллер, фантастика."
    elif category == 'books':
        message = "Есть ли автор или жанр книг, который вам нравится? Например: фантастика, детектив, Достоевский."

    await send_text(update, context, message)


async def handle_preferences_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик для получения предпочтений и запроса рекомендаций у ChatGPT.
    """
    if dialog.mode not in ['movies', 'books']:
        return

    preferences = update.message.text.strip()

    if dialog.mode == 'movies':
        prompt = load_prompt('movies_recommendations')
        request_text = f"Рекомендуй фильмы в жанре: {preferences}"
    elif dialog.mode == 'books':
        prompt = load_prompt('books_recommendations')
        request_text = f"Рекомендуй книги в жанре или по автору: {preferences}"

    chat_gpt.set_prompt(prompt)
    recommendations = await chat_gpt.send_question(prompt, request_text)

    await update.message.reply_text(recommendations)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random_fact))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk_with_famous_people))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('food', food_recipe))
app.add_handler(CommandHandler('enjoy', enjoy))

# Зарегистрировать обработчик команды можно так:
app.add_handler(MessageHandler(filters.TEXT, console_print), group=0)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler), group=1)
app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(?!/).*$'), quiz_answer_handler))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(?!/).*$'), handle_preferences_query))
# Зарегистрировать обработчик кнопки можно так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(CallbackQueryHandler(random_fact_button, pattern='^more_facts.*'))
app.add_handler(CallbackQueryHandler(random_fact_button, pattern='^enough_facts.*'))
app.add_handler(CallbackQueryHandler(famous_people_button, pattern='^(cobain|hawking|nietzsche|queen|tolkien)$'))
app.add_handler(CallbackQueryHandler(start_quiz, pattern='^quiz_prog$'))
app.add_handler(CallbackQueryHandler(quiz_more_question, pattern='^quiz_more$'))
app.add_handler(CallbackQueryHandler(handle_category_selection, pattern='^(movies|books)$'))

app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()
