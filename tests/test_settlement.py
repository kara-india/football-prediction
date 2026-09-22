from python.calibration.settlement import SettlementCalculator

def test_settle_1x2():
    calc = SettlementCalculator()
    assert calc.settle_1x2(2, 1, '1') == 'win'
    assert calc.settle_1x2(2, 1, 'X') == 'loss'
    assert calc.settle_1x2(2, 1, '2') == 'loss'
    
    assert calc.settle_1x2(1, 1, 'X') == 'win'
    assert calc.settle_1x2(1, 1, '1') == 'loss'
    
    assert calc.settle_1x2(0, 2, '2') == 'win'

def test_settle_over_under():
    calc = SettlementCalculator()
    # .5 line
    assert calc.settle_over_under(3, 2.5, 'over') == 'win'
    assert calc.settle_over_under(2, 2.5, 'over') == 'loss'
    assert calc.settle_over_under(2, 2.5, 'under') == 'win'
    
    # whole number line
    assert calc.settle_over_under(2, 2.0, 'over') == 'void'
    assert calc.settle_over_under(2, 2.0, 'under') == 'void'
    assert calc.settle_over_under(3, 2.0, 'over') == 'win'

def test_settle_btts():
    calc = SettlementCalculator()
    assert calc.settle_btts(1, 1, 'yes') == 'win'
    assert calc.settle_btts(2, 0, 'yes') == 'loss'
    assert calc.settle_btts(2, 0, 'no') == 'win'
    assert calc.settle_btts(0, 0, 'no') == 'win'

def test_calculate_paper_pl():
    calc = SettlementCalculator()
    assert calc.calculate_paper_pl('win', 2.5, 10.0) == 15.0
    assert calc.calculate_paper_pl('loss', 2.5, 10.0) == -10.0
    assert calc.calculate_paper_pl('void', 2.5, 10.0) == 0.0
