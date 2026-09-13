#!/usr/bin/env python3
"""
Binance Futures Position Card Generator
Recreates the reference image exact same.

Reference image analysis:
- Size: portrait 1080x1920 black background
- Top: avatar 80px, username white bold, timestamp gray
- Watermark top-right: large dark gray geometric diamonds/chevron
- Symbol: "IOSTUSDT Perpetual" white bold ~38px
- Position: "Long | 50x" green + gray separator
- PNL: "+0.02 USDT" large green + white
- Two columns: Entry Price / Average Close Price
- Footer: Binance Futures logo, Referral Code, QR code
- Also supports TP/SL, Risk/Reward, Confidence in same visual style
"""

import json
import os
import re
import sys
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
MARGIN = 48
DATA_PATH = Path(__file__).parent.parent / "data" / "demo_position.json"
OUTPUT_PATH = Path(__file__).parent.parent / "output" / "demo_position_card.png"

COLORS = {
    "bg": (0, 0, 0),
    "watermark_dark": (22, 22, 22),
    "watermark_mid": (38, 38, 38),
    "watermark_light": (55, 55, 55),
    "white": (255, 255, 255),
    "gray_label": (128, 128, 128),
    "gray_light": (145, 145, 145),
    "gray_sep": (90, 90, 90),
    "green": (46, 189, 133),  # Reference green
    "red": (246, 70, 93),
    "yellow": (243, 186, 47),
    "border": (38, 38, 38),
}

def find_font(bold=False, size=32):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def get_font(size, bold=False):
    return find_font(bold=bold, size=size)

def validate_data(data):
    errors = []
    required = ["symbol", "position", "entry_price", "leverage"]
    for f in required:
        if f not in data:
            errors.append(f"Missing required field: '{f}'")
    if errors:
        raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

    symbol = str(data.get("symbol", "")).strip()
    if not symbol:
        errors.append("symbol cannot be empty")

    pos = str(data.get("position", "")).strip().upper()
    if pos not in ("LONG", "SHORT"):
        errors.append(f"position should be LONG or SHORT, got '{data.get('position')}'")

    def check_price(field):
        if field in data and data[field] is not None and str(data[field]).strip() != "":
            val = data[field]
            try:
                s = str(val).replace(",", "").replace("$", "").strip()
                num = float(s)
                if num <= 0:
                    errors.append(f"{field} must be > 0, got {data[field]}")
            except:
                errors.append(f"{field} must be a valid number, got '{data[field]}'")

    check_price("entry_price")
    check_price("take_profit")
    check_price("stop_loss")
    check_price("average_close_price")

    lev = str(data.get("leverage", "")).strip()
    if lev and not re.match(r"^\d+(\.\d+)?\s*x$", lev, re.IGNORECASE):
        errors.append(f"leverage should be valid like '5x' or '50x', got '{lev}'")

    if "risk_reward" in data and data["risk_reward"]:
        rr = str(data["risk_reward"]).strip()
        if ":" not in rr:
            errors.append(f"risk_reward should be like '1:2', got '{rr}'")

    if "confidence" in data and data["confidence"]:
        conf = str(data["confidence"]).strip()
        m = re.match(r"^(\d+(\.\d+)?)\s*%?$", conf)
        if not m:
            errors.append(f"confidence should be like '85%' or '85', got '{conf}'")
        else:
            try:
                v = float(m.group(1))
                if not (0 <= v <= 100):
                    errors.append(f"confidence must be between 0 and 100, got '{conf}'")
            except:
                errors.append(f"confidence invalid: '{conf}'")

    if errors:
        raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

def format_price(value):
    if value is None or str(value).strip() == "":
        return ""
    try:
        s = str(value).strip()
        num = float(s.replace(",", "").replace("$", ""))
        if abs(num) < 1:
            # Preserve original if very precise like 0.00179122
            if "." in s and len(s.split(".")[-1]) >= 5:
                # Keep original up to 8 decimals
                return s
            formatted = f"{num:.8f}".rstrip("0").rstrip(".")
            return formatted
        elif abs(num) < 1000:
            if num == int(num):
                return f"{int(num)}"
            return f"{num:.4f}".rstrip("0").rstrip(".")
        else:
            if num == int(num):
                return f"{int(num):,}"
            return f"{num:,.2f}".rstrip("0").rstrip(".")
    except:
        return str(value)

