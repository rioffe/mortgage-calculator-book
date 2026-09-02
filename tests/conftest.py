import pytest

@pytest.fixture
def worked_example():
    """The Chapter 4.5 answer key: $200,000 / 6% / 30yr monthly."""
    return {
        "principal": 200_000,
        "annual_rate": 0.06,
        "term_years": 30,
        "payments_per_year": 12,
        "expected_payment": 1199.10,
    }
