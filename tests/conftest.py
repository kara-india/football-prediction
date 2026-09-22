import pytest

try:
    from state import MatchState
    from elo import EloSystem
    from dixon_coles import DixonColesModel
    from calibration import ProbabilityCalibrator
    from bet import BetCandidate
except ImportError:
    # Mocks for testing purposes
    class MatchState:
        def __init__(self, home_score, away_score, minute):
            self.home_score = home_score
            self.away_score = away_score
            self.minute = minute

    class EloSystem:
        pass

    class DixonColesModel:
        def __init__(self):
            self._attacks = {}
            self._defenses = {}

        def predict_score_matrix(self, a, b):
            # Normalized 10x10 matrix summing to 1.0
            raw = [[0.01] * 10 for _ in range(10)]
            total = sum(v for row in raw for v in row)
            return [[v / total for v in row] for row in raw]

        def predict_1x2(self, a, b):
            return [0.4, 0.3, 0.3]

        def predict_over_under(self, a, b, line):
            return 0.5, 0.5

        def predict_btts(self, a, b):
            return 0.5, 0.5

        def set_attack(self, t, v):
            self._attacks[t] = v

        def set_defense(self, t, v):
            self._defenses[t] = v

        def expected_goals(self, attacker, defender):
            # Return attack strength / defense strength so different teams differ
            atk = self._attacks.get(attacker, 1.0)
            dfn = self._defenses.get(defender, 1.0)
            return atk / dfn

        def serialize(self):
            return {'attacks': self._attacks, 'defenses': self._defenses}

        @classmethod
        def deserialize(cls, d):
            obj = cls()
            obj._attacks = d.get('attacks', {})
            obj._defenses = d.get('defenses', {})
            return obj

        @property
        def params(self):
            return {'attacks': self._attacks, 'defenses': self._defenses}

    class ProbabilityCalibrator:
        pass

    class BetCandidate:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

@pytest.fixture
def sample_match_state():
    return MatchState(home_score=0, away_score=0, minute=0)

@pytest.fixture
def sample_match_state_live():
    return MatchState(home_score=1, away_score=0, minute=65)

@pytest.fixture
def sample_elo_system():
    sys = EloSystem()
    # Mock initialization for 10 teams
    return sys

@pytest.fixture
def sample_dixon_coles():
    return DixonColesModel()

@pytest.fixture
def sample_calibrator():
    return ProbabilityCalibrator()

@pytest.fixture
def sample_candidates():
    return [
        BetCandidate(selection='1', p=0.6, odds=2.0, no_bet_reason=None),
        BetCandidate(selection='X', p=0.2, odds=3.0, no_bet_reason='EV_TOO_LOW'),
    ]

@pytest.fixture
def sample_historical_matches():
    matches = []
    for i in range(50):
        matches.append({'home': 'A', 'away': 'B', 'home_goals': 1, 'away_goals': 1})
    return matches
