# Phase 15 — Advanced Statistical Modeling & Assumption Removal

## Goal

Replace hand-authored football effect sizes in the production research path with parameters estimated from historical data and evaluated by chronological out-of-sample validation.

The phase is deliberately a research/model-selection phase. New models are challengers until they demonstrate out-of-sample improvement. No model is promoted because it produces more confident predictions, more candidate bets, or better results on a small selected sample.

## Evidence incorporated from the prior chat replay

The supplied 10-match scorecard produced an 8/10 primary-call hit rate, but that sample is selected and is not sufficient to establish model skill. Seven explicit match-win probabilities allowed a proper binary score check: Brier 0.1552 and log loss 0.4947.

The errors and tail observations were used only to identify research questions:
- Milan–Benfica: test whether point-in-time lineup/player information improves the goal-rate forecast.
- Liverpool–Tottenham: test whether a learned in-play hazard improves changing score-state/late-game forecasts.
- Dortmund–Villarreal, PSG–Slovan, Barcelona–Racing: test whether the score distribution is under-dispersed and whether Negative Binomial is supported by likelihood/BIC rather than a fixed dispersion multiplier.

This evidence does not justify manually changing any coefficient.

## Implemented model components

### 15.1 Dynamic Dixon-Coles

python/models/dynamic_dixon_coles.py

A score-driven dynamic Dixon-Coles challenger now estimates:
- baseline log goal rate;
- home advantage;
- Dixon-Coles rho;
- attack-state persistence;
- defence-state persistence;
- attack/defence score-driven gains.

Team attack/defence states evolve chronologically from observed score innovations. fit_as_of() enforces a strict pre-cutoff training boundary.

### 15.2 Distribution selection

GoalCountModel in python/models/count_models.py now fits Poisson and Negative Binomial with Var(Y) = mu + phi * mu^2 and selects the lower-BIC family.

The previous fixed variance-to-mean threshold has been removed.

### 15.3 Learned lineup effects

python/models/learned_lineup_effects.py

Player/XI effects are estimated through regularized Poisson regression on historical team-match observations.

The model exposes attack and opponent-defense log-rate contributions.

The system no longer applies a fixed missing-starter adjustment.

### 15.4 Learned live hazard

python/models/live_hazard.py

A discrete-time Poisson hazard challenger estimates lambda_minute = lambda_baseline * exp(X beta), where X can contain minute/time spline basis, score difference, red-card difference, shots-on-target difference, xG difference, substitution difference, knockout context, and home/away indicator.

Coefficients are estimated from historical minute-level data with L2 regularization.

### 15.5 Monte Carlo

python/simulation/vectorized_mc.py and python/simulation/monte_carlo.py

The Monte Carlo engine is now a probability-propagation layer. It no longer contains hard-coded goal multipliers for late minutes, score state, or red cards.

Those effects enter only through a fitted live-hazard model.

### 15.6 Form

python/models/form.py

The previous fixed 60/40 form blend and fixed composite coefficients were removed from the raw feature calculation.

LearnedFormModel provides a regularized Poisson mapping from point-in-time form channels to next-match goals. Feature coefficients must be learned.

### 15.7 Backtesting integrity

python/backtesting/walk_forward.py

The full backtest CLI no longer creates synthetic historical matches. A real CSV/Parquet dataset is now required for benchmark execution.

## Integration contract

AnalysisWorker now accepts a fitted ScoreDrivenDixonColes prematch model and a fitted LearnedLineupEffectModel.

It resolves goal rates from explicit point-in-time rates or a fitted dynamic model and fails closed rather than substituting hard-coded population rates.

Lineup effects are applied only after an 11-v-11 verified XI exists and only when a fitted player-effect model is available.

## Validation requirements

A model is research-valid only when:
1. Training data is strictly earlier than the evaluation observation.
2. Calibration is fit on a preceding temporal window.
3. Test observations remain untouched until scoring.
4. Probabilistic metrics are reported: log loss, Brier and RPS where applicable.
5. Calibration drift is reported.
6. Champion/challenger comparison uses paired out-of-sample predictions.
7. Model parameters and feature versions are persisted for reproducibility.
8. Selected or rejected models are not chosen from the 10-match chat sample.

## Exit criteria

- [x] Remove fixed score-state / late-game / red-card multipliers from MC.
- [x] Replace fixed goal-dispersion threshold with likelihood/BIC selection.
- [x] Implement dynamic Dixon-Coles challenger.
- [x] Implement learned lineup effects.
- [x] Implement learned live hazard challenger.
- [x] Remove synthetic full-backtest fallback.
- [x] Add unit/regression coverage for the new modeling contracts.
- [ ] Run a real historical walk-forward benchmark using the 13,403-match dataset with no synthetic observations.
- [ ] Compare dynamic DC, static DC and NB candidates out-of-sample.
- [ ] Fit calibration only on historical validation windows.
- [ ] Persist validated model artifacts and parameters to the model registry.
- [ ] Promote a challenger only after passing the existing statistical gate.

## Important non-goals

This phase does not:
- guarantee profitable betting;
- infer player effects from the 10-match chat sample;
- hard-code lineup penalties;
- hard-code late-game goal bumps;
- hard-code red-card percentages;
- treat market prices as truth;
- promote a challenger using in-sample ROI alone.