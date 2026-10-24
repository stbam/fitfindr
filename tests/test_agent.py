# tests/test_agent.py
from agent import _parse_query


def test_im_is_not_size_m():
    assert _parse_query("I'm looking for a jacket") == {
        "description": "jacket", "size": None, "max_price": None,
    }

def test_in_word_is_not_a_size():
    assert _parse_query("a jacket in red")["size"] is None
    assert _parse_query("something in the color green")["size"] is None

def test_explicit_sizes_still_parse():
    assert _parse_query("vintage graphic tee under $30, size M")["size"] == "M"
    assert _parse_query("leather jacket size xl")["size"] == "XL"
    assert _parse_query("tee in s/m")["size"] == "S/M"
    assert _parse_query("90s track jacket in size M")["description"] == "90s track jacket"

def test_filler_is_stripped_anywhere():
    assert _parse_query("please find me a dress")["description"] == "dress"
    assert _parse_query("show me boots")["description"] == "boots"
    assert _parse_query("i want a green fit")["description"] == "green fit"
