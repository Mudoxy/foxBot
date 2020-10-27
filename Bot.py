# New version of welcome bot that migrated from pyTelegramBotApi -> aiogram
# Bot restricts (admin rights needed) newcomer users and ask them to press button to show
# That newcomer user are human and prevent bot spamming.

# After button was pressed Bot send welocme message with chat info
# Welcome message automatically deleted after %time_delta time
# Inactive users whose not press antispam button kicked after %time_delt time

from SQLclasses import SQLchatsGreatings, SQLmessages, SQLmembers
# classes for interact with sqlite databases
# chatGreatings - db with welcome animation and welcome message
# messages - db with welcome messages to remember what messages to delete
# members - db with newcomers to remember what inactive users to kick

import asyncio
import logging
import aiogram
import typing
import datetime
from aiogram.utils.callback_data import CallbackData
from aiogram.types import ContentType, InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.DEBUG)
#Still in beta. Logging in debug mode

KICKING = False
REPORTING = True
USERS_TO_REPORT = [410584052]
TOKEN = "648522503:AAHjE3axKhIWKRHayFhGDfxJoGSUy9Bwzmk"
bot = aiogram.Bot(token=TOKEN)
dp = aiogram.Dispatcher(bot)

dp.filters_factory.bind(MyFilter)

from aiogram.dispatcher.filters import BoundFilter
class MyFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message):
        member = await bot.get_chat_member(chat_id=message.chat.id, message_id=message.from_user.id)
        return member.is_chat_admin()

button_click = CallbackData("Click","action")
def get_keyboad():
    return InlineKeyboardMarkup().row(InlineKeyboardButton("Click", callback_data=button_click.new(action="done")))

async def check_for_old_messages(time_diff):
    logging.debug("CHECK FOR OLD MESSAGES")
    messages_db = SQLmessages()
    list_of_old_messages = messages_db.check_old_messages(time_diff)
    if list_of_old_messages:
        logging.debug("old messages:\n{}".format(list_of_old_messages))
        for old_message in list_of_old_messages:
            message_id, chat_id = int(old_message["message_id"]), int(old_message["chat_id"])
            try:
                messages_db.delete_record(chat_id=chat_id, message_id=message_id)
            except:
                logging.debug("FAILED TO DELETE MESSAGE FROM SQL DB")
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                logging.debug("FAILED TO DELETE MESSAGE FROM TELEGRAM")
    messages_db.close()

async def check_for_restricted_users(time_diff):
    members_db = SQLmembers()
    list_of_idle_restricted_users = members_db.check_awaited_restrict(time_diff=time_diff, status="awaiting")
    if list_of_idle_restricted_users:
        logging.debug("USERS TO BE KICKED:\n{}".format(list_of_idle_restricted_users))
        for restr_user in list_of_idle_restricted_users:
            chat_id, message_id, user_id = int(restr_user["chat_id"]), int(restr_user["message_id"]), int(restr_user["user_id"])
            members_db.delete_row(chat_id=chat_id, message_id=message_id)
            members_db.add_member(chat_id=chat_id, message_id=message_id, status="restricted")
            if KICKING:
                try:
                    await bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
                except:
                    logging.debug("CAN'T KICK USER {}".format(user_id))
            
        if REPORTING:
            for user_to_report in USERS_TO_REPORT:
                try:
                    await bot.send_message(chat_id=user_to_report, text=str(*list_of_idle_restricted_users))
                except:
                    logging.debug("CAN'T SEND MESSAGE TO USER {}".format(user_to_report))
        
    members_db.close()

async def permanent_check_for_old_messages(delta_time = 3, check_delay = 15):
    # delta_time in minutes, check_delay in seconds. Sorry for incosistency
    # infinite loop for check inactive newcome users and old messages
    # delta_time in minutes
    # TODO: for each newcomer spawns new message. Possible deadlock here
    while True:
        await asyncio.sleep(check_delay)
        time_diff = datetime.datetime.now() - datetime.timedelta(minutes = delta_time)
        time_diff = time_diff.strftime("%Y-%m-%d %H:%M:%S") # Removing milisec part
        logging.debug("checking for old messages before {}".format(time_diff))
        await check_for_old_messages(time_diff)
        await check_for_restricted_users(time_diff)

