#requirements: pytelegrambotapi-3.6.7 python36


import telebot
from telebot import types
from multi_threading import parallel_check_for_old_messages
from SQLighter import SQLighter
from time import sleep, time
from functools import wraps
import datetime
from token_importer import tokenator

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
    print ("time threshold - {}".format(time_diff))
    print ("checking for old messages")
    list_of_rows = db_worker.check_old_messages(time_diff)
    if list_of_rows:
      print (list_of_rows)
      for row in list_of_rows:
          message_id=int(row[0])
          chat_id=int(row[1])
          worker_bot.delete_message(chat_id=chat_id, message_id=message_id)
          db_worker.delete_row(chat_id=chat_id, message_id=message_id)
    db_worker.close()

TOKEN = tokenator()
MAIN_URL = 'https://api.telegram.org/bot{}'.format(TOKEN)


bot = telebot.TeleBot(TOKEN)

message_text1 = "Привет "
message_text2 = "!\nИнформация для тебя находится в закрепе.\nКидай свои работы (если есть), чтобы мы знали чего от тебя ждать :)\nПриятного анимирования!"

animation = "CgACAgIAAxkBAAMQXqRWUPJTX-dkqkD8WDxnv8ssNsoAAoMDAAKXmgFIQnZNSLqs7iAZBA"

@bot.message_handler(content_types=["new_chat_members"]) #message: message.new_chat_member is not None and message.chat.id == GROUP_ID
def send_welcome(message):
    name = message.new_chat_member.first_name
    re1 = bot.send_message(message.chat.id, message_text1+name+message_text2)
    re2 = bot.send_animation(message.chat.id, animation=animation)
    db_worker = SQLighter("messages")
    old_message = db_worker.read_by_chat_id(message.chat.id) #check for old messages in this chat
    if old_message:
        for message_row in old_message:
            print (bot.delete_message(chat_id=message.chat.id, message_id=message_row[0]))
            db_worker.delete_row(chat_id=message.chat.id, message_id=message_row[0])
    db_worker.insert_message(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
    db_worker.insert_message(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm beautiful animation")
    db_worker.close()
        

if __name__ == '__main__':
  parallel_check_for_old_messages(worker_bot=bot, delta_time = 3, check_delay = 10)
  bot.polling()