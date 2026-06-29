from core.parser import parse_resume


def test_parser_skips_blank_lines():
    text = "Line one.\n\n\nLine two.\n"
    blocks = parse_resume(text)
    assert len(blocks) == 2
    assert blocks[0].id == "L001"
    assert blocks[1].id == "L002"


def test_parser_strips_whitespace():
    blocks = parse_resume("   spaced out line   \n")
    assert blocks[0].text == "spaced out line"


def test_parser_empty_input():
    assert parse_resume("") == []