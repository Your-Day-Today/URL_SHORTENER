from flask import Flask, request, render_template, redirect  # Методы для создания веб интерфейса
from math import floor  # Метод математичесского округления
from sqlite3 import OperationalError  # Метод возвращающий ошибку происходящую при взаимодействии с базой данных
import string  # Метод содержащий текстовые константы и вспомагательные классы для работы с текстом
import sqlite3  # Метод для взаимодействия с базой данных

# Импорт модулей для работы со ссылками и строками стандарта ascii, под Python 2 и Python 3
try:
    from urllib.parse import urlparse  # Импорт модуля для парсинга ссылок (Python 3)
    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Импорт модуля для парсинга ссылок (Python 2)
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import base64

# Предполагается, что файл базы данных urls.db находится в директории проекта
app = Flask(__name__)  # Инициализация веб интерфейса
host = 'http://localhost:5000/'  # Локальный адрес доступа к веб интерфейсу


def table_check():
    '''Создание таблицы в базе данных, если таковой не существует'''
    with sqlite3.connect('urls.db') as conn:  # Установление соединения с базой данных
        cursor = conn.cursor()  # Инициализация курсора
        try:  # Попытка отправки запроса на создание таблицы
            cursor.execute("CREATE TABLE WEB_URL(ID INT PRIMARY KEY AUTOINCREMENT, URL TEXT NOT NULL);")
        except OperationalError:  # В случае если произошла ошибка
            pass  # Продолжить работу алгоритма


def toBase62(num, b=62):
    '''Функция кодирования десятичного числа в строку формата Base62'''
    if b <= 0 or b > 62:
        return 0
    base = string.digits + ascii_lowercase + ascii_uppercase  # Формировании строки всех используемых символов
    r = num % b  # Возврат остатка от деления входящего числа на 62
    res = base[r]  # Возврат значения строки используемых символов соответствующего r
    q = floor(num / b)  # Возврат целочисленной части от деления входящего числа на 62
    while q:  # До тех пор пока целочисленная часть не равна нулю
        r = q % b  # Возврат остатка от деления на 62
        q = floor(q / b)  # Возврат целочисленной части от деления на 62
        res += base[int(r)]  # Добавление символа из строки всех используемых символов по остатку в роли индекса
    return res  # Возврат результата


def toBase10(num, b=62):
    '''Функция декодирования строки формата Base62 в десятичное число '''
    base = string.digits + ascii_lowercase + ascii_uppercase  # Формировании строки всех используемых символов
    lim = len(num)  # Задание границы итератора
    res = 0  # Назначение переменной для записи результата
    for i in range(lim):  # Для каждого символа из строки num
        res = b * res + base.find(num[i])  # Расчет итогового значения десятичного числа
    return res  # Возврат результата


@app.route('/', methods=['GET', 'POST']) # Задание маршрута домашней страницы
def home():
    '''Основная страница сервиса, принимающая ссылки пользователя и возвращающая результат'''
    if request.method == 'POST': # Если запрос с веб формы получен по методу POST
        original_url = str_encode(request.form.get('url')) # Считать из формы ссылку для сокращения
        if urlparse(original_url).scheme == '': # Если отсутствует http:// часть
            url = 'http://' + original_url # Нормализация полученной ссылки
        else: # В противном случа
            url = original_url # Нормализация не требуется
        with sqlite3.connect('urls.db') as conn: # Установление соединения с базой данных
            cursor = conn.cursor() # Инициализация курсора
            # Кодирование оригинальной ссылки пользователя и запись в базу данных
            res = cursor.execute('INSERT INTO WEB_URL (URL) VALUES (?)',[base64.urlsafe_b64encode(url)])
            encoded_string = toBase62(res.lastrowid) # Кодирование индекса записи оригинальной ссылки
        return render_template('home.html', short_url=host + encoded_string) # Отображение ссылки для пользователя
    return render_template('home.html') # Если запрос POST не получен, осображать основую страницу сервиса


@app.route('/documentation.html') # Задание маршрута страницы документации
def documentation():
    '''Страница документации'''
    return render_template('documentation.html') # Отображение страницы документации


@app.route('/<short_url>') # Задание маршрута для любой ранее сокращённой ссылки для переадресации
def redirect_short_url(short_url):
    '''Алгоритм переадресации пользователя короткой ссылки на оригинальный URL'''
    decoded = toBase10(short_url) # Декодирования индекса оригинальной ссылки в базе данных
    url = host  # fallback if no URL is found
    with sqlite3.connect('urls.db') as conn: # Установление соединения с базой данных
        cursor = conn.cursor() # Инициализация курсора
        # Получение закодированной строки оригинальной ссылки из базы данных
        res = cursor.execute('SELECT URL FROM WEB_URL WHERE ID=?', [decoded])
        try:
            short = res.fetchone() # Возврат одного объекта
            if short is not None: # TЕсли он существует
                url = base64.urlsafe_b64decode(short[0]) # Декодирование оригинальной ссылки
        except Exception as e: # В случае ошибки
            print(e) # Отобразить ошибку
    return redirect(url) # Переадресовать пользователя по оригинальной ссылке


if __name__ == '__main__': # В случаее запуска скрипта не из стороннего файла
    table_check() # Создание таблицы в случае отсутствия
    app.run(debug=True) # Запуск веб интерфейса
