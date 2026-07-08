from rag_engine.observability.context import (
    get_request_id,
    reset_request_id,
    set_request_id,
)


def test_request_id_is_none_by_default():
    assert get_request_id() is None


def test_set_request_id_makes_value_available():
    token = set_request_id(
        "request-123"
    )

    try:
        assert (
            get_request_id()
            == "request-123"
        )

    finally:
        reset_request_id(
            token
        )


def test_reset_request_id_restores_previous_value():
    outer_token = set_request_id(
        "outer-request"
    )

    try:
        inner_token = set_request_id(
            "inner-request"
        )

        assert (
            get_request_id()
            == "inner-request"
        )

        reset_request_id(
            inner_token
        )

        assert (
            get_request_id()
            == "outer-request"
        )

    finally:
        reset_request_id(
            outer_token
        )