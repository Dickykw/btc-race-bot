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

- **Entry (in cash):** the latest close is at least 220 bps (2.2%)
  below the highest close of the last 240 bars (4 hours). Buy with all
  cash, slippage capped at 100 bps.
- **Exit (holding):** sell everything when the position is worth 150
  bps over its cost, when the close falls 150 bps below the highest
  close since the entry (trailing stop), or when it is worth 100 bps
  under its cost (stop loss).
- After a sale it may buy again on a later drawdown.

All decisions are integer basis-point arithmetic on the closes, so the
same bars always give the same orders. No clock, no environment, no
randomness.

## Results on the dev window

The kit's frozen 24-hour dev window (1,440 one-minute bars, 10 Nov
08:01 UTC to 11 Nov 08:01 UTC, a downtrend of -1.07%):

| Metric | Value |
|---|---|
| Net PnL | **+11.05 USDC** |
| Trades | 2 (one round trip) |
| Fees | 0.80 USDC |
| Max drawdown | 1.02% |
| Buy | bar 463 at $72,903 (231 bps below the 4h high) |
| Sell | flattened at the last close |

For comparison, buy-and-hold on the same window loses 13.44 USDC and
the bundled EMA-cross baseline loses 89.29 USDC.

## Layout

- `main.py` — the entrypoint the grader runs (`python3 -P -s main.py`).
- `vendor/makefun_bars.py` — the kit's protocol shim, copied unchanged
  from the competition kit (byte-identical).

Only the Python standard library is used. No install step, no network.
