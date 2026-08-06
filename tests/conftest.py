import pytest
from deduplic.config import settings
from deduplic import deduplic_set_workspace_dir


@pytest.fixture(autouse=True)
def isolate_workspace_environment():
    """Fixture that saves the original settings path and restores it after each test."""
    original_projects_dir = settings.projects_dir

    yield

    deduplic_set_workspace_dir(original_projects_dir)
