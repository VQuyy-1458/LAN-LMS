"""Thành viên 3: triển khai endpoint courses theo hợp đồng API.

Chưa đăng ký router trong main.py; gắn dependency xác thực/phân quyền trước khi tích hợp.
"""
from fastapi import APIRouter

router = APIRouter(tags=["courses"])
