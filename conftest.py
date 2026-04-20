"""
Root conftest.py — sets dummy env vars BEFORE any module-level imports.
This prevents pydantic-settings from failing when .env is absent in CI/tests.
"""
import os

os.environ.setdefault("BOT_TOKEN", "0000000000:AAFakeTokenForTestingOnly")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SUPPORT_CHAT_ID", "-1")
os.environ.setdefault("PLATFORM_URL", "http://platform.test")
os.environ.setdefault("PLATFORM_BOT_SHARED_SECRET", "test-secret")
