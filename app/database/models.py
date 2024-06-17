import os
import random
import string
from typing import Dict, List

import aiofiles
from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select

from database.database import Media, Tweets, Users, async_session

IMAGES_BASE_DIR_PATH: str = os.path.join(
    os.path.dirname(__file__), "media/user_post_images"
)
SYMBOLS: str = string.ascii_letters + string.digits


async def generate_random_filename() -> str:
    """
    Корутин генерирующий случайное имя файля
    :return: Случайное имя файла
    :rtype: str
    """
    # Генерируем список из случайных символов
    random_symbols_list: List = [random.choice(SYMBOLS) for _ in range(15)]
    # Объединяем список в строку
    random_filename_str: str = "".join(random_symbols_list)
    # Добавляем расширение файла
    random_filename: str = "".join([random_filename_str, ".jpg"])

    return random_filename


async def write_image_to_disk(
    file: bytes, file_name: str, user_api_key: str
) -> None:
    """
    Корутин записывающий файлы на диск
    :param file: Байтовый файл
    :type file: bytes
    :param file_name: Имя файла
    :type file_name: str
    :param user_api_key: Api-Key Пользователя
    :type user_api_key: str
    :return: Ничего не возвращает
    :rtype: None
    """
    # Путь до папки пользователя
    path_dir: str = "{}/{}".format(IMAGES_BASE_DIR_PATH, user_api_key)

    # Проверяем существует папка пользователя или нет, если нет, то создаёт
    if not os.path.exists(path_dir):
        os.mkdir(path_dir)

    # Путь до файла в папке пользователя
    image_path: str = os.path.join(path_dir, file_name)

    # Записываем файл на диск, в папку пользователя
    async with aiofiles.open(image_path, mode="wb") as f:
        await f.write(file)


async def remove_images_from_disk(file_paths: List[str]) -> None:
    """
    Корутин удаляющий файлы с диска при удалении поста
    :param file_paths: Список путей для файлов
    :type file_paths: List[str]
    :return: Ничего не возвращает
    :rtype: None
    """
    # Проходимся по списку и удаляем файлы
    for i_path in file_paths:
        # путь к удаляемому файлу
        file_path = f"{"/app/database/media"}/{i_path}"
        # Проверяем существует ли файл
        if os.path.exists(file_path):
            # удаляем файл
            os.remove(file_path)


async def get_user_from_api_key(api_key: str) -> Users | None:
    """
    Корутин возвращающий Users по Api-Key
    :param api_key: Api-Key пользователя
    :type api_key: str
    :return: Экземпляр класса Users
    :rtype: Users | None
    """
    async with async_session() as session:
        async with session.begin():
            # Запрос на получение пользователя по api_key
            user_query: Select = select(Users).where(Users.api_key == api_key)
            user_result: ChunkedIteratorResult = await session.execute(
                user_query
            )
            user: Users | None = user_result.scalars().one_or_none()

            return user


async def get_user_from_id(user_id: int) -> Dict | None:
    """
    Корутин возвращающий всю информацию о пользователе по его ID
    :param user_id: ИД пользователя
    :type user_id: int
    :return: Словарь со всей информацией о пользователе
    :rtype: Dict
    """
    async with async_session() as session:
        async with session.begin():
            # Запрос на получение пользователя, так же его подписчиков и на кого он подписан
            user_query: Select = (
                select(Users)
                .filter(Users.id == user_id)
                .options(
                    selectinload(Users.following),
                    selectinload(Users.followers),
                )
            )
            user_result: ChunkedIteratorResult = await session.execute(
                user_query
            )
            user: Users | None = user_result.scalars().one_or_none()

    # Если пользователь найден
    if user:
        # Создаём словарь с информацией о пользователе
        user_data: Dict = {
            "id": user.id,
            "name": user.user,
            "followers": [
                {"id": i_followers.id, "name": i_followers.user}
                for i_followers in user.followers
            ],
            "following": [
                {"id": i_following.id, "name": i_following.user}
                for i_following in user.following
            ],
        }

        return user_data

    return None


