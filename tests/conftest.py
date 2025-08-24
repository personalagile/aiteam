from __future__ import annotations

import os

import django
import pytest


@pytest.fixture(scope="session", autouse=True)
def django_setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiteam.settings")
    django.setup()
