from hypothesis import given, assume, example
import hypothesis.strategies as st

from api.v2.models import parse_currency


@st.composite
def currency_values(draw, elements=st.floats(allow_nan=False, allow_infinity=False)):
    return draw(elements)
    
@st.composite
def currency_separator_strategy(draw):
    """Use this to generate a currency string with a separator"""
    initial_value = draw(currency_values(), label="Initial Value")
    assume(initial_value >= 1000)
    return f"{initial_value:,.2f}", f"{initial_value:.2f}"

@st.composite
def currency_negative_strategy(draw):
    """Use this to generate a negative currency string with parentheses"""
    initial_value = draw(currency_values(), label="Initial Value")
    assume(initial_value < 0)
    return f"({initial_value:.2f})", f"{initial_value:.2f}"

@st.composite
def currency_symbol_strategy(draw):
    """Use this to generate a currency string with a symbol"""
    intermediate_value, initial_value = draw(st.one_of(currency_separator_strategy(), currency_negative_strategy()))
    return f"${intermediate_value}", str(initial_value)

@st.composite
def currency(draw):
    value, expected = draw(st.one_of(currency_separator_strategy(), currency_negative_strategy(), currency_symbol_strategy()))
    return value, expected
    


@given(currency())
@example(("1,000.00", "1000.00"))
@example(("$(1,000)", "-1000.00"))
@example(("$341.122", "341.12"))
def test_validate_currency(s):
    value, expected = s
    try:
        parsed = parse_currency(value)
    except ValueError:
        assert expected is None, "ValueError should only be raised when the expected value is None"
        return
    assert parsed == expected