def draw_watermark(draw, W, H):
    """Draw exact watermark as reference: large dark chevron/diamond pattern top-right"""
    def diamond(cx, cy, size):
        return [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]

    # Main large shape - as in reference: looks like a big arrow/chevron made of thick border
    # Center at right side, upper third
    cx, cy = int(W * 0.72), int(H * 0.24)

    # Outer biggest diamond - dark gray
    draw.polygon(diamond(cx, cy, 560), fill=(28, 28, 28))

    # Inner cutout black to create thick border
    draw.polygon(diamond(cx, cy, 440), fill=COLORS["bg"])

    # Middle diamond border
    draw.polygon(diamond(cx, cy, 380), fill=(45, 45, 45))

    # Inner cutout black
    draw.polygon(diamond(cx, cy, 260), fill=COLORS["bg"])

    # Small solid diamond inside as in reference (middle right)
    # Reference shows small diamond at center right of chevron
    small_cx, small_cy = cx + 110, cy - 30
    draw.polygon(diamond(small_cx, small_cy, 85), fill=(62, 62, 62))

    # Top right corner partial diamond (as in reference screenshot top edge)
    cx2, cy2 = int(W * 0.88), int(H * 0.02)
    draw.polygon(diamond(cx2, cy2, 300), fill=(38, 38, 38))

def draw_avatar(draw, x, y, size=72):
    # Outer dark circle
    draw.ellipse([x, y, x+size, y+size], fill=(45, 45, 45))
    # Yellow face
    face = int(size * 0.68)
    fx = x + (size - face)//2
    fy = y + (size - face)//2 + 4
    draw.ellipse([fx, fy, fx+face, fy+face], fill=(210, 165, 30))
    # Cap
    cap_h = int(face * 0.38)
    draw.ellipse([fx-1, fy-2, fx+face+1, fy+cap_h], fill=(25, 35, 60))
    # Brim
    draw.ellipse([fx-4, fy+cap_h-6, fx+face+4, fy+cap_h+6], fill=(25, 35, 60))
    # Binance logo on cap small yellow diamond
    dcx, dcy = fx + face//2, fy + cap_h//2
    ds = 5
    draw.polygon([(dcx, dcy-ds), (dcx+ds, dcy), (dcx, dcy+ds), (dcx-ds, dcy)], fill=COLORS["yellow"])

