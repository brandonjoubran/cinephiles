import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture(autouse=True)
def clear_cache():
    from infrastructure.cache import cache
    cache.clear()
