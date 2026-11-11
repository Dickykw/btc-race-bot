# Crash-dip buyer — BTC 24h race bot

A Python 3.13 bot for the make.fun "Race a BTC trading bot live for 24
hours" competition (agent-fun/bars-replay/v1). It trades Coinbase Wrapped
BTC (cbBTC) against USDC, one minute at a time, long only, starting from
1,000 USDC of paper money.

## How it works

A round trip costs about 26 bps (4 bps fee, 2 bps slippage and pool
impact each way), which is large next to 1-minute noise. Trend following
whipsaws and ordinary mean reversion buys into a falling knife on the
dev window, so this bot does neither. It waits for the one event that
pays: a sharp drawdown, then rides the recovery.

- **Entry (in cash):** the latest close is at least 240 bps (2.4%)
  below the highest close of the last 240 bars (4 hours). Buy with all
  cash, slippage capped at 100 bps.
- **Exit (holding):** sell everything when the position is worth 150
  bps over its cost, when the close falls 200 bps below the highest
  close since the entry (trailing stop), or when it is worth 150 bps
  under its cost (stop loss).
- **Cooldown:** after a stop-loss exit the bot stays out for 120 bars.
  A stopped-out dip is still below the high, so without this it re-buys
  into the same fall and stops out twice (stress tests: -20 USDC
  instead of -11). After a profit or trailing-stop exit it may buy
  again on a later drawdown immediately.

All decisions are integer basis-point arithmetic on the closes, so the
same bars always give the same orders. No clock, no environment, no
randomness.

## Results on the dev window

The kit's frozen 24-hour dev window (1,440 one-minute bars, 10 Nov
08:01 UTC to 11 Nov 08:01 UTC, a downtrend of -1.07%):

| Metric | Value |
|---|---|
| Net PnL | **+14.31 USDC** |
| Trades | 2 (one round trip) |
| Fees | 0.81 USDC |
| Max drawdown | 1.02% |
| Buy | bar 516 at $72,769 (240 bps below the 4h high) |
| Sell | flattened at the last close |

Parameters were tuned on an 864-config grid plus crash-depth stress
tests (the same crash scaled 0.7x-1.3x, and flat/no-recovery variants):
240 bps sits on a plateau (240-245 identical), a 150 bps stop survives
the fill gap at the crash bottom where a 100 bps stop fires early, and
the 150 bps profit target beats holding to the end. The previous
version (220 bps entry, 150/100 exits) made +11.05 USDC on the same
window; the tuned version also has the best stress-test mean (+3.44
vs -0.34) and the smallest worst case (-11.45 vs -20.24).

For comparison, buy-and-hold on the same window loses 13.44 USDC and
the bundled EMA-cross baseline loses 89.29 USDC.

## Layout

- `main.py` — the entrypoint the grader runs (`python3 -P -s main.py`).
- `vendor/makefun_bars.py` — the kit's protocol shim, copied unchanged
  from the competition kit (byte-identical).

Only the Python standard library is used. No install step, no network.
