#requirement: pytelegrambotapi-3.6.7 python36


import telebot
from telebot import types
from foxBot import multi_threading
from SQLighter import SQLighter
from token import tokenator

TOKEN = tokenator()


bot = telebot.TeleBot(TOKEN)

animation = "CgACAgIAAxkBAAMQXqRWUPJTX-dkqkD8WDxnv8ssNsoAAoMDAAKXmgFIQnZNSLqs7iAZBA"

@bot.message_handler(content_types=["new_chat_members"]) #message: message.new_chat_member is not None and message.chat.id == GROUP_ID
def send_welcome(message):
    name = message.new_chat_member.first_name
    re1 = bot.send_message(message.chat.id, "Greating {}, i was waiting for you".format(name))
    re2 = bot.send_animation(message.chat.id, animation=animation)
    db_worker = SQLighter("messages")
    old_message = db_worker.read_by_chat_id(message.chat.id) #check for old messages in this chat
    if old_message:
        for message_row in old_message:
            bot.delete_message(chat_id=message.chat.id, message_id=message_row[0])
    db_worker.insert_message(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
    db_worker.insert_message(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm beautiful animation")
    db_worker.close()
        

if __name__ == '__main__':
  #parallel_check_for_old_messages(delta_time = 3, check_delay = 3)
  bot.polling()