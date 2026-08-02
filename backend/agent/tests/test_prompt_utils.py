from app.utils.prompt_utils import load_prompt


def test_load_prompt_reads_gateway_file():
    text = load_prompt("client/gateway_prompt.md")
    assert "route_target" in text


def test_load_prompt_missing_returns_empty():
    assert load_prompt("client/does_not_exist.md") == ""