@dp.message_handler(content_types=[ContentType.VIDEO, ContentType.ANIMATION, ContentType.DOCUMENT], is_admin=True)
async def set_animation(message):
    # func for recieving animation from user and set it to welcome animation
    #TODO: set welcome text too
    logging.debug("CATCHED ANIMATION")
    animation_db = SQLchatsGreatings()
    animation_db.update_record(chat_id=message.chat.id, animation_link=message.animation.file_id, capcha=True)
    animation_db.close()

@dp.message_handler(content_types=[ContentType.TEXT], is_admin=True)
async def set_text(message):
    logging.debug("CATCHED TEXT")
    animation_db = SQLchatsGreatings()
    animation_db.update_record(chat_id=message.chat.id, welcome_text=message.text, capcha=True)
    animation_db.close()

@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def restrict_newcomers(message):
    # func for handle newcomers. Spawn message with button on it to press
    # restrict member and add member in members_db. If he remain inactive he will be kicked by permanent_check func
    new_members = message.new_chat_members
    members_db = SQLmembers()
    messages_db = SQLmessages()
    welcome_text = "Привет. Добро пожаловать в чат CHAT, будь добр - нажми на кнопочку и покажи что ты хороший человек"
    re1 = await message.answer(welcome_text.replace("CHAT", message.chat.title), reply_markup=get_keyboad())
    for member in new_members:
        members_db.add_member(chat_id=message.chat.id, user_id=member.id, status="awaiting", message_id=re1.message_id)
        messages_db.insert_record(chat_id=message.chat.id, message_id=re1.message_id, message_text=re1.text)
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=member.id)
    members_db.close()
    messages_db.close()

@dp.callback_query_handler(button_click.filter(action=["done"]))
async def welcome_and_unrestrict(query, callback_data: typing.Dict[str, str]):
    # handling pressing button. Unrestrict user and sending him welcome message
    # welcome message will be deleted automatically after %delte_time time
    user = query["from"]
    message = query.message
    members_db = SQLmembers()
    await query.answer()
    members_db.delete_record(chat_id=message.chat.id, user_id=user.id)
    logging.debug("DELETING MESSAGE")
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    logging.debug("UNRESTRICTING USER")
    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user.id, can_send_messages=True,
                                    can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
    members_db.close()

    messages_db = SQLmessages()
    welcome_text = "Привет NAME, рады тебя видеть"
    #TODO take welcome messae from DB
    re1 = await bot.send_message(message.chat.id, welcome_text.replace("NAME", user.first_name))
    messages_db.insert_record(chat_id=message.chat.id, message_id=re1.message_id)

    old_messages = messages_db.record_by_chat_id(message.chat.id)
    if old_messages:
        for message_row in old_messages:
            logging.debug("TRYING TO DELETE MESSAGE CHAT {} ID {}".format(message_row["chat_id"], message_row["message_id"]))
            await bot.delete_message(chat_id=message_row["chat_id"], message_id=message_row["message_id"]) #zero index in row is chat_id
            messages_db.delete_record(chat_id=message_row["chat_id"], message_id=message_row["message_id"])
        messages_db.insert_record(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
        messages_db.insert_record(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm an animation")

    animation_db = SQLchatsGreatings()
    try:
        animation = animation_db.record_by_chat_id(message.chat.id)[0]["animation"] #first (and only one) row, second argument is file name
        re2 = await bot.send_animation(message.chat.id, animation=animation)
        messages_db.insert_record(chat_id=message.chat.id, message_id=re2.message_id)
    except:
        logging.debug("FAILED TO SEND ANIMATION")
    messages_db.close()
    animation_db.close()

if __name__ == "__main__":
    # add bot and permanent_check in parallel executing
    ioloop = asyncio.get_event_loop()
    tasks = [ioloop.create_task(permanent_check_for_old_messages()), ioloop.create_task(aiogram.executor.start_polling(dp, skip_updates=True))]
    ioloop.run_forever()