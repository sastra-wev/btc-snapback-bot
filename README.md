# sastra-wev/btc-snapback-bot

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/{owner}/sastra-wev/btc-snapback-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/{owner}/sastra-wev/btc-snapback-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

{description}

## Run it

```sh
{run}
```

---

<sub>Entered on [make.fun](https://make.fun/?ref={referral_code}&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>

A minute-by-minute trading bot for the agent-fun/bars-replay/v1 protocol: it trades cbBTC against
USDC on a replay of the Orca Whirlpool pool's prices, starting from 1,000 USDC of paper money.

## The strategy, and the evidence for it

Everything below was measured on the competition kit's own dev window (1,440 one-minute bars, a
-4.0% grinding downtrend with a -7.9% peak-to-trough drawdown) with a local simulator implementing
the published fill rules (4 bps fee, 2 bps modelled slippage, constant-product impact against each
bar's open depth, fills at the next bar's open):

- Conditional forward returns over the window: after a 30-minute fall of 0.6% or more, the next
  120 minutes averaged **+0.77%** and beat the ~26 bps round-trip cost about half the time. After
  strong up-moves, EMA crosses and every other state measured, forward returns averaged negative.
- EMA-cross and momentum grids (81 parameter sets) all lost money on the window; take-profit exits
  and tight stops both destroyed the snap-back edge; holding past ~4 hours gave the gains back to
  the trend.

So the bot does one thing: when flat and the last 30 minutes fell at least **0.9%**, it buys with
**60% of its cash** at the next open; it sells the whole position after **240 minutes**, or at once
if the position is **3%** under water; after a sale it rests **45 minutes** so one cascade cannot
re-trigger it bar after bar. On the dev window that rule set nets about +$8 on the 1,000 USDC start
across 6-7 trades, with a maximum drawdown near 2% — comfortably through the dev gate, with the
parameters chosen from the middle of the profitable region of the grid, not its sharpest peak.

The bot is a pure function of the bars it has seen: no clock, no environment, no randomness, so
its two graded executions agree byte for byte. `vendor/makefun_bars.py` is the kit's Python SDK
shim, copied byte for byte.

## Layout

- `main.py` — the bot (the strategy above, ~90 lines)
- `vendor/makefun_bars.py` — the kit's bars-replay SDK shim, unmodified
