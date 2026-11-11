#!/usr/bin/env python3
"""Crash-dip buyer for the BTC 24h race (agent-fun/bars-replay/v1).

The idea, from the dev window's own bars: cbBTC's 1-minute noise is large
next to the moves a round trip must clear (about 26 bps in fees, slippage
and pool impact), so trend following whipsaws and ordinary mean reversion
buys into a falling knife. What does pay is the rare sharp drawdown: on
the dev window the price fell 2.5% below its 4-hour high exactly once,
at the morning crash, and the recovery that followed was worth about
+1.7%. This bot waits for that one event and rides it.

  - Entry (in cash): the latest close is at least 240 bps (2.4%) below
    the highest close of the last 240 bars (4 hours). Buy with all cash.
  - Exit (holding): sell everything when the position is worth 150 bps
    over its cost, when the close falls 200 bps below the highest close
    since the entry (trailing stop), or when it is worth 150 bps under
    its cost (stop loss).
  - After a stop-loss exit the bot stays out for 120 bars: a stopped-out
    dip is still below the high, so without this it re-buys into the
    same fall and stops out twice.

Parameters are tuned, not picked: an 864-config grid over drawdown,
lookback, profit, trailing stop and stop loss, plus crash-depth stress
tests (the same crash scaled 0.7x-1.3x, and flat/no-recovery variants).
240 bps sits on a plateau (240-245 identical, +14.31 USDC on the dev
window vs +11.05 at 220); a 150 bps stop survives the fill gap at the
crash bottom where a 100 bps stop fires early and bleeds twice; the
150 bps profit target beats holding to the end and beats 100-140.
Dev window: +14.31 USDC, 2 trades, fees 0.81, max drawdown 1.02%.
The second half of the window, with no crash, makes no trade at all.

All decisions are integer basis-point arithmetic on the closes, so the
same bars give the same orders in every execution. No clock, no
environment, no randomness: the only state is the closes seen and the
peak since the entry. Orders cap slippage at 100 bps past the close
they were decided on, so a fill into a gap is refused rather than
chased.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
# How far the close must sit below the rolling high to buy, in bps.
DRAWDOWN_BPS = 240
# Bars of history the high is taken over (240 one-minute bars = 4 hours).
LOOKBACK_BARS = 240
# Exit: profit target, trailing stop and stop loss, in bps.
PROFIT_BPS = 150
TRAIL_BPS = 200
STOP_BPS = 150
# Bars to stay out after a stop-loss exit: a stopped-out dip is still
# below the high, so without this the bot re-buys into the same fall
# and stops out twice (stress tests: -20 USDC instead of -11).
COOLDOWN_BARS = 120
# Slippage cap on every order, in bps past the close it was decided on.
MAX_SLIPPAGE_BPS = 100

closes = []
peak_since_entry = 0
cool_until_bar = -1


def on_batch(state, batch):
    """The orders decided on this batch's bar (a bar, its fills, account)."""
    global peak_since_entry, cool_until_bar
    bar = None
    for b in batch["bars"]:
        if b["symbol"] == SYMBOL:
            bar = b
            break
    if bar is None:
        return []
    close = int(bar["c"])
    closes.append(close)

    held = state.positions.get(SYMBOL)
    if held is not None:
        if close > peak_since_entry:
            peak_since_entry = close
        value = state.value(SYMBOL, held.qty)
        cost = held.cost
        pnl_bps = (value - cost) * 10000 // cost if cost > 0 else 0
        trail_bps = (peak_since_entry - close) * 10000 // peak_since_entry if peak_since_entry > 0 else 0
        if pnl_bps >= PROFIT_BPS or trail_bps >= TRAIL_BPS:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty, "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if pnl_bps <= -STOP_BPS:
            cool_until_bar = len(closes) + COOLDOWN_BARS
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty, "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    if len(closes) <= cool_until_bar:
        return []
    if len(closes) < LOOKBACK_BARS:
        return []
    high = max(closes[-LOOKBACK_BARS:])
    drawdown_bps = (high - close) * 10000 // high if high > 0 else 0
    if drawdown_bps < DRAWDOWN_BPS:
        return []
    peak_since_entry = close
    return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": state.cash, "max_slippage_bps": MAX_SLIPPAGE_BPS}]


makefun_bars.run(on_batch)
