# -*- coding: utf-8 -*-
"""Anim_Greeting_Bot.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1M-xIdu5Y1e1W4BABnfbVCdydORtJDJYO
"""

#requirement: pytelegrambotapi-3.6.7 python36



import telebot
from telebot import types

TOKEN = "your_token"
MAIN_URL = 'https://api.telegram.org/bot{}'.format(TOKEN)
#GROUP_ID = -1001387932680
#GROUP_ID = -1001267139997

bot = telebot.TeleBot(TOKEN)

animation = "CgACAgIAAxkBAAMQXqRWUPJTX-dkqkD8WDxnv8ssNsoAAoMDAAKXmgFIQnZNSLqs7iAZBA"

@bot.message_handler(content_types=["new_chat_members"]) #message: message.new_chat_member is not None and message.chat.id == GROUP_ID
def send_welcome(message):
    name = message.new_chat_member.first_name
    bot.send_message(message.chat.id, "Greeting {}, i was waiting for you".format(name))
    bot.send_animation(message.chat.id, animation=animation)

# @bot.message_handler(content_types=["new_chat_members"]) #message: message.new_chat_member is not None and message.chat.id == GROUP_ID
# def send_welcome(message):
#     bot.send_message(message.chat.id, "Greating, i was waiting for you")
#     bot.send_animation(message.chat.id, animation=animation)

if __name__ == '__main__':
  bot.polling() #none_stop=True

