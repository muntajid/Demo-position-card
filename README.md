# Demo Position Card

Recreates the Binance Futures position card design exact same as reference image.

## Reference Design
Based on Binance Futures screenshot with:
- Black background with dark gray geometric watermark
- Top: avatar, username, timestamp
- Symbol: `IOSTUSDT Perpetual`
- Position: `Long | 50x` (green/red)
- PNL: `+0.02 USDT` large
- Entry Price / Average Close Price two columns
- Footer: Binance Futures logo, Referral Code, QR code
- Extended support: Take Profit, Stop Loss, Risk/Reward, Confidence

## Usage

### 1. Edit demo data
Open `data/demo_position.json`:

```json
{
  "symbol": "IOSTUSDT",
  "position": "Long",
  "entry_price": "0.00179122",
  "take_profit": "0.0019",
  "stop_loss": "0.00175",
  "leverage": "50x",
  "risk_reward": "1:2.5",
  "confidence": "85%",
  "pnl": "+0.02",
  "pnl_currency": "USDT",
  "average_close_price": "0.0018",
  "username": "muntajid",
  "timestamp": "2026-09-13 22:07:15",
  "referral_code": "768056928"
}
```

Required fields:
- `symbol` - cannot be empty
- `position` - LONG or SHORT
- `entry_price` - valid number >0
- `leverage` - like `5x`, `50x`

Optional:
- `take_profit`, `stop_loss`, `average_close_price`
- `risk_reward` like `1:2`
- `confidence` like `85%`
- `pnl`, `pnl_currency`
- `username`, `timestamp`, `referral_code`

### 2. Generate locally
```bash
pip install -r requirements.txt
python src/generate_card.py
# Output: output/demo_position_card.png
```

### 3. Generate via GitHub Actions
1. Commit/push your changes to `data/demo_position.json`
2. Go to GitHub → Actions → Demo Position Card → Run workflow
3. Download artifact `demo-position-card` containing `demo_position_card.png`

Output is a real PNG 1080x1920, sharp text, mobile readable, tested with:
- BTC/USDT
- ETH/USDT
- 1000PEPE/USDT (long symbols)

## Validation
Before generation, JSON is validated. If invalid, Actions fails with clear error:
- `symbol cannot be empty`
- `position should be LONG or SHORT`
- `entry_price must be a valid number`
- `leverage should be valid like '5x'`
