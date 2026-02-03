from typing import Any
from collections.abc import Iterator

import pytest
from pymongo import MongoClient
from pymongo.database import Collection, Database
from faker import Faker

from src.core.config import settings


faker = Faker()


@pytest.fixture(scope="session")
def client() -> Iterator[MongoClient[Any]]:
    client = MongoClient(settings.mongo_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def db(client: MongoClient[Any]) -> Iterator[Database[Any]]:
    db = client["test_db"]
    yield db
    client.drop_database("test_db")


@pytest.fixture(scope="class")
def collection(db: Database[Any]) -> Iterator[Collection[Any]]:
    col = db["test_col"]
    yield col
    col.drop()


@pytest.fixture
def sample() -> dict[str, str]:
    return {
        "username": faker.user_name(),
        "password": faker.password()
    }
