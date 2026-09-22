def normalize_fixture(raw_api_response: dict) -> dict:
    return raw_api_response

def normalize_lineup(raw_api_response: dict) -> list:
    return raw_api_response if isinstance(raw_api_response, list) else [raw_api_response]

def normalize_events(raw_api_response: dict) -> list:
    return raw_api_response if isinstance(raw_api_response, list) else [raw_api_response]

def normalize_statistics(raw_api_response: dict) -> dict:
    return raw_api_response

def normalize_odds(raw_api_response: dict) -> list:
    return raw_api_response if isinstance(raw_api_response, list) else [raw_api_response]

def normalize_player(raw_api_response: dict) -> dict:
    return raw_api_response
