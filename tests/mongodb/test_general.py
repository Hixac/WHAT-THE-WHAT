from typing import Any

import pytest
from pymongo.database import Collection

from .fixtures import *


class TestMongoDB:
    def test_insert_and_find(self, collection: Collection[Any], sample: dict[str, str]):
        _ = collection.insert_one(sample)

        doc = collection.find_one({"username": sample["username"]})
        assert doc is not None
