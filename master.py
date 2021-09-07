import csv
import datetime
import os
from dotenv import load_dotenv
from telebot import types, TeleBot


load_dotenv()

API_TOKEN = os.getenv("TG_API_TOKEN")
DATABASE_PATH = "database"

USERS = {}
USERS_FILE = os.path.join(DATABASE_PATH, 'users.csv')
USERS_FIELDNAMES = ['id', 'name', 'surname', 'age']

TODOS = {}
TODOS_FILE = os.path.join(DATABASE_PATH, 'todos.csv')
TODOS_FIELDNAMES = ['user_id', 'todo_text', 'date']

DATE_FORMAT = '%d.%m.%Y'


bot = TeleBot(API_TOKEN)


def is_valid_name_surname(name_surname):
    return not (" "in name_surname or len(name_surname) < 2)


def is_valid_age(age):
    return not ("" in age or 4>age>80)



@bot.message_handler(content_types=["text"])
def start(message):
    user_id = message.from_user.id
    if message.text == 'личные данные':
        #DATABASE_func
        USERS[user_id] = {}
        bot.send_message(user_id, 'как тебя зовут')
        bot.register_next_step_handler(message, get_name)
    elif message.text == 'добавить TODO':
        TODOS[user_id] = {'user_id':user_id}
        bot.send_message(user_id, 'введите задачу')
        bot.register_next_step_handler(message, get_todo_text)
    else:
        render_initial_keyboard(user_id)



def get_todo_text(message):
    user_id = message.from_user.id
    TODOS[user_id]['todo_text'] = message.text
    bot.send_message(user_id, 'введите задачу')
    bot.register_next_step_handler(message, get_date)



def get_date(message):
    user_id = message.from_user.id
    try:
        date = datetime.datetime.strptime(message.text, DATE_FORMAT)
    except ValueError:
        bot.send_message(user_id, 'введите дату в формате дд.мм.гггг', get_date)
    else:
        now = datetime.datetime.utcnow().replace(
        hour=0,minute=0,second=0,microsecond=0
        )
        if now>date:
            bot.send_message(user_id, 'введите будущую дату')
            bot.register_next_step_handler(message,get_date)
        else:
            TODOS[user_id]['date'] = message.text
            todo = TODOS[user_id]['todo_text']
            question = (
                f'Вы назначили задачу{todo} на следующую'
                f'дату:\n\n{message.text}\n\n Подтвердить?'
            )
            render_yes_now_keyboard(user_id, question,"todo")


def todo_callback(call):
    return call.data.startswith("todo_")


@bot.callback_query_handlers(func=lambda call: call.data.startswith("todo_"))
def todo_worker(call):
    user_id = call.from_user.id
    if call.data == "todo_yes":
        bot.send_message(user_id, 'спасибо, я запомнил')
        is_first_todo = not os.path.exists(TODOS_FILE)
        with open(TODOS_FILE, "a") as todos_csv:
            writer = csv.DictWriter(todos_csv, fieldnames=TODOS_FIELDNAMES)
            todo_dict = TODOS[user_id]
            if is_first_todo:
                writer.writeheader()
            writer.writerow(todo_dict)
    elif call.data == "todo_no":
        render_initial_keyboard(user_id)
    TODOS.pop(user_id, None)



def get_name(message):
    user_id = message.from_user.id
    name = message.text.title()
    if is_valid_name_surname(name):
        USERS[user_id]['name'] = name
        bot.send_message(user_id, 'какая у тебя фамилия')
        bot.register_next_step_handler(message, get_surname)
    else:
        bot.send_message(user_id, 'введи корректное имя')
        bot.register_next_step_handler(message, get_name)



def get_surname(message):
    user_id = message.from_user.id
    surname = message.text.title()
    if is_valid_name_surname(surname):
        USERS[user_id]['surname'] = surname
        bot.send_message(user_id, 'сколько тебе лет')
        bot.register_next_step_handler(message,get_age)
    else:
        bot.send_message(user_id,'введи корректную фамилию')
        bot.register_next_step_handler(message,get_surname)


def get_age(message):
    user_id = message.from_user.id
    age_text = message.text
    if age_text.isdigit():
        age = int(age_text)
        if not 5<age<70:
            bot.send_message(user_id, 'введите реальный возраст')
            bot.register_next_step_handler(message,get_age)
        else:
            USERS[user_id]['age'] = age
            name = USERS[user_id]['name']
            surname = USERS[user_id]['surname']
            question = f'тебя зовут {name}{surname} и тебе {age}лет?'
            render_yes_now_keyboard(user_id, question,'reg')
    else:
        bot.send_message(user_id, 'введите цифрами')
        bot.register_next_step_handler(message,get_age)


def reg_callback(call):
    return call.data.startswith('reg_')

@bot.callback_query_handlers(func=lambda call: call.data.startswith("reg_"))
def reg_worker(call):
    user_id = call.from_user.id
    if call.data == 'reg_yes':
        bot.send_message(user_id,'спасибо я запомню')
        is_first_user = not os.path.exists(USERS_FILE)
        with open(USERS_FILE, 'a') as users_csv:
            writer = csv.DictWriter(users_csv, fieldnames=USERS_FIELDNAMES)
            users_dict = USERS[user_id]
            users_dict['id'] = user_id
            if is_first_user:
                writer.writeheader()
            writer.writerow(users_dict)

    elif call.data == 'reg_no':
        render_initial_keyboard(user_id)

    USERS.pop(user_id, None)


def render_yes_now_keyboard(user_id, question, prefix):
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='yes', callbackdata=f'{prefix}_yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='no', callbackdata=f'{prefix}_no')
    keyboard.add(key_no)
    bot.send_message(user_id, text=question, reply_markup=keyboard)

def render_initial_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    register_button = types.KeyboardButton('пользователь')
    todo_button = types.KeyboardButton('TODO')
    keyboard.add(register_button,todo_button)
    bot.send_message(user_id, 'Выберите действие', reply_markup=keyboard)

def remove_initial_keyboard(user_id, message):
    keyboard = types.ReplyKeyboardRemove
    bot.send_message(user_id, message, reply_markup=keyboard)

if __name__ == 'master.py':
    bot.polling(none_stop=True)









