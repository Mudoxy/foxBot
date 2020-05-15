#requirements: pytelegrambotapi-3.6.7 python36


import telebot
from telebot import types
from SQLighter import SQLighter, SQLever
from time import sleep, time
from functools import wraps
import datetime
from token_importer import tokenator

TOKEN = tokenator()
#MAIN_URL = 'https://api.telegram.org/bot{}'.format(TOKEN)
bot = telebot.TeleBot(TOKEN)

def mult_threading(func):
     """Декоратор для запуска функции в отдельном потоке"""
     @wraps(func) 
     def wrapper(*args_, **kwargs_): 
         import threading 
         func_thread = threading.Thread(target=func,  
                                        args=tuple(args_),  
                                        kwargs=kwargs_) 
         func_thread.start()
         return func_thread 
     return wrapper


#  Сразу делаем функцию многопоточной
@mult_threading 
def parallel_check_for_old_messages(worker_bot : telebot.TeleBot, delta_time = 3, check_delay = 10):
#delta_time in minutes
  while True:
    sleep(check_delay) #  Тут мы чего-то доолго ждем / вычисляем / etc
    db_worker = SQLighter("messages")
    time_diff = datetime.datetime.now() - datetime.timedelta(minutes = delta_time)
    time_diff = time_diff.strftime("%Y-%m-%d %H:%M:%S") # Форматируем время, убирая милисек.
    print ("checking for old messages before {}".format(time_diff))
    list_of_rows = db_worker.check_old_messages(time_diff)
    if list_of_rows:
      print ("old messages:\n{}".format(list_of_rows))
      for row in list_of_rows:
        try:
          message_id=int(row[0])
          chat_id=int(row[1])
          worker_bot.delete_message(chat_id=chat_id, message_id=message_id)
          db_worker.delete_row(chat_id=chat_id, message_id=message_id)
        except:
          print("Oops! An old message might have been deleted manually")
          db_worker.delete_row(chat_id=chat_id, message_id=message_id)
    db_worker.close()



@bot.message_handler(content_types=["new_chat_members"])
def send_welcome(message):
    name = message.new_chat_member.first_name
    db_kicker = SQLever("greetings")
    message_text = db_kicker.read_welcome(chat_id=message.chat.id)
    print (message_text)
    re1 = bot.send_message(message.chat.id, message_text)
    re2 = bot.send_animation(message.chat.id, animation=animation)
    print("welcome messages sent to chat with ID:{} for {}".format(message.chat.id, name))
    db_worker = SQLighter("messages")
    old_message = db_worker.read_by_chat_id(message.chat.id) #check for old messages in this chat
    if old_message:
        for message_row in old_message:
          try:
            bot.delete_message(chat_id=message.chat.id, message_id=message_row[0])
            db_worker.delete_row(chat_id=message.chat.id, message_id=message_row[0])
          except:
            print("Oops! An old message might have been deleted manually")
            db_worker.delete_row(chat_id=message.chat.id, message_id=message.id)
    db_worker.insert_message(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
    db_worker.insert_message(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm an animation")
    db_worker.close()
    db_kicker.close()

@bot.message_handler(commands=['setmessage']) #Здесь должен быть обработчик для команды "задать приветствие"
def set_welcome(message):
  db_kicker = SQLever("greetings")
  word_sequence = message.text.split(' ', maxsplit=1)
  if len(word_sequence) == 1:
    bot.send_message(message.chat.id, "Please, write the text of your greeting after the command, separated by a single space")
  elif len(word_sequence) == 2:
    greeting_text = word_sequence[1]
    db_kicker.set_welcome(chat_id=message.chat.id, greeting_text=greeting_text) #add message to user
    bot.send_message(message.chat.id, "Your new greeting was set")
  else:
    bot.send_message(message.chat.id, "Something went wrong")
  db_kicker.close()


# message_text1 = "Привет "
# message_text2 = "!\nИнформация для тебя находится в закрепе.\nКидай свои работы (если есть), чтобы мы знали чего от тебя ждать :)\nПриятного анимирования!"
animation = "CgACAgIAAxkBAAIB6F6-4W8qvVJA7XSOSIBGeeh3vwKBAAKDAwACl5oBSJejGtfSsoRHGQQ"

# forward_from_message_id

if __name__ == '__main__':
  parallel_check_for_old_messages(worker_bot=bot, delta_time = 3, check_delay = 10)
  bot.polling()