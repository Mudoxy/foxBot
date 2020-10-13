from SQLclasses import SQLchatsGreatings, SQLmessages

import logging
import aiogram
from aiogram.types import ContentType
logging.basicConfig(level=logging.DEBUG)

TOKEN = "PLACE FOR YOUR TOKEN"

bot = aiogram.Bot(token=TOKEN)
dp = aiogram.Dispatcher(bot)

@dp.message_handler(content_types=[ContentType.VIDEO, ContentType.ANIMATION, ContentType.DOCUMENT])
async def set_animation(message):
    logging.debug("CATCHED ANIMATION")
    animation_db = SQLchatsGreatings()
    animation_db.update_record(chat_id=message.chat.id, animation_link=message.animation.file_id, capcha=True)
    animation_db.close()

@dp.message_handler(content_types=[ContentType.NEW_CHAT_MEMBERS])
async def send_welcome(message):
    name = message.new_chat_members[-1].first_name
    animation_db = SQLchatsGreatings()
    animation = animation_db.record_by_chat_id(message.chat.id)[0][1] #first (and only one) row, second argument is file name
    welcome_text = "Hello NAME, we glad you are here"
    re1 = await bot.send_message(message.chat.id, welcome_text.relpace("NAME", name))
    re2 = await bot.send_animation(message.chat.id, animation=animation)
    animation_db.close()
    messages_db = SQLmessages()
    old_messages = messages_db.record_by_chat_id(message.chat.id)
    if old_messages:
        for message_row in old_messages:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message_row[0]) #zero index in row is chat_id
                messages_db.delete_record(chat_id=message.chat.id, message_id=message_row[0])
            except:
                logging.error("TRYIED TO DELETE MESSAGE IN CHAT BUT CAN'T FIND IT")
                messages_db.delete_record(chat_id=message.chat.id, message_id=message_row[0])
        messages_db.insert_record(chat_id=message.chat.id, message_id=re1.message_id, message_text=message.text)
        messages_db.insert_record(chat_id=message.chat.id, message_id=re2.message_id, message_text="I'm an animation")
        messages_db.close()


if __name__ == "__main__":
    aiogram.executor.start_polling(dp, skip_updates=True)