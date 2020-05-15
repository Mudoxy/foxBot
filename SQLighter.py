#SQLighter

import sqlite3
import datetime

class SQLighter:
    """ bot messages database"""

    def __init__(self, database : str):
        self.connection = sqlite3.connect(database)
        self.name = database
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (message_id INTEGER, chat_id INTEGER, begin_date DATETIME, message_text TEXT);".format(self.name))


    def read_by_chat_id(self, chat_id: int):
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE  chat_id = '{}';".format(self.name, chat_id)).fetchall()

    def check_old_messages(self, time_diff: str):
        """ Проверяем на наличие устаревших строк """
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE begin_date < '{}'".format(self.name, time_diff)).fetchall()

    def insert_message(self, chat_id: int, message_id: int, message_text=""):
        """ Добавляем строку """
        with self.connection:
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO {}(chat_id, message_id, message_text, begin_date) VALUES(?,?,?,?);".format(self.name), (chat_id, message_id, message_text, current_time))
        return (0)

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM {};".format(self.name)).fetchall()
            return len(result)

    def delete_row(self, chat_id: int, message_id: int):
        """ Удаляем строку с устаревшим сообщением """
        with self.connection:
            self.cursor.execute("DELETE FROM {} WHERE chat_id = '{}' AND message_id = '{}';".format(self.name, chat_id, message_id))

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()


class SQLever:
    """ greeting texts database """

    def __init__(self, database2: str):
        self.connection = sqlite3.connect(database2)
        self.name = database2
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (chat_id INTEGER, greeting_text TEXT, date_added DATETIME);".format(self.name))

    def set_welcome(self, chat_id: int, greeting_text: str):
        """ Добавляем строку с приветствием """
        with self.connection:
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            check = self.cursor.execute("SELECT greeting_text FROM {} WHERE chat_id = '{}';".format(self.name, chat_id)).fetchall()
            print(check)
            if check:
                self.cursor.execute("UPDATE {} SET greeting_text = '{}' WHERE chat_id = '{}';".format(self.name, greeting_text, chat_id)) #add time update
            else:
                self.cursor.execute("INSERT INTO {}(chat_id, greeting_text, date_added) VALUES(?,?,?);".format(self.name), (chat_id, greeting_text, current_time))

    def read_welcome(self, chat_id: int):
        """ Считываем нужное приветствие """
        with self.connection:
            return self.cursor.execute("SELECT greeting_text FROM {} WHERE  chat_id = '{}';".format(self.name, chat_id))

    def close(self):
        self.connection.close()

