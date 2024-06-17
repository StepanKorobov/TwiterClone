# Проект TWITTER CORPORATE SERVICE

TWITTER CORPORATE SERVICE - Корпоративный сервис микроблогов, в котором сотрудники могут
размещать свои посты с текстом и медиа, а так же подписываться друг на друга, ну
и как же без лайков)

####
# ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fastapi)

<div align="middle">
   <img src="https://s10.gifyu.com/images/SfDy7.png" width="60%"></img>
</div>


## Установка

1. Клонируйте или скачайте репозиторий с gitlab/github
2. В случае первого запуска приложения, нужно выполнить команду `docker-compose run --rm postgresql` после появления надписи `database system is ready to accept connections` нажать сочетания клавиш`CTRL + C`, приступить к 3-му пункту
3. Введите команду `docker compose up -d` из папки с проектом


## Настройка

Нужно создать файл .env в корне проекта.

Указать переменные окружения для настройки базы данных.

*Пример:*
```bash
# Настройки для основной базы данных
# Имя пользователя БД
DB_USER = "admin"
# Пароль от БД
DB_PASSWORD = "admin"
# Хост от БД
DB_HOST = database
# Порт от БД
DB_PORT = 5432
# Имя БД
DB_NAME = "twitter"


# Настройки для тестовой базы дынных
# Имя пользователя БД
TEST_DB_USER = "test_user"
# Пароль от БД
TEST_DB_PASSWORD = "test_password"
# Хост от БД
TEST_DB_HOST = 127.0.0.1
# Порт от БД
TEST_DB_PORT = 6000
# Имя БД
TEST_DB_NAME = "test"
```

## Функционал

1) **Пользователь может добавить свой твит.**
![](https://s10.gifyu.com/images/SffEA.gif)
2) **Пользователь может удалить свой твит.**
![](https://s10.gifyu.com/images/SffhJ.gif)
3) **Пользователь может зафоловить другого пользователя.**
![](https://s10.gifyu.com/images/Sfflj.gif)
4) **Пользователь может отписаться от другого пользователя.**
![](https://s10.gifyu.com/images/SffnH.gif)
5) **Пользователь может отмечать твит как понравившийся.**
![](https://s12.gifyu.com/images/Sffnl.gif)
6) **Пользователь может убрать отметку «Нравится».**
![](https://s10.gifyu.com/images/SffuE.gif)
7) **Пользователь может получить ленту из твитов.**
![](https://s10.gifyu.com/images/SffDh.gif)
8) **Твит может содержать картинку.**
![](https://s12.gifyu.com/images/SfftU.gif)

## Endpoints

**Более подробная документация описана при помощи swagger, её можно посмотреть после запуска проекта: (ip сервера:8000/docs)**

1) Endpoint для загрузки твитов:
   - Method: POST 
   - Rout: /api/tweets
2) Endpoint для загрузки файлов из твита. Загрузка происходит через отправку формы.
    - Method: POST
    - Rout: /api/medias
3) Endpoint по удалению твита. В этом endpoint пользователь может удалить только свой собственный твит.
    - Method: DELETE
    - Rout: /api/tweets/<id>
4) Пользователь может поставить отметку «Нравится» на твит
   - Method: POST
   - Rout: /api/tweets/<id>/likes
5) Пользователь может убрать отметку «Нравится» с твита.
   - Method: DELETE
   - Rout: /api/tweets/<id>/likes
6) Пользователь может зафоловить другого пользователя.
   - Method: POST
   - Rout: /api/users/<id>/follow
7) Пользователь может убрать подписку на другого пользователя.
   - Method: DELETE
   - Rout: /api/users/<id>/follow
8) Пользователь может получить ленту с твитами.
   - Method: GET
   - Rout: /api/tweets
9) Пользователь может получить информацию о своём профиле:
   - Method: GET
   - Rout: /api/users/me

## Тестирование
**В проекте содержаться тесты, они нужны для тестирования работоспособности всех Эндпоинтов.**

*Для запуска понадобится:*
1) Установить необходимые библиотеки командой `pip install -r requarements_test.txt`.
2) Запустить тестовую базу данных командой `docker run --name testing_database --rm -e POSTGRES_USER=test_user -e POSTGRES_PASSWORD=test_password -e POSTGRES_DB=test -p 6000:5432 -it postgres`
3) Запустить тесты командой `pytest -v test/`

*Примечание к пункту 2 (в случае применения других настроек в .env):*
   - -e POSTGRES_USER=(нужно указать значение TEST_DB_USER из .env)
   - -e POSTGRES_PASSWORD=(нужно указать значение TEST_DB_PASSWORD из .env)
   - -e POSTGRES_DB=(нужно указать значение TEST_DB_NAME из .env)
   - -p (нужно указать значение TEST_DB_PORT из .env):5432

## Мониторинг
**Для мониторинга используется prometheus+grafana**

*Для входа понадобится:*

1) Зайти в grafana по адресу "ip-проекта:3000" либо "127.0.0.1:3000"
2) Залогиниться в grafana 
   - Логин: admin
   - Пароль: admin
3) Выбрать пункт Add data source и ввести следующие данные:
   - Name: Prometheus
   - Type: Prometheus
   - URL: http://prometheus:9090
   - Нажать Save & Test
4) В левой части экрана нажать на ***+***, выбрать ***import***, нажать ***upload .json file***, выбрать файл ***dashboard.json*** (лежит в паке проекта grafana)
5) заполнить данные:
   - Name: любое название
   - Prometheus: Prometheus
   - Нажать Import
