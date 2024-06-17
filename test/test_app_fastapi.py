import pytest
from app.database.database import Users
from httpx import AsyncClient
from sqlalchemy.future import select

from conftest import ac, async_session_maker_test


async def test_add_user_to_db():
    """Тест на работу БД, добавляем пользователей и проверяем"""
    async with async_session_maker_test() as session:
        user1: Users = Users(user="Pytest", api_key="pytest")
        user2: Users = Users(user="Josh", api_key="a5c69a74-00e6-4f9b-8ba9-ee5e51f1aef1")
        user3: Users = Users(user="Ricardo", api_key="0f977897-5efc-4d16-8648-d50722ac988b")
        user4: Users = Users(user="Comedian", api_key="a41efa05-303b-486d-bec7-3fe50533035b")

        session.add(user1)
        session.add(user2)
        session.add(user3)
        session.add(user4)
        await session.commit()

        query = select(Users)
        result = await session.execute(query)
        results = result.scalars().all()
        result_json = [i.to_json() for i in results]

        users_json = [
            {"id": 1, "user": "Pytest", "api_key": "pytest"},
            {
                "id": 2,
                "user": "Josh",
                "api_key": "a5c69a74-00e6-4f9b-8ba9-ee5e51f1aef1",
            },
            {
                "id": 3,
                "user": "Ricardo",
                "api_key": "0f977897-5efc-4d16-8648-d50722ac988b",
            },
            {
                "id": 4,
                "user": "Comedian",
                "api_key": "a41efa05-303b-486d-bec7-3fe50533035b",
            },
        ]

        assert result_json == users_json, "no users added"


@pytest.mark.parametrize("route", ["/api/users/me", "/api/users/1", "/api/tweets"])
async def test_all_routs_get(ac: AsyncClient, route: str):
    """Тест всех GET ендпоинтов на доступность"""
    response = await ac.get(route, headers={"Api-Key": "pytest"})

    assert response.status_code == 200


async def test_user_me_response(ac: AsyncClient):
    """Тест отдачи профиля пользователя"""
    response = await ac.get("/api/users/me", headers={"Api-Key": "pytest"})
    expected_response = {
        "result": True,
        "user": {"id": 1, "name": "Pytest", "followers": [], "following": []},
    }

    assert response.status_code == 200
    assert response.json() == expected_response


async def test_user_me_fail_user(ac: AsyncClient):
    """Тест отдачи профиля, если пользователь не найден"""
    response = await ac.get("/api/users/me", headers={"Api-Key": "no_such_key_exists"})

    expected_response = {
        "result": False,
        "error_type": "AuthenticationError",
        "error_message": "User is not found",
    }

    assert response.status_code == 401
    assert response.json() == expected_response


async def test_user_get_from_id(ac: AsyncClient):
    """Тест на получение профиля юзера по id"""
    response = await ac.get("/api/users/2")
    expected_response = {
        "result": True,
        "user": {"id": 2, "name": "Josh", "followers": [], "following": []},
    }

    assert response.status_code == 200
    assert response.json() == expected_response


async def test_user_get_from_id_not_found(ac: AsyncClient):
    """Тест на получение профиля пользователя, если пользователь не найден"""
    response = await ac.get("/api/users/222")
    expected_response = {
        "result": False,
        "error_type": "NotFound",
        "error_message": "User not found",
    }

    assert response.status_code == 404
    assert response.json() == expected_response


async def test_tweets_get(ac: AsyncClient):
    """Тест на работу роута по получения твитов"""
    response = await ac.get("/api/tweets", headers={"Api-Key": "pytest"})
    expected_response = {"result": True, "tweets": []}

    assert response.status_code == 200
    assert response.json() == expected_response


async def test_tweets_get_authorisation_error(ac: AsyncClient):
    """Тест на работу роута по получения твитов, в случае ошибки авторизации"""
    response = await ac.get("/api/tweets", headers={"Api-Key": "no_such_key_exists"})
    expected_response = {
        "result": False,
        "error_type": "AuthenticationError",
        "error_message": "User is not found",
    }

    assert response.status_code == 401
    assert response.json() == expected_response


async def test_user_following_post(ac: AsyncClient):
    """Тест на добавление подписки пользователю"""
    response_follow = await ac.post(
        "/api/users/3/follow", headers={"Api-Key": "pytest"}
    )
    expected_response_follow = {"result": True}

    response_profile = await ac.get("/api/users/me", headers={"Api-Key": "pytest"})
    expected_response_profile = {
        "result": True,
        "user": {
            "id": 1,
            "name": "Pytest",
            "followers": [],
            "following": [{"id": 3, "name": "Ricardo"}],
        },
    }

    assert response_follow.status_code == 200
    assert response_follow.json() == expected_response_follow

    assert response_profile.status_code == 200
    assert response_profile.json() == expected_response_profile


