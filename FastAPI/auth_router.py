from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
import os
import secrets
from typing import Optional

router = APIRouter(tags=["auth"])

#从环境变量读取管理员账号
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

#内存token存储
ACTIVE_TOKENS = set()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    """
    登录接口: POST /login
    请求体: {"username": "...", "password": "..."}
    返回: {"success": True, "token": "..."}
    """
    if req.username == ADMIN_USERNAME and req.password == ADMIN_PASSWORD:
        token = secrets.token_hex(16)
        ACTIVE_TOKENS.add(token)
        return {"success": True, "token": token}
    else:
        raise HTTPException(status_code=401, detail="用户名或账号错误")
    
@router.post("/logout")
async def logout(x_token: Optional[str] = Header(None)):
    """
    注销：从 header 'x-token' 中读取 token 并删除（可用 Authorization: Bearer ... 替代）
    """
    token = x_token
    if not token:
        raise HTTPException(status_code=400, detail="缺少 token")
    ACTIVE_TOKENS.discard(token)
    return {"success": True}

def require_token(x_token: Optional[str] = Header(None)):
    if not x_token or x_token not in ACTIVE_TOKENS:
        raise HTTPException(status_code=401, detail="未认证或 token 无效")
    return x_token