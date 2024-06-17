from typing import List, Optional

from pydantic import BaseModel


class BaseTweetsPost(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]]


class BaseTweetsPostIn(BaseTweetsPost): ...


class BaseTweetsPostOut(BaseModel):
    result: bool
    tweet_id: int


class BaseOperationResultOut(BaseModel):
    result: bool


class BaseFollowers(BaseModel):
    id: int
    name: str


class BaseFollowing(BaseModel):
    id: int
    name: str


class BaseUser(BaseModel):
    id: int
    name: str
    followers: List[BaseFollowers | None]
    following: List[BaseFollowing | None]


class BaseUserInfoOut(BaseModel):
    result: bool
    user: BaseUser


class BaseLikes(BaseModel):
    user_id: int
    name: str


class BaseAuthor(BaseModel):
    id: int
    name: str


class BaseTweetsGet(BaseModel):
    id: int
    content: str
    attachments: List[str | None]
    author: BaseAuthor
    likes: List[BaseLikes | None]


class BaseTweetsGetOut(BaseModel):
    result: bool
    tweets: List[BaseTweetsGet]


class BaseMediaOut(BaseModel):
    result: bool
    media_id: int


class BaseErrorOut(BaseModel):
    result: bool
    error_type: str
    error_message: str