async def test_user_unfollowing_delete(ac: AsyncClient):
    """Тест на удаление подписки у пользователя"""
    response_unfollow = await ac.delete(
        "/api/users/3/follow", headers={"Api-Key": "pytest"}
    )
    expected_response_unfollow = {"result": True}

    response_profile = await ac.get("/api/users/me", headers={"Api-Key": "pytest"})
    expected_response_profile = {
        "result": True,
        "user": {"id": 1, "name": "Pytest", "followers": [], "following": []},
    }

    assert response_unfollow.status_code == 200
    assert response_unfollow.json() == expected_response_unfollow

    assert response_profile.status_code == 200
    assert response_profile.json() == expected_response_profile


async def test_tweet_post(ac: AsyncClient):
    """Тест на написание твита без картинок"""
    tweet = {
        "tweet_data": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
        "tweet_media_ids": [],
    }

    response_tweet_post = await ac.post(
        "/api/tweets", headers={"Api-Key": "pytest"}, json=tweet
    )
    expected_response_tweet_post = {"result": True, "tweet_id": 1}

    response_tweet_get = await ac.get("/api/tweets", headers={"Api-Key": "pytest"})
    expected_response_tweet_get = {
        "result": True,
        "tweets": [
            {
                "id": 1,
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
                "attachments": [],
                "author": {"id": 1, "name": "Pytest"},
                "likes": [],
            }
        ],
    }

    assert response_tweet_post.status_code == 200
    assert response_tweet_post.json() == expected_response_tweet_post

    assert response_tweet_get.status_code == 200
    assert response_tweet_get.json() == expected_response_tweet_get


async def test_tweet_delete_other(ac: AsyncClient):
    """Тест на удаление твита другим пользователем (не автором)"""
    response_tweet_delete = await ac.delete(
        "/api/tweets/1", headers={"Api-Key": "a41efa05-303b-486d-bec7-3fe50533035b"}
    )
    expected_response_tweet_delete = {
        "result": False,
        "error_type": "UserError",
        "error_message": "the user is not the author of the tweet",
    }

    assert response_tweet_delete.status_code == 403
    assert response_tweet_delete.json() == expected_response_tweet_delete


async def test_tweet_delete(ac: AsyncClient):
    """Тест на удаление твита без картинок"""
    response_tweet_delete = await ac.delete(
        "/api/tweets/1", headers={"Api-Key": "pytest"}
    )
    expected_response_tweet_delete = {"result": True}

    assert response_tweet_delete.status_code == 200
    assert response_tweet_delete.json() == expected_response_tweet_delete


async def test_user_like_post(ac: AsyncClient):
    """Тест на добавление лайка"""
    tweet = {
        "tweet_data": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
        "tweet_media_ids": [],
    }

    await ac.post("/api/tweets", headers={"Api-Key": "pytest"}, json=tweet)

    response_like = await ac.post(
        "/api/tweets/2/likes",
        headers={"Api-Key": "0f977897-5efc-4d16-8648-d50722ac988b"},
    )
    expected_response_like = {"result": True}

    response_tweet = await ac.get("/api/tweets", headers={"Api-Key": "pytest"})
    expected_response_tweet = {
        "result": True,
        "tweets": [
            {
                "id": 2,
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
                "attachments": [],
                "author": {"id": 1, "name": "Pytest"},
                "likes": [{"user_id": 3, "name": "Ricardo"}],
            }
        ],
    }

    assert response_like.status_code == 200
    assert response_like.json() == expected_response_like

    assert response_tweet.status_code == 200
    assert response_tweet.json() == expected_response_tweet


async def test_user_like_delete(ac: AsyncClient):
    """Тест на удаление лайка"""
    response_like = await ac.delete(
        "/api/tweets/2/likes",
        headers={"Api-Key": "0f977897-5efc-4d16-8648-d50722ac988b"},
    )
    expected_response_like = {"result": True}

    response_tweet = await ac.get("/api/tweets", headers={"Api-Key": "pytest"})
    expected_response_tweet = {
        "result": True,
        "tweets": [
            {
                "id": 2,
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
                "attachments": [],
                "author": {"id": 1, "name": "Pytest"},
                "likes": [],
            }
        ],
    }

    assert response_like.status_code == 200
    assert response_like.json() == expected_response_like

    assert response_tweet.status_code == 200
    assert response_tweet.json() == expected_response_tweet