async def get_all_tweets_from_db() -> List[Dict]:
    """
    Корутин для получения списка всех твитов
    :return: Список твитов
    :rtype: List[Dict]
    """
    async with async_session() as sessions:
        async with sessions.begin():
            tweets_query: Select = (
                select(Tweets)
                .options(
                    selectinload(Tweets.author),
                    selectinload(Tweets.medias),
                    selectinload(Tweets.user_like),
                )
                .order_by(Tweets.id.desc())
            )
            tweets_result: ChunkedIteratorResult = await sessions.execute(
                tweets_query
            )
            tweets: Tweets = tweets_result.scalars().all()

    # Список словарей с информацией о твите
    tweets_list: List = list()

    # Проходимся циклом по результату, для создания словаря с информацией о твите
    for i_result in tweets:
        tweet: Dict = {
            "id": i_result.id,
            "content": i_result.tweet,
            "attachments": [i_image.media_path for i_image in i_result.medias],
            "author": {"id": i_result.author.id, "name": i_result.author.user},
            "likes": [
                {"user_id": i_like.id, "name": i_like.user}
                for i_like in i_result.user_like
            ],
        }

        # Добавляем твит к списку
        tweets_list.append(tweet)

    return tweets_list


async def write_image_to_db(file: bytes, user_api_key: str) -> int:
    """
    Корутин для записи пути(местонахождения) файла в БД
    :param file: картинка
    :type file: byte
    :param user_api_key: Api_Key
    :type user_api_key: str
    :return: id записи в БД
    :rtype: int
    """
    # Генерируем случайное имя файла
    # (нужно для предотвращения перезаписи файла в случае загрузки разных файлов с одинаковыми именами)
    file_name = await generate_random_filename()
    # Записываем файл на диск
    await write_image_to_disk(
        file=file, file_name=file_name, user_api_key=user_api_key
    )

    # Создаём путь для файла, который запишем в БД
    media_path: str = "user_post_images/{}/{}".format(user_api_key, file_name)
    # Создаём экземпляр класса Media для записи в БД
    media: Media = Media(media_path=media_path)

    # Записываем в БД
    async with async_session() as sessions:
        async with sessions.begin():
            sessions.add(media)
            await sessions.commit()

    # Получаем id новой записи
    media_id: int = media.id

    return media_id


async def write_post_to_db(tweet_text: str, author_id: int) -> int:
    """
    Корутин для записи твита в БД
    :param tweet_text: Тест из твита
    :type tweet_text: str
    :param author_id: id автора записи
    :type author_id: int
    :return: id записи в БД
    :rtype: int
    """
    # Создаём экземпляр класса Tweets для записи в БД
    tweet: Tweets = Tweets(tweet=tweet_text, author_id=author_id)

    # Записываем в БД
    async with async_session() as sessions:
        async with sessions.begin():
            sessions.add(tweet)
            await sessions.commit()

    # Получаем id новой записи
    tweet_id: int = tweet.id

    return tweet_id


async def write_likes_to_db(tweet_id: int, user: Users) -> None:
    """
    Корутин для записи лайков в БД
    :param tweet_id: id Твита
    :type tweet_id: str
    :param user: Экземпляр класса Users
    :type user: User
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем твит из БД
            tweet_query: Select = (
                select(Tweets)
                .filter(Tweets.id == tweet_id)
                .options(selectinload(Tweets.user_like))
            )
            tweet_result: ChunkedIteratorResult = await session.execute(
                tweet_query
            )
            tweet: Tweets | None = tweet_result.scalars().one_or_none()

            # Добавляем пользователя к лайкам в твите
            tweet.user_like.append(user)
            await session.commit()


async def write_following_to_db(user_id: int, following_id: int) -> None:
    """
    Корутин для записи подписки в БД
    :param user_id: id пользователя
    :type user_id: int
    :param following_id: id на кого подписываться
    :type following_id: int
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем пользователя, который будет подписываться
            user_query: Select = (
                select(Users)
                .filter(Users.id == user_id)
                .options(selectinload(Users.following))
            )
            user_result: ChunkedIteratorResult = await session.execute(
                user_query
            )
            user: Users = user_result.scalars().one_or_none()

            # Получаем пользователя на которого будем подписываться
            following_query: Select = select(Users).filter(
                Users.id == following_id
            )
            following_result: ChunkedIteratorResult = await session.execute(
                following_query
            )
            following: Users = following_result.scalars().one_or_none()

            # Добавляем подписку пользователю
            user.following.append(following)
            await session.commit()


