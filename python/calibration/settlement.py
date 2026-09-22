class SettlementCalculator:
    def settle_1x2(self, home_goals: int, away_goals: int, selection: str) -> str:
        if home_goals > away_goals:
            result = '1'
        elif home_goals == away_goals:
            result = 'X'
        else:
            result = '2'
        return 'win' if selection == result else 'loss'
    
    def settle_over_under(self, total_goals: int, line: float, selection: str) -> str:
        if total_goals == line:
            return 'void'
        if selection == 'over':
            return 'win' if total_goals > line else 'loss'
        elif selection == 'under':
            return 'win' if total_goals < line else 'loss'
        return 'void'
    
    def settle_btts(self, home_goals: int, away_goals: int, selection: str) -> str:
        btts = home_goals > 0 and away_goals > 0
        if selection == 'yes':
            return 'win' if btts else 'loss'
        elif selection == 'no':
            return 'win' if not btts else 'loss'
        return 'void'
    
    def settle_double_chance(self, home_goals: int, away_goals: int, selection: str) -> str:
        if home_goals > away_goals:
            result = '1'
        elif home_goals == away_goals:
            result = 'X'
        else:
            result = '2'
            
        if selection == '1X':
            return 'win' if result in ['1', 'X'] else 'loss'
        elif selection == '12':
            return 'win' if result in ['1', '2'] else 'loss'
        elif selection == 'X2':
            return 'win' if result in ['X', '2'] else 'loss'
        return 'void'
    
    def settle_anytime_goalscorer(self, scorer_ids: list[int], player_id: int) -> str:
        return 'win' if player_id in scorer_ids else 'loss'
    
    def settle_player_assist(self, assist_ids: list[int], player_id: int) -> str:
        return 'win' if player_id in assist_ids else 'loss'
    
    def settle_total_cards(self, total_cards: int, line: float, selection: str) -> str:
        if total_cards == line:
            return 'void'
        if selection == 'over':
            return 'win' if total_cards > line else 'loss'
        elif selection == 'under':
            return 'win' if total_cards < line else 'loss'
        return 'void'
    
    def settle_next_goal(self, next_scoring_team_id: int, 
                          home_id: int, away_id: int, selection: str) -> str:
        if next_scoring_team_id == home_id:
            result = '1'
        elif next_scoring_team_id == away_id:
            result = '2'
        else:
            result = 'no_goal'
        return 'win' if selection == result else 'loss'
    
    def calculate_paper_pl(self, outcome: str, decimal_odds: float, 
                            stake_units: float) -> float:
        if outcome == 'win':
            return (decimal_odds - 1.0) * stake_units
        elif outcome == 'loss':
            return -stake_units
        return 0.0
