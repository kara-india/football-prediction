# RL Contextual Bandit Architecture

## Architecture Overview
The reinforcement learning layer acts as an override mechanism. It does not replace the core probability models; instead, it learns *when to bet* (or more accurately, when *not* to bet) based on contextual signals.

## State Space Description
The RL state representation combines match state, market state, model outputs, quality signals, and context to provide a comprehensive vector for the contextual bandit.

## Action Space
`V1_ACTIONS` consist of `ABSTAIN` and `BET`. Future versions may include actions like `BET_GOALS`, `BET_RESULT`, etc.

## Reward Function
The base reward is the realized return of paper bets. Penalties are added for:
- Overconfidence (model predicted high probability but outcome was 0)
- Stale data
- Drawdown contribution
- Poor calibration

## Why Contextual Bandit for V1
Contextual bandits are sample efficient and do not require the massive amounts of data that Deep RL requires. They balance exploration and exploitation efficiently.

## Guardrails
- RL cannot force a bet, it can only `ABSTAIN` when the underlying model recommends a bet.
- Minimum observations (default 500) are required before RL begins affecting decisions.

## How to Enable RL
Set `engine_settings.rl_enabled = True`.

## When to Consider Deep RL
When there is sufficient historical data across multiple distinct environments to generalize well.

## Safety Constraints
The RL state is clamped strictly to the range `[-1, 1]` or `[0, 1]` for numerical stability. 
