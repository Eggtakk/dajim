from data.schema import merchant_code_to_category


def test_known_codes_map_to_expected_categories():
    assert merchant_code_to_category("5811") == "delivery"
    assert merchant_code_to_category("5814") == "cafe"
    assert merchant_code_to_category("5651") == "shopping"
    assert merchant_code_to_category("4899") == "subscription"


def test_unknown_code_maps_to_none():
    assert merchant_code_to_category("0000") is None
