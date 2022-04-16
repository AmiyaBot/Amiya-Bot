import os
import time
import passlib.handlers.bcrypt

from typing import Union
from datetime import timedelta
from pydantic import BaseModel
from fastapi import Request, Depends, HTTPException
from fastapi_login import LoginManager
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from core.database.user import Admin, Role, model_to_dict
from core.config import config


class LoginManagerMiddleware(LoginManager):
    def __init__(self, secret: str, token_url: str):
        super().__init__(secret, token_url, custom_exception=HTTPException(
            status_code=401,
            detail='用户权限失效',
            headers={'WWW-Authenticate': 'Bearer'}
        ))

    async def __call__(self, request: Request, security_scopes: SecurityScopes = None):
        token = await self._get_token(request)

        if token is None:
            raise self.not_authenticated_exception

        if security_scopes is not None and security_scopes.scopes:
            if not self.has_scopes(token, security_scopes):
                raise self.not_authenticated_exception

        return await self.get_user(request, token)

    async def get_user(self, request: Request, token: str):
        payload = self._get_payload(token)

        user_identifier = payload.get('sub')
        if user_identifier is None:
            raise self.not_authenticated_exception

        user: Admin = await self._load_user(user_identifier)

        if user is None or not user.role_id or user.role_id.active == 0:
            raise self.not_authenticated_exception

        if request.url.path not in user.role_id.access_path.split(','):
            raise HTTPException(
                status_code=403,
                detail='没有访问该接口的权限'
            )

        return user


class AuthModel(BaseModel):
    userId: Union[str, int]
    password: str


class AuthManager:
    login_url = '/login'
    token_url = '/token'
    manager = LoginManagerMiddleware(os.urandom(24).hex(), token_url=token_url)

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
            raise HTTPException(status_code=401, detail='用户不存在')

        if password != admin.password:
            raise HTTPException(status_code=401, detail='密码不正确')

        if not admin.role_id:
            raise HTTPException(status_code=401, detail='用户无角色权限')

        if admin.role_id.active == 0:
            raise HTTPException(status_code=401, detail='角色已被禁用')

        if admin.active == 0:
            raise HTTPException(status_code=401, detail='用户已被禁用')

        access_token = cls.manager.create_access_token(
            data=dict(sub=user_id),
            expires=timedelta(hours=12)
        )

        Admin.update(last_login=int(time.time())).where(Admin.user_id == user_id).execute()

        return {'access_token': access_token, 'admin': model_to_dict(admin)}

    @classmethod
    async def set_super_admin(cls, routes):
        if Role.get_or_none(id=1):
            Role.update(access_path=routes).where(Role.id == 1).execute()
        else:
            Role.create(
                id=1,
                role_name='超级管理员',
                access_path=routes,
                active=1
            )

        for item in config.admin.accounts:
            if not Admin.get_or_none(user_id=item):
                Admin.create(
                    user_id=item,
                    role_id=1,
                    password='admin123',
                    active=1
                )

        Admin.update(role_id=1).where(Admin.user_id.in_(config.admin.accounts)).execute()


@AuthManager.manager.user_loader()
def get_admin(user_id: str) -> Admin:
    return Admin.get_or_none(user_id=user_id)
