# New version of welcome bot that migrated from pyTelegramBotApi -> aiogram
# Bot restricts (admin rights needed) newcomer users and ask them to press button to show
# That newcomer user are human and prevent bot spamming.

# After button was pressed Bot send welocme message with chat info
# Welcome message automatically deleted after %time_delta time
# Inactive users whose not press antispam button kicked after %time_delt time

from SQLclasses import SQLchatsGreatings, SQLmessages, SQLmembers
# classes for interact with sqlite databases
# chatGreatings - db with welcome animation and welcome message
# TODO: only admin of channel should have rights for set welcome animation
# messages - db with welcome messages to remember what messages to delete
# members - db with newcomers to remember what inactive users to kick
# TODO: db.read_by_chatid return [list of args] what is unreadable
#       should change to dict {chat_id: value, message_id: value}

import asyncio
import logging
import aiogram
import typing
import datetime
from aiogram.utils.callback_data import CallbackData
from aiogram.types import ContentType, InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.DEBUG)
#Still in beta. Logging in debug mode

button_click = CallbackData("Click","action")
def get_keyboad():
    return InlineKeyboardMarkup().row(InlineKeyboardButton("Click", callback_data=button_click.new(action="done")))

async def permanent_check_for_old_messages(delta_time = 3, check_delay = 10):
    # infinite loop for check inactive newcome users and old messages
    # delta_time in minutes
    # TODO: hide time calculation inside db class. code are overburdened
    # TODO: for each newcomer spawns new message. Possible deadlock here
    while True:
        await asyncio.sleep(check_delay)
        messages_db = SQLmessages()
        members_db = SQLmembers()
        time_diff = datetime.datetime.now() - datetime.timedelta(minutes = delta_time)
        time_diff = time_diff.strftime("%Y-%m-%d %H:%M:%S") # Removing milisec part
        logging.debug("checking for old messages before {}".format(time_diff))
        list_of_old_messages = messages_db.check_old_messages(time_diff)
        if list_of_old_messages:
            logging.debug("old messages:\n{}".format(list_of_old_messages))
            for old_message in list_of_old_messages:
                message_id, chat_id = int(old_message[0]), int(old_message[1])
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                messages_db.delete_row(chat_id=chat_id, message_id=message_id)
        list_of_idle_restricted_users = members_db.check_old_messages(time_diff)
        if list_of_idle_restricted_users:
            logging.debug("users_to_be_kicked:\n{}".format(list_of_idle_restricted_users))
            for restr_user in list_of_idle_restricted_users:
                chat_id, message_id, user_id = int(restr_user[0]), int(restr_user[1]), int(restr_user[2])
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                await bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
                members_db.delete_row(chat_id=chat_id, message_id=message_id)

TOKEN = "YOUR_TOKEN_HERE"

bot = aiogram.Bot(token=TOKEN)
dp = aiogram.Dispatcher(bot)

@dp.message_handler(content_types=[ContentType.VIDEO, ContentType.ANIMATION, ContentType.DOCUMENT])
async def set_animation(message):
    # func for recieving animation from user and set it to welcome animation
    #TODO: set welcome text too
    logging.debug("CATCHED ANIMATION")
    animation_db = SQLchatsGreatings()
    animation_db.update_record(chat_id=message.chat.id, animation_link=message.animation.file_id, capcha=True)
    animation_db.close()

@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def restrict_newcomers(message):
    # func for handle newcomers. Spawn message with button on it to press
    # restrict member and add member in members_db. If he remain inactive he will be kicked by permanent_check func
    new_members = message.new_chat_members
    members_db = SQLmembers()
    welcome_text = "Привет. Добро пожаловать в чат CHAT, будь добр - нажми на кнопочку и покажи что ты хороший человек"
    re1 = await message.answer(welcome_text.replace("CHAT", message.chat.title), reply_markup=get_keyboad())
    for member in new_members:
        members_db.add_member(chat_id=message.chat.id, user_id=member.id, status="restricted", message_id=re1.message_id)
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=member.id)
    members_db.close()

@dp.callback_query_handler(button_click.filter(action=["done"]))
async def welcome_and_unrestrict(query, callback_data: typing.Dict[str, str]):
    # handling pressing button. Unrestrict user and sending him welcome message
    # welcome message will be deleted automatically after %delte_time time
    user = query["from"]
    message = query.message
    members_db = SQLmembers()
    await query.answer()
    members_db.delete_record(chat_id=message.chat.id, user_id=user.id)
    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user.id, can_send_messages=True,
                                    can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    members_db.close()

    animation_db = SQLchatsGreatings()
    animation = animation_db.record_by_chat_id(message.chat.id)[0][1] #first (and only one) row, second argument is file name
    welcome_text = "Привет NAME, рады тебя видеть"
    re1 = await bot.send_message(message.chat.id, welcome_text.relpace("NAME", user.name))
    re2 = await bot.send_animation(message.chat.id, animation=animation)
    animation_db.close()
    messages_db = SQLmessages()
    old_messages = messages_db.record_by_chat_id(message.chat.id)
    if old_messages:
        for message_row in old_messages:
            await bot.delete_message(chat_id=message.chat.id, message_id=message_row[0]) #zero index in row is chat_id
            messages_db.delete_record(chat_id=message.chat.id, message_id=message_row[0])
        messages_db.insert_record(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
        messages_db.insert_record(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm an animation")
        messages_db.close()

if __name__ == "__main__":
    # add bot and permanent_check in parallel executing
    ioloop = asyncio.get_event_loop()
    tasks = [aiogram.executor.start_polling(dp, skip_updates=True), ioloop.create_task(permanent_check_for_old_messages())]
    ioloop.run_until_complete()