# btc-race-24h entry: a snap-back rider for cbBTC/USDC, minute by minute.
#
# What the tape taught (measured on the kit's dev window, a -4% grinding day, and checked against
# conditional forward returns over every minute of it): sharp drops snap back, trends do not
# follow through. After a 30-minute fall of 0.6% or more, the next two hours averaged +0.77% and
# beat the ~26 bps round-trip cost half the time; after strong up-moves, trend crosses and every
# other state I measured, forward returns averaged negative. EMA-cross and momentum variants of
# every size lost money on the window; dip-buying without a stop bled into the down-legs.
#
# So the bot does exactly one thing:
#   - flat, and the last 30 minutes fell at least 0.9%: buy with 60% of the cash at the next open;
#   - holding: sell everything after 240 minutes, or at once if the position is 3% under water
#     (the snap-back has had its four hours by then; what is left is the trend, and the trend on
#     this tape is not a friend);
#   - after a sale, rest 45 minutes so one cascade cannot re-trigger the bot bar after bar.
# No take-profit: the winners in the grid were the runs that let the full four hours play out.
# The parameters sit in the middle of the profitable region of the grid (drop 0.75-1.1%, hold
# exactly 240, size 0.5-0.75 all cleared the dev gate), not on its sharpest peak.
#
# Deterministic: a pure function of the bars seen. No clock, no environment, no randomness.
# Runs as `python3 -P -s /bot/main.py`; the vendored shim speaks agent-fun/bars-replay/v1.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

DROP = 0.009        # 30-minute fall that counts as a snap-back setup
SIZE = 0.6          # share of cash a buy spends
HOLD_MINUTES = 240  # time exit: the snap-back's horizon
STOP = 0.03         # disaster exit under the entry price
COOLDOWN = 45       # flat minutes to rest after a sale
MAX_SLIPPAGE_BPS = 500

closes = []         # every close seen, raw price units, in order
bars_held = 0       # batches answered while holding the position
entry_price = None  # raw price the position cost, fees included, once it appears
cooldown = 0


def on_batch(state, batch):
    global bars_held, entry_price, cooldown
    symbol = next(iter(state.symbols))
    bar = state.latest.get(symbol)
    if bar is None:
        return []
    close = int(bar["c"])
    closes.append(close)
    if state.warming_up:
        return []

    holding = state.positions.get(symbol)
    if holding is not None:
        if entry_price is None:
            # Invert the shim's value(): price = cost * 10^(qty+price scales) / (qty * 10^quote scale).
            s = state.symbols[symbol]
            entry_price = holding.cost * 10 ** (s["qty_scale"] + s["price_scale"]) // (
                holding.qty * 10 ** state.hello["capital"]["quote_scale"])
            bars_held = 0
        bars_held += 1
        if bars_held >= HOLD_MINUTES or close <= entry_price * (1 - STOP):
            cooldown = COOLDOWN
            return [{"side": "sell", "symbol": symbol, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    entry_price = None
    bars_held = 0
    if cooldown > 0:
        cooldown -= 1
        return []
    if len(closes) > 30:
        r30 = closes[-1] / closes[-31] - 1
        if r30 <= -DROP:
            notional = int(state.cash * SIZE)
            if notional >= 1_000_000:  # the 1 USDC minimum order
                return [{"side": "buy", "symbol": symbol, "notional_quote_units": notional,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
