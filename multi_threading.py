from time import sleep, time
from functools import wraps
import datetime
from SQLighter import SQLighter

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
def parallel_check_for_old_messages(delta_time = 3, check_delay = 3):
  while True:
    sleep(check_delay) #  Тут мы чего-то доолго ждем / вычисляем / etc
    db_worker = SQLighter("messages")
    time_diff = datetime.datetime.now() - datetime.timedelta(minutes = 3)
    time_diff = time_diff.strftime("%Y-%m-%d %H:%M:%S")
    a = db_worker.check_old_messages(time_diff)
    print (a)
    print ("checking for old messages")
    db_worker.close()