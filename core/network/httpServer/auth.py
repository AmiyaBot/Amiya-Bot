import os
import passlib.handlers.bcrypt

from typing import Union
from datetime import timedelta
from pydantic import BaseModel
from fastapi import Depends, HTTPException
from fastapi_login import LoginManager
from fastapi.security import OAuth2PasswordRequestForm
from core.database.user import Admin


class AuthModel(BaseModel):
    userId: Union[str, int]
    password: str


class AuthManager:
    login_url = '/login'
    token_url = '/token'
    manager = LoginManager(os.urandom(24).hex(), token_url=token_url)

    @classmethod
    def depends(cls) -> Admin:
        return Depends(cls.manager)

    @classmethod
    async def token(cls, data: OAuth2PasswordRequestForm = Depends()):
        return await cls.__access(data.username, data.password)

    @classmethod
    async def login(cls, data: AuthModel):
        return await cls.__access(data.userId, data.password)

    @classmethod
    async def __access(cls, user_id, password):
        admin = get_admin(user_id)

        if not admin:
            raise HTTPException(
                status_code=401,
                detail='用户不存在'
            )

        if password != admin.password:
            raise HTTPException(
                status_code=401,
                detail='密码不正确'
            )

        if admin.active == 0:
            raise HTTPException(
                status_code=401,
                detail='用户已被禁用'
            )

        access_token = cls.manager.create_access_token(
            data=dict(sub=user_id),
            expires=timedelta(hours=12)
        )

        return {'access_token': access_token, 'token_type': 'bearer'}


@AuthManager.manager.user_loader()
def get_admin(user_id: str) -> Admin:
    return Admin.get_or_none(user_id=user_id)
