# Phase 0 — Mathematical Rebaseline

Status: DESIGN LOCK  
Base commit: 1882f3f71a69a2abcd68950b61ed1b5334a458d5  
Purpose: define the statistical architecture before Phase 1–10 implementation changes.

## 1. Objective

The system is a probabilistic football forecasting and market-mispricing research engine. It must estimate calibrated outcome distributions and quantify uncertainty before comparing those distributions with bookmaker prices.

A positive expected value estimate is not sufficient by itself to create a BET decision. All decisions remain fail-closed when required evidence is missing.

## 2. Core model

Primary prematch model: dynamic hierarchical Dixon-Coles.

For fixture i with home team h and away team a:

log(lambda_h) = mu + home_advantage + attack[h,t] - defense[a,t] + X_h,t * beta
log(lambda_a) = mu + attack[a,t] - defense[h,t] + X_a,t * beta

Team attack and defence strengths are time-varying latent states. Their evolution must be learned from historical data rather than represented by fixed manual adjustments.

The low-score Dixon-Coles dependence correction remains part of the joint score distribution.

## 3. Model uncertainty

Inference must preserve parameter uncertainty rather than reducing the model to a single point estimate.

Target representation:

p(y_new | D) = integral p(y_new | theta) p(theta | D) dtheta

Implementation may use an appropriate Bayesian/state-space approximation if full MCMC is operationally excessive. The approximation must be evaluated against out-of-sample probabilistic scoring.

Outputs should support predictive intervals/credible intervals where statistically justified.

## 4. Alternative models

Dixon-Coles is the primary candidate, not an unquestionable winner.

The evaluation framework should support:

- dynamic Dixon-Coles
- bivariate Poisson
- negative-binomial/count overdispersion variants where justified by diagnostics
- time-to-event/hazard formulations for in-play modelling

Model selection must be based on strict chronological walk-forward validation, not in-sample fit.

Primary comparison metrics:

- Log loss
- Brier score
- Ranked Probability Score (RPS)
- calibration error / reliability
- market-specific performance
- stability across seasons/competitions

ROI is a secondary decision metric and must not be the sole model-selection criterion.

## 5. Player and lineup information

Starter effects must not use arbitrary rules such as "missing starter = -4%".

Lineup information should enter through learned player/team contribution features.

The T-60 system should produce a versioned feature snapshot containing the selected XI and the model-derived contribution of those players.

No lineup effect may be introduced unless its coefficient/effect is estimated from historical data or is explicitly identified as an unvalidated research feature.

## 6. Market probability

Bookmaker prices are treated as an information source and benchmark, not as ground truth.

Raw bookmaker odds must be converted to implied probabilities and de-vigged.

The initial de-vigging implementations are:

- Shin for 1X2
- multiplicative normalization for two-way markets

Alternative de-vigging methods should remain testable.

The target bookmaker price must not be used as an input to an independent model in a way that creates leakage when the objective is to measure model-vs-market edge.

## 7. Model/market combination

Do not assign hand-written weights such as 30% model / 70% market.

The combination must be learned from chronological validation data.

Preferred research formulation:

logit(P_final) = logit(P_market) + delta(X)

where delta(X) is a learned residual correction based only on information available before the prediction timestamp.

Alternative learned stacking/blending models may be evaluated through walk-forward validation.

The system must retain the independent model probability separately from the market-informed probability.

## 8. Posterior predictive simulation

Monte Carlo is a downstream uncertainty-propagation mechanism, not the source of model intelligence.

Target pipeline:

historical data
-> fitted latent strengths / posterior
-> posterior predictive goal intensities
-> score distribution
-> Monte Carlo samples
-> market probabilities

The simulation must persist:

- simulation count
- random seed where deterministic replay is required
- model version
- feature snapshot/version
- calibration version
- prediction timestamp

## 9. In-play model

Do not retain fixed hand-coded rules such as universal late-game +25% goal hazard, fixed red-card multipliers, or fixed score-state multipliers as production truth.

The production target is a time-varying goal-arrival hazard:

lambda_team(t) = exp(eta_team(t))

with eta estimated from historical in-play observations and available state variables such as:

- minute / time remaining
- score difference
- red cards
- shots / shots on target
- xG rate where available
- substitutions
- other validated live-state features

The survival formulation should derive interval goal probabilities from the estimated hazard.

## 10. Calibration

Calibration is a first-class model component.

Required checks:

- reliability curves
- calibration slope/intercept
- Brier score
- log loss
- calibration error
- calibration drift over time

Calibration must be fitted only on data that would have been available at the relevant historical prediction time.

No synthetic calibration bootstrap is permitted.

## 11. Betting decision mathematics

For decimal odds o and calibrated probability p:

EV = p * o - 1

Break-even probability:

p_break_even = 1 / o

However, the decision engine must also account for predictive uncertainty.

Research target:

P(EV > 0) = P(p > 1/o)

and, where appropriate, a conservative lower-bound EV:

EV_lower = p_lower * o - 1

The exact production threshold must be learned/validated rather than chosen solely because it improves historical ROI on the same sample used for development.

## 12. No-BET gates

A BET is prohibited when any critical evidence prerequisite is unavailable or invalid.

Examples:

- odds unavailable
- model uncalibrated
- insufficient historical support
- lineup required but unconfirmed
- market suspended/stale
- prediction interval too wide for the configured decision rule
- model/data integrity failure

NO_BET reason codes must be deterministic, persisted, and auditable.

## 13. Backtesting rules

All model development and comparison must use chronological splits.

No future information may enter:

- team ratings
- player ratings
- calibration
- market features
- feature normalization
- model selection
- threshold selection

Any transformation with fitted parameters must be fitted only on the historical training window and applied forward.

The system must distinguish:

TRAIN -> VALIDATION -> TEST

and ultimately perform a genuine walk-forward evaluation.

## 14. Data leakage controls

The following are mandatory:

- prediction timestamp is authoritative
- lineup data cannot enter a prediction made before lineup publication
- closing odds cannot be used for an earlier prediction
- final match result cannot influence pre-match features
- post-match player/team ratings cannot leak backward
- calibration cannot be fitted on future observations
- threshold selection cannot use the final test set

## 15. Research policy

Complexity must be earned by out-of-sample evidence.

The project will prefer the simplest model that demonstrates stable improvement across chronological validation.

A more complex model must not be promoted merely because:

- it produces higher in-sample likelihood
- it produces more confident predictions
- it generates more BET signals
- it produces higher ROI on a small sample

## 16. Phase 0 exit criteria

Phase 0 is complete when this specification is accepted as the mathematical target architecture.

Phase 1 remains a product/data-integrity phase.

The first mathematical implementation work belongs in Phase 5, after the fixture/persistence/CI foundations are repaired.

No production model code is changed by Phase 0 solely for the purpose of claiming mathematical improvement.