def draw_binance_logo(draw, x, y):
    def dpts(cx, cy, s):
        return [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
    cx, cy = x + 14, y + 14
    draw.polygon(dpts(cx, cy, 11), fill=COLORS["yellow"])
    draw.polygon(dpts(cx, cy, 4), fill=(0,0,0))
    font_b = get_font(22, bold=True)
    font_f = get_font(30, bold=True)
    draw.text((x+32, y+1), "BINANCE", fill=COLORS["yellow"], font=font_b)
    draw.text((x+32, y+26), "FUTURES", fill=COLORS["white"], font=font_f)

def generate_qr(size=170):
    modules = 29
    cell = size // modules
    actual = cell * modules
    img = Image.new("RGB", (actual, actual), "white")
    d = ImageDraw.Draw(img)

    def finder(x, y):
        for i in range(7):
            for j in range(7):
                if i in (0,6) or j in (0,6) or (2 <= i <= 4 and 2 <= j <= 4):
                    d.rectangle([ (x+j)*cell, (y+i)*cell, (x+j+1)*cell-1, (y+i+1)*cell-1 ], fill="black")

    finder(0,0)
    finder(modules-7,0)
    finder(0,modules-7)

    random.seed(768056928)
    for i in range(modules):
        for j in range(modules):
            if (i < 9 and j < 9) or (i < 9 and j >= modules-8) or (i >= modules-8 and j < 9):
                continue
            if i == 6 or j == 6:
                if (i+j) % 2 == 0:
                    d.rectangle([j*cell, i*cell, (j+1)*cell-1, (i+1)*cell-1], fill="black")
                continue
            if random.random() > 0.52:
                d.rectangle([j*cell, i*cell, (j+1)*cell-1, (i+1)*cell-1], fill="black")

    # Add quiet zone and rounded corners
    bordered = Image.new("RGB", (actual+16, actual+16), "white")
    bordered.paste(img, (8,8))
    # Resize to target
    final_size = size + 16
    # Create rounded
    out = bordered.resize((final_size, final_size), Image.NEAREST)
    # Rounded mask
    mask = Image.new("L", (final_size, final_size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0,0,final_size-1,final_size-1], radius=12, fill=255)
    out.putalpha(mask)
    white_bg = Image.new("RGB", (final_size, final_size), "white")
    white_bg.paste(out, mask=out.split()[-1])
    return white_bg

def main():
    if not DATA_PATH.exists():
        print(f"ERROR: Data file not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {DATA_PATH}: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        validate_data(data)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    symbol_raw = str(data.get("symbol", "")).strip()
    symbol_display = symbol_raw.replace("/", "").upper()
    suffix = data.get("symbol_suffix", "Perpetual")
    if "PERP" not in symbol_display.upper() and suffix:
        full_symbol = f"{symbol_display} {suffix}"
    else:
        full_symbol = symbol_display

    position_raw = str(data.get("position", "")).strip()
    position_display = position_raw.capitalize()
    is_long = position_raw.upper() == "LONG"
    leverage = str(data.get("leverage", "")).strip()

    entry_price = format_price(data.get("entry_price"))
    tp = format_price(data.get("take_profit")) if data.get("take_profit") is not None else ""
    sl = format_price(data.get("stop_loss")) if data.get("stop_loss") is not None else ""
    avg_close = format_price(data.get("average_close_price")) if data.get("average_close_price") is not None else ""

    pnl = str(data.get("pnl", "")).strip()
    if not pnl:
        try:
            if tp and data.get("take_profit") is not None and data.get("entry_price") is not None:
                e = float(str(data.get("entry_price")).replace(",", ""))
                t = float(str(data.get("take_profit")).replace(",", ""))
                diff = t - e if is_long else e - t
                pnl = f"{diff:+.4f}" if abs(diff) < 1 else f"{diff:+.2f}"
            else:
                pnl = "+0.00"
        except:
            pnl = "+0.00"

    pnl_currency = str(data.get("pnl_currency", "USDT")).strip() or "USDT"
    risk_reward = str(data.get("risk_reward", "")).strip()
    confidence = str(data.get("confidence", "")).strip()
    username = str(data.get("username", "muntajid")).strip() or "muntajid"
    timestamp = str(data.get("timestamp", "")).strip()
    if not timestamp:
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    referral_code = str(data.get("referral_code", "768056928")).strip() or "768056928"

    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    draw_watermark(draw, W, H)

    # Top user
    avatar_size = 72
    avatar_x, avatar_y = MARGIN, MARGIN
    draw_avatar(draw, avatar_x, avatar_y, avatar_size)

    font_user = get_font(30, bold=True)
    font_time = get_font(20, bold=False)
    draw.text((avatar_x + avatar_size + 18, avatar_y + 4), username, fill=COLORS["white"], font=font_user)
    draw.text((avatar_x + avatar_size + 18, avatar_y + 38), timestamp, fill=COLORS["gray_light"], font=font_time)

    # Symbol - lower to match reference spacing (reference has large gap after header)
    symbol_font_size = 42
    if len(full_symbol) > 22:
        symbol_font_size = 32
    elif len(full_symbol) > 18:
        symbol_font_size = 36
    font_symbol = get_font(symbol_font_size, bold=True)
    symbol_y = 520  # Reference shows symbol about 1/3 down
    draw.text((MARGIN, symbol_y), full_symbol, fill=COLORS["white"], font=font_symbol)

    # Position | Leverage
    pos_y = symbol_y + symbol_font_size + 18
    font_pos = get_font(24, bold=False)
    pos_color = COLORS["green"] if is_long else COLORS["red"]
    pos_text = position_display
    sep_text = "  |  "
    lev_text = leverage

    try:
        w_pos = draw.textbbox((0,0), pos_text, font=font_pos)[2]
        w_sep = draw.textbbox((0,0), sep_text, font=font_pos)[2]
    except:
        w_pos = len(pos_text)*14
        w_sep = 24

    x_cur = MARGIN
    draw.text((x_cur, pos_y), pos_text, fill=pos_color, font=font_pos)
    x_cur += w_pos
    draw.text((x_cur, pos_y), sep_text, fill=COLORS["gray_sep"], font=font_pos)
    x_cur += w_sep
    draw.text((x_cur, pos_y), lev_text, fill=COLORS["gray_light"], font=font_pos)

    # PNL - big
    pnl_y = pos_y + 70
    font_pnl_big = get_font(84, bold=True)
    font_pnl_curr = get_font(38, bold=True)

    try:
        w_pnl = draw.textbbox((0,0), pnl, font=font_pnl_big)[2]
    except:
        w_pnl = len(pnl)*45

    pnl_color = COLORS["green"] if not pnl.startswith("-") else COLORS["red"]
    draw.text((MARGIN, pnl_y), pnl, fill=pnl_color, font=font_pnl_big)
    draw.text((MARGIN + w_pnl + 18, pnl_y + 28), pnl_currency, fill=COLORS["white"], font=font_pnl_curr)

    # Prices - start around 60% height as reference
    price_y = pnl_y + 180
    font_label = get_font(22, bold=False)
    font_val = get_font(28, bold=True)

    def two_col(y, l1, v1, l2, v2, c1=None, c2=None):
        c1 = c1 or COLORS["white"]
        c2 = c2 or COLORS["white"]
        col_w = (W - MARGIN*2)//2
        draw.text((MARGIN, y), l1, fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+32), v1, fill=c1, font=font_val)
        rx = MARGIN + col_w + 16
        draw.text((rx, y), l2, fill=COLORS["gray_label"], font=font_label)
        draw.text((rx, y+32), v2, fill=c2, font=font_val)
        return y + 96

    y = price_y

    # Row 1
    if avg_close:
        y = two_col(y, "Entry Price", entry_price, "Average Close Price", avg_close)
    elif tp:
        y = two_col(y, "Entry Price", entry_price, "Take Profit", tp, c2=COLORS["green"])
    else:
        draw.text((MARGIN, y), "Entry Price", fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+32), entry_price, fill=COLORS["white"], font=font_val)
        y += 96

    # Additional rows for TP/SL if avg_close was present
    if avg_close and tp and sl:
        y += 8
        y = two_col(y, "Take Profit", tp, "Stop Loss", sl, c1=COLORS["green"], c2=COLORS["red"])
    elif avg_close and tp:
        y += 8
        draw.text((MARGIN, y), "Take Profit", fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+32), tp, fill=COLORS["green"], font=font_val)
        y += 96
    elif avg_close and sl:
        y += 8
        draw.text((MARGIN, y), "Stop Loss", fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+32), sl, fill=COLORS["red"], font=font_val)
        y += 96
    elif not avg_close and sl:
        # TP already shown in row1, now show SL
        y += 8
        if risk_reward:
            y = two_col(y, "Stop Loss", sl, "Risk / Reward", risk_reward, c1=COLORS["red"])
        else:
            draw.text((MARGIN, y), "Stop Loss", fill=COLORS["gray_label"], font=font_label)
            draw.text((MARGIN, y+32), sl, fill=COLORS["red"], font=font_val)
            y += 96

    # Risk/Reward and Confidence
    if risk_reward or confidence:
        y += 8
        if risk_reward and confidence:
            y = two_col(y, "Risk / Reward", risk_reward, "Confidence", confidence)
        elif risk_reward:
            draw.text((MARGIN, y), "Risk / Reward", fill=COLORS["gray_label"], font=font_label)
            draw.text((MARGIN, y+32), risk_reward, fill=COLORS["white"], font=font_val)
            y += 96
        elif confidence:
            draw.text((MARGIN, y), "Confidence", fill=COLORS["gray_label"], font=font_label)
            draw.text((MARGIN, y+32), confidence, fill=COLORS["white"], font=font_val)
            y += 96

    # Footer
    footer_y = H - 280
    draw.line([(0, footer_y), (W, footer_y)], fill=COLORS["border"], width=2)

    logo_x, logo_y = MARGIN, footer_y + 28
    draw_binance_logo(draw, logo_x, logo_y)

    font_ref_lbl = get_font(20, bold=False)
    font_ref_code = get_font(22, bold=True)
    ref_y = logo_y + 78
    draw.text((MARGIN+8, ref_y), "Referral Code", fill=COLORS["white"], font=font_ref_lbl)
    try:
        w_lbl = draw.textbbox((0,0), "Referral Code ", font=font_ref_lbl)[2]
    except:
        w_lbl = 150
    draw.text((MARGIN+8+w_lbl+6, ref_y), referral_code, fill=COLORS["white"], font=font_ref_code)

    qr_img = generate_qr(170)
    qr_x = W - MARGIN - qr_img.width - 8
    qr_y = footer_y + 28
    img.paste(qr_img, (qr_x, qr_y))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, "PNG", optimize=True)
    print(f"Generated card: {OUTPUT_PATH}")
    print(f"Symbol: {full_symbol}, Position: {position_display} {leverage}, PNL: {pnl} {pnl_currency}")
    return OUTPUT_PATH

if __name__ == "__main__":
    main()
