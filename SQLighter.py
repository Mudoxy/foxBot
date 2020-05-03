#SQLighter

import sqlite3

class SQLighter:

    def __init__(self, database : str):
        self.connection = sqlite3.connect(database)
        self.name = database
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (message_id integer, chat_id integer, begin_date datetime default current_timestamp);".format(self.name))


    def read_by_chat_id(self, chat_id: int):
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE  chat_id = '{}';".format(self.name, chat_id)).fetchall()

    def check_old_messages(self, checkpoint_time : str):
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE begin_date < '{}'".format(self.name, checkpoint_time)).fetchall()

    def insert_message(self, chat_id: int, message_id: int, message_text=""):
        with self.connection:
            self.cursor.execute("INSERT INTO {}(chat_id, message_id, message_text) VALUES(?,?,?);".format(self.name), (chat_id, message_id, message_text))
        return (0)

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute("SELECT * FROM {}".format(self.name)).fetchall()
            return len(result)

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()