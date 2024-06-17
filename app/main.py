from contextlib import asynccontextmanager
from typing import Annotated, Dict, List

from fastapi import FastAPI, Header, Request, UploadFile, status
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from database.database import Base, Users, engine, session
from database.models import (
    delete_following,
    delete_likes_from_db,
    delete_tweet_from_db,
    get_all_tweets_from_db,
    get_user_from_api_key,
    get_user_from_id,
    testing,
    update_image_tweet_id,
    write_following_to_db,
    write_image_to_db,
    write_likes_to_db,
    write_post_to_db,
)
from shemas import (
    BaseMediaOut,
    BaseOperationResultOut,
    BaseTweetsGetOut,
    BaseTweetsPostIn,
    BaseTweetsPostOut,
    BaseUserInfoOut,
)

# Сообщение в случае ошибки авторизации (пользователь не найден)
ERROR_AUTHENTICATION: Dict = {
    "result": False,
    "error_type": "AuthenticationError",
    "error_message": "User is not found",
}


# Контекстный менеджер для выполнения действий
# до запуска приложения и после завершения работы
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы в БД, если они не созданы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Нужен только для заполнения тестовыми данными
    # (в конечной версии будет удалён)
    await testing()

    yield

    # Завершаем сессию
    await session.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/api/users/me", response_model=BaseUserInfoOut)
async def get_users_me(api_key: Annotated[str | None, Header()] = None):
    """Returns information about the current user"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден, то возвращаем информацию по нему
    if user:
        # Собираем информацию о профиле пользователя из БД
        user_dict: Dict = await get_user_from_id(user_id=user.id)

        # Собираем ответ
        user_data: Dict = {"result": True, "user": user_dict}

        return user_data

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.get("/api/tweets", response_model=BaseTweetsGetOut)
async def get_all_tweets(api_key: Annotated[str | None, Header()] = None):
    """Returns a list of all tweets"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден, то возвращаем твиты
    if user:
        # Получаем список твитов
        tweets_list: List = await get_all_tweets_from_db()
        # Готовим ответ
        tweets: Dict = {"result": True, "tweets": tweets_list}

        return tweets

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.get("/api/users/{id}", response_model=BaseUserInfoOut)
async def get_user_by_id(id: int):
    """Returns information about any user by his ID"""
    # Получаем информацию о пользователе по id
    user_info: Dict | None = await get_user_from_id(user_id=id)

    # Если пользователь найден, то возвращаем информацию по нему
    if user_info:
        user: Dict = {"result": True, "user": user_info}

        return user

    # Ответ в случае, если пользователь не найден
    error_response: Dict = {
        "result": False,
        "error_type": "NotFound",
        "error_message": "User not found",
    }

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response
    )


@app.post("/api/tweets", response_model=BaseTweetsPostOut)
async def post_tweets(
        tweet: BaseTweetsPostIn, api_key: Annotated[str | None, Header()] = None
):
    """Loads a user's tweet"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден, то возвращаем твиты
    if user:
        # Извлекаем текст твита
        tweet_text: str = tweet.tweet_data
        # Извлекаем список медиа
        media_list: List[int | None] = tweet.tweet_media_ids

        # Записываем твит в БД, и получаем его id
        tweet_id: int = await write_post_to_db(
            tweet_text=tweet_text, author_id=user.id
        )

        # Если есть медиа, то обновляем id твита у медиа
        if media_list:
            await update_image_tweet_id(
                image_id_list=media_list, tweet_id=tweet_id
            )

        return {"result": True, "tweet_id": tweet_id}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.post("/api/medias", response_model=BaseMediaOut)
async def post_medias(
        file: UploadFile, api_key: Annotated[str | None, Header()] = None
):
    """Loads a user's media"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден,
    # то записываем медиа, а затем возвращаем id медиа
    if user:
        # Читаем файлы в байты
        file_byte: bytes = await file.read()
        # Записываем медиа в БД и на диск, получаем его id
        media_id: int = await write_image_to_db(
            file=file_byte, user_api_key=api_key
        )

        return {"result": True, "media_id": media_id}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.post("/api/users/{id}/follow", response_model=BaseOperationResultOut)
async def following(id: int, api_key: Annotated[str | None, Header()] = None):
    """Subscribe to any user"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден
    if user:
        # Записываем подписку в БД
        await write_following_to_db(user_id=user.id, following_id=id)

        return {"result": True}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.post("/api/tweets/{id}/likes", response_model=BaseOperationResultOut)
async def like(id: int, api_key: Annotated[str | None, Header()] = None):
    """Like any post"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден
    if user:
        # Записываем лайк в БД
        await write_likes_to_db(tweet_id=id, user=user)

        return {"result": True}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.delete("/api/tweets/{id}", response_model=BaseOperationResultOut)
async def remove_tweets(id: int, api_key: Annotated[str | None, Header()] = None):
    """Allows you to delete your tweet"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден
    if user:
        # Удаляем твит
        result: bool = await delete_tweet_from_db(tweet_id=id, user_id=user.id)

        if result:
            return {"result": True}

        # Ответ в случае, если пользователь не являет автором твита
        error_response: Dict = {
            "result": False,
            "error_type": "UserError",
            "error_message": "the user is not the author of the tweet",
        }

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content=error_response
        )

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.delete("/api/users/{id}/follow", response_model=BaseOperationResultOut)
async def unfollowing(id: int, api_key: Annotated[str | None, Header()] = None):
    """Allows you to unfollow another user"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден
    if user:
        # Удалям подписку у пользователя
        await delete_following(user_id=user.id, following_id=id)

        return {"result": True}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.delete("/api/tweets/{id}/likes", response_model=BaseOperationResultOut)
async def remove_like(id: int, api_key: Annotated[str | None, Header()] = None):
    """Allows you to remove a like from a tweet"""
    # Проверяем наличие пользователя
    user: Users | None = await get_user_from_api_key(api_key)

    # Если пользователь найден
    if user:
        # удаляем лайк пользователя
        await delete_likes_from_db(tweet_id=id, user_id=user.id)

        return {"result": True}

    # Ответ в случае ошибки аутентификации (пользователь не найден)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, content=ERROR_AUTHENTICATION
    )


@app.get('/debug-sentry')
async def trigger_error():
    division_by_zero = 1 / 0


@app.exception_handler(500)
async def error_handler(request: Request, exc: Exception):
    # получаем тип ошибки
    error_type: str = str(type(exc))[8:-2]
    # ответ содержащий тип ошибки и сообщение
    response: Dict = {
        "result": False,
        "error_type": error_type,
        "error_message": str(exc),
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response
    )
