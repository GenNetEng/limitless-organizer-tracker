from app.main import parse_cors_origins


def test_parse_cors_origins_strips_whitespace_around_commas():
    assert parse_cors_origins("http://localhost:5173, https://dashboard.example.com") == [
        "http://localhost:5173",
        "https://dashboard.example.com",
    ]


def test_parse_cors_origins_skips_blank_entries():
    assert parse_cors_origins("http://localhost:5173,,") == ["http://localhost:5173"]
