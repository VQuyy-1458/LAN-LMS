"""Thành viên 4: triển khai endpoint submissions theo hợp đồng API.

Chưa đăng ký router trong main.py; gắn dependency xác thực/phân quyền trước khi tích hợp.
"""
from fastapi import APIRouter

router = APIRouter(tags=["submissions"])
