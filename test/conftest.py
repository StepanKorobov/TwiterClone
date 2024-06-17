import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Тесты работают только если отправить переменную окружения, до подключения модулей
os.environ["ENV"] = "test"

from app.database.database import Base
from app.main import app


def get_database_url():
    """Функция получающая данные для подключения к тестовой БД """
    db_user: str = os.getenv("TEST_DB_USER")
    db_password: str = os.getenv("TEST_DB_PASSWORD")
    db_host: str = os.getenv("TEST_DB_HOST")
    db_port: str = os.getenv("TEST_DB_PORT")
    db_name: str = os.getenv("TEST_DB_NAME")

    database_url: str = (
        f"postgresql+asyncpg://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )

    return database_url


# Получаем адрес для подключения к БД
DATABASE_URL_TEST: str = get_database_url()

# Создаём движёк
engine_test = create_async_engine(DATABASE_URL_TEST, future=True, poolclass=NullPool)
# Создаём session maker
async_session_maker_test = sessionmaker(
    engine_test, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="session")
async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    yield async_session_maker_test


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# SETUP
@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def ac():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
