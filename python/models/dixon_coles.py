import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

class DixonColesModel:
    def __init__(self):
        self.attack_params = {}
        self.defense_params = {}
        self.home_advantage = 0.3
        self.rho = 0.0
        self.teams = []
        
    def _tau(self, x, y, lambda_h, mu_a, rho):
        if x == 0 and y == 0:
            return max(1.0 - lambda_h * mu_a * rho, 1e-8)
        elif x == 0 and y == 1:
            return max(1.0 + lambda_h * rho, 1e-8)
        elif x == 1 and y == 0:
            return max(1.0 + mu_a * rho, 1e-8)
        elif x == 1 and y == 1:
            return max(1.0 - rho, 1e-8)
        else:
            return 1.0
            
    def _lambda_h(self, home_id, away_id):
        alpha_h = self.attack_params.get(home_id, 0.1)
        beta_a = self.defense_params.get(away_id, 0.1)
        gamma = self.home_advantage
        return np.exp(alpha_h + beta_a + gamma)
        
    def _mu_a(self, home_id, away_id):
        alpha_a = self.attack_params.get(away_id, 0.1)
        beta_h = self.defense_params.get(home_id, 0.1)
        return np.exp(alpha_a + beta_h)

    def _log_likelihood(self, params, match_data, xi, current_time):
        n_teams = len(self.teams)
        alpha = params[:n_teams]
        beta = params[n_teams:2*n_teams]
        gamma = params[2*n_teams]
        rho = params[2*n_teams+1]
        
        self.attack_params = dict(zip(self.teams, alpha))
        self.defense_params = dict(zip(self.teams, beta))
        self.home_advantage = gamma
        self.rho = rho
        
        ll = 0.0
        for _, row in match_data.iterrows():
            h_id = row['home_id']
            a_id = row['away_id']
            h_goals = row['home_goals']
            a_goals = row['away_goals']
            m_time = row['time']
            
            lam = self._lambda_h(h_id, a_id)
            mu = self._mu_a(h_id, a_id)
            
            p_h = poisson.pmf(h_goals, lam)
            p_a = poisson.pmf(a_goals, mu)
            t = self._tau(h_goals, a_goals, lam, mu, rho)
            
            w = np.exp(-xi * (current_time - m_time))
            prob = max(p_h * p_a * t, 1e-20)
            ll += w * np.log(prob)
            
        return -ll

    def fit(self, matches: pd.DataFrame, xi: float = 0.0):
        self.teams = list(set(matches['home_id'].unique()) | set(matches['away_id'].unique()))
        n_teams = len(self.teams)
        
        if 'date' in matches.columns:
            matches['time'] = (pd.to_datetime(matches['date']) - pd.Timestamp("1970-01-01")) // pd.Timedelta('1D')
        else:
            matches['time'] = 0
            
        current_time = matches['time'].max()
        
        init_params = np.concatenate([
            np.ones(n_teams) * 0.1, 
            np.ones(n_teams) * -0.1,
            [0.3],                  
            [0.0]                   
        ])
        
        bounds = [(None, None)] * (2 * n_teams) + [(None, None), (-1.0, 1.0)]
        
        def constraint(params):
            return np.sum(params[:n_teams]) - n_teams
            
        cons = [{'type': 'eq', 'fun': constraint}]
        
        res = minimize(
            self._log_likelihood, 
            init_params, 
            args=(matches, xi, current_time),
            method='SLSQP',
            bounds=bounds,
            constraints=cons
        )
        
        alpha = res.x[:n_teams]
        beta = res.x[n_teams:2*n_teams]
        self.attack_params = dict(zip(self.teams, alpha))
        self.defense_params = dict(zip(self.teams, beta))
        self.home_advantage = res.x[2*n_teams]
        self.rho = res.x[2*n_teams+1]
        
    def predict_score_matrix(self, home_id: int, away_id: int, max_goals: int = 10) -> np.ndarray:
        lam = self._lambda_h(home_id, away_id)
        mu = self._mu_a(home_id, away_id)
        
        mat = np.zeros((max_goals+1, max_goals+1))
        for i in range(max_goals+1):
            for j in range(max_goals+1):
                p_i = poisson.pmf(i, lam)
                p_j = poisson.pmf(j, mu)
                t = self._tau(i, j, lam, mu, self.rho)
                mat[i, j] = p_i * p_j * t
                
        mat = mat / mat.sum()
        return mat
        
    def predict_1x2(self, home_id: int, away_id: int) -> tuple[float, float, float]:
        mat = self.predict_score_matrix(home_id, away_id)
        prob_home = np.tril(mat, -1).sum()
        prob_draw = np.trace(mat)
        prob_away = np.triu(mat, 1).sum()
        return prob_home, prob_draw, prob_away
        
    def predict_over_under(self, home_id: int, away_id: int, line: float) -> tuple[float, float]:
        mat = self.predict_score_matrix(home_id, away_id)
        prob_over = 0.0
        prob_under = 0.0
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                if i + j > line:
                    prob_over += mat[i, j]
                else:
                    prob_under += mat[i, j]
        return prob_over, prob_under
        
    def predict_btts(self, home_id: int, away_id: int) -> tuple[float, float]:
        mat = self.predict_score_matrix(home_id, away_id)
        prob_btts = 0.0
        for i in range(1, mat.shape[0]):
            for j in range(1, mat.shape[1]):
                prob_btts += mat[i, j]
        return prob_btts, 1.0 - prob_btts
        
    def get_expected_goals(self, home_id: int, away_id: int) -> tuple[float, float]:
        lam = self._lambda_h(home_id, away_id)
        mu = self._mu_a(home_id, away_id)
        
        mat = self.predict_score_matrix(home_id, away_id)
        h_xg = sum(i * mat[i, j] for i in range(mat.shape[0]) for j in range(mat.shape[1]))
        a_xg = sum(j * mat[i, j] for i in range(mat.shape[0]) for j in range(mat.shape[1]))
        
        return h_xg, a_xg

    def serialize(self) -> dict:
        return {
            'attack_params': self.attack_params,
            'defense_params': self.defense_params,
            'home_advantage': self.home_advantage,
            'rho': self.rho,
            'teams': self.teams
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DixonColesModel':
        m = cls()
        m.attack_params = data.get('attack_params', {})
        m.defense_params = data.get('defense_params', {})
        m.home_advantage = data.get('home_advantage', 0.3)
        m.rho = data.get('rho', 0.0)
        m.teams = data.get('teams', [])
        return m