async def update_image_tweet_id(
    image_id_list: List[int], tweet_id: int
) -> None:
    """
    Корутин для обновления Media, мы добавляем tweet_id
    так как изображения загружаются перед твитом, мы не может знать id твита,
    поэтому id твита к изображениям мы добавляем здесь
    :param image_id_list: Список состоящий из id картинок
    :type image_id_list: List[int]
    :param tweet_id: id твита
    :type tweet_id: int
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем медиа
            media_query: Select = select(Media).filter(
                Media.id.in_(image_id_list)
            )
            media_result: ChunkedIteratorResult = await session.execute(
                media_query
            )
            media: Media = media_result.scalars().all()

            # Проходимся по полученному списку медиа, и добавляем к ним id твита
            for i_media in media:
                i_media.tweet_id = tweet_id

            await session.commit()


async def delete_likes_from_db(tweet_id: int, user_id: int):
    """
    Корутин для удаления лайка из БД
    :param tweet_id: id Твита
    :type tweet_id: int
    :param user_id: id пользователя
    :type user_id: int
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем пользователя
            user_query: Select = select(Users).filter(Users.id == user_id)
            user_result: ChunkedIteratorResult = await session.execute(
                user_query
            )
            user: Users = user_result.scalars().one_or_none()

            # Получаем твит
            tweet_query: Select = (
                select(Tweets)
                .filter(Tweets.id == tweet_id)
                .options(selectinload(Tweets.user_like))
            )
            tweet_result: ChunkedIteratorResult = await session.execute(
                tweet_query
            )
            tweet: Tweets = tweet_result.scalars().one_or_none()

            # Удаляем пользователя из лайков в твите
            tweet.user_like.remove(user)
            await session.commit()


async def delete_tweet_from_db(tweet_id: int, user_id: int) -> bool:
    """
    Корутин для удаления твита из БД
    :param tweet_id: id твита
    :type tweet_id: int
    :param user_id: id пользователя, который хочет удалить твит
    :type user_id: int
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем твит
            tweet_query: Select = (
                select(Tweets)
                .filter(Tweets.id == tweet_id)
                .options(
                    selectinload(Tweets.medias), selectinload(Tweets.author)
                )
            )
            tweet_result: ChunkedIteratorResult = await session.execute(
                tweet_query
            )
            tweet: Tweets = tweet_result.scalars().one_or_none()

            # Если id пользователя и id автора твита совпадают, то удаляем твит, иначе нет
            if tweet.author.id == user_id:

                # Список содержащий пути к файлам из удаляемого твита (нужен для удаления изображений с диска)
                media_path_list: List[str] | None = [
                    media.media_path for media in tweet.medias
                ]

                # Удаляем твит
                await session.delete(tweet)
                await session.commit()

                # Если у поста были медиа фалы, то удаляем их с диска
                if media_path_list:
                    await remove_images_from_disk(file_paths=media_path_list)

                return True

            return False


async def delete_following(user_id: int, following_id: int) -> None:
    """
    Корутин для удаления подписки на пользователя
    :param user_id: id пользователя
    :type user_id: int
    :param following_id: id того, на кого подписан
    :type following_id: int
    :return: Ничего не возвращает
    :rtype: None
    """
    async with async_session() as session:
        async with session.begin():
            # Получаем пользователя, который подписан
            user_query: Select = (
                select(Users)
                .filter(Users.id == user_id)
                .options(selectinload(Users.following))
            )
            user_result: ChunkedIteratorResult = await session.execute(
                user_query
            )
            user: Users = user_result.scalars().one_or_none()

            # Получаем пользователя на которого подписан
            following_query: Select = select(Users).filter(
                Users.id == following_id
            )
            following_result: ChunkedIteratorResult = await session.execute(
                following_query
            )
            following: Users = following_result.scalars().one_or_none()

            # Удаляем подписку у пользователя
            user.following.remove(following)
            await session.commit()


# Нужен только для заполнения тестовыми данными (в конечной версии будет удалён)
async def testing():
    async with async_session() as session:
        async with session.begin():
            users_query = select(Users)
            users_result: ChunkedIteratorResult = await session.execute(
                users_query
            )
            users: Users = users_result.scalars().all()

            if len(users) == 0:
                user1 = Users(user="Test", api_key="test")
                user2 = Users(user="Josh", api_key="fd2f8f56-a060-4bba")
                user3 = Users(user="Ricardo", api_key="3c0da680-3c2d-4511")
                user4 = Users(user="Comedian", api_key="67b4a167-a3cb-4bb0")
                #
                # user1.following.append(user2)
                # user1.following.append(user3)
                # user3.following.append(user2)
                # # user2.followers.append(user1)
                # # user2.followers.append(user3)
                #
                session.add_all([user1, user2, user3, user4])
                session.commit()
