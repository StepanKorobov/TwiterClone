import os
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import (
    Mapped,
    Relationship,
    declarative_base,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.orm.decl_api import DeclarativeMeta

# Загружаем переменные окружения
load_dotenv()


def get_database_url():
    """Функция получающая адрес БД, нужно для тестов"""
    if os.environ.get("ENV") == "test":
        db_user: str = os.getenv("TEST_DB_USER")
        db_password: str = os.getenv("TEST_DB_PASSWORD")
        db_host: str = os.getenv("TEST_DB_HOST")
        db_port: str = os.getenv("TEST_DB_PORT")
        db_name: str = os.getenv("TEST_DB_NAME")
    else:
        db_user: str = os.getenv("DB_USER")
        db_password: str = os.getenv("DB_PASSWORD")
        db_host: str = os.getenv("DB_HOST")
        db_port: str = os.getenv("DB_PORT")
        db_name: str = os.getenv("DB_NAME")

    database_url: str = (
        f"postgresql+asyncpg://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )

    return database_url


DATABASE_URL: str = get_database_url()
# Создаем асинхронный движок
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
# Создаём асинхронную сессию
async_session: sessionmaker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
# Создаём базу
Base: DeclarativeMeta = declarative_base()
# Сессия
session = async_session()

# Self-Referential таблица для связи Many-to-Many для таблицы Users
integration_followers = Table(
    "followers",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id"), primary_key=True),
)

# Таблица для связи Many-to-Many для таблиц Users и Tweets
integration_like = Table(
    "like",
    Base.metadata,
    Column("tweet_id", Integer, ForeignKey("tweets.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class Users(Base):
    """Таблица пользователей"""

    __tablename__ = "users"
    # Определяем поля таблицы
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str] = mapped_column(String(50), nullable=False)

    # Определяем связь One-to-Many с таблицей Tweets
    tweet: Mapped[List["Tweets"]] = Relationship(back_populates="author")
    # Определяем связь Many-to-Many с таблицей Tweets
    tweet_like: Mapped[Optional[List["Tweets"]]] = Relationship(
        secondary=integration_like, back_populates="user_like"
    )

    # Определяем связь Many-to-Many для таблицы Users самой с собой (свмоссылающаяся таблица)
    following: Mapped[List["Users"]] = Relationship(
        secondary=integration_followers,
        primaryjoin=id == integration_followers.c.user_id,
        secondaryjoin=id == integration_followers.c.following_id,
        back_populates="followers",
    )

    followers: Mapped[List["Users"]] = Relationship(
        secondary=integration_followers,
        primaryjoin=id == integration_followers.c.following_id,
        secondaryjoin=id == integration_followers.c.user_id,
        back_populates="following",
    )

    # метод класса для конвертации экземпляра класса в формат json
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweets(Base):
    """Таблица твитов"""

    __tablename__ = "tweets"
    # Определяем поля таблицы
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet: Mapped[str] = mapped_column(nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Определяем связь Many-to-One для с таблицей Users
    author: Mapped[List["Users"]] = Relationship(back_populates="tweet")
    # Определяем связь Many-to-Many с таблицей Users
    user_like: Mapped[Optional[List["Users"]]] = Relationship(
        secondary=integration_like, back_populates="tweet_like"
    )
    # Определяем связь One-to-Many с таблицей Media
    medias: Mapped[List["Media"]] = Relationship(
        back_populates="tweet", cascade="all"
    )

    # метод класса для конвертации экземпляра класса в формат json
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    """Таблица медиа, содержит путь к картинкам"""

    __tablename__ = "media"
    # Определяем поля таблицы
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_path: Mapped[str] = mapped_column(String(64))
    tweet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tweets.id"), nullable=True
    )

    # Определяем связь Many-to-One для с таблицей Tweets
    tweet: Mapped[Optional["Tweets"]] = Relationship(
        back_populates="medias", cascade="all"
    )

    # метод класса для конвертации экземпляра класса в формат json
    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
