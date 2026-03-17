import pytest
from django.core.management import call_command


@pytest.fixture
def test_data(db):
    call_command("prezentation_data")
