import sqlite3
import datetime

class SQLmessages:
    def __init__(self, database_name : str):
        self.connection = sqlite3.connect(database_name)
        self.name = database_name
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (message_id integer, chat_id integer, begin_date datetime, message_text text);".format(self.name))

    def read_by_chat_id(self, chat_id: int):
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE  chat_id = '{}';".format(self.name, chat_id)).fetchall()

    def check_old_messages(self, time_diff : str):
        with self.connection:
            return self.cursor.execute("SELECT * FROM {} WHERE begin_date < '{}'".format(self.name, time_diff)).fetchall()

    def insert_message(self, chat_id: int, message_id: int, message_text=""):
        with self.connection:
            current_time = datetime.datetime.now()
            current_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO {}(chat_id, message_id, message_text, begin_date) VALUES(?,?,?,?);".format(self.name), (chat_id, message_id, message_text, current_time))
        return (0)

    def __len__(self):
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

test_class = SQLmessages("test_name")
print(len(test_class))