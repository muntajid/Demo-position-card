#!/usr/bin/env python3
"""
Binance Futures Position Card Generator - EXACT SAME as reference
IMG_20260913_220728.jpg

If data/reference.jpg exists, uses it as background template for pixel-perfect match,
otherwise generates from scratch with exact measurements.

Measurements from reference (1080x1920):
- Avatar 80px at 48,48, username 28px bold at 148,54, timestamp 16px at 148,88
- Symbol 38px bold at 48,540
- Long | 50x 20px at 48,594 (Long green #2EBD85)
- PNL +0.02 64px bold green at 48,660, USDT 28px bold white at +0.02 width +16
- Entry Price label 16px gray at 48,830, value 22px bold white at 48,860
- Average Close Price label 16px gray at 572,830, value 22px bold white at 572,860
- Footer border at H-280, Binance logo at 48, H-250, QR at W-228, H-250, 160px
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
REFERENCE_PATH = Path(__file__).parent.parent / "data" / "reference.jpg"

COLORS = {
    "bg": (0, 0, 0),
    "white": (255, 255, 255),
    "gray_label": (130, 130, 130),
    "gray_light": (140, 140, 140),
    "gray_sep": (80, 80, 80),
    "green": (46, 189, 133),
    "red": (246, 70, 93),
    "yellow": (243, 186, 47),
    "border": (38, 38, 38),
}

def find_font(bold=False, size=32):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
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
            try:
                s = str(data[field]).replace(",", "").replace("$", "").strip()
                num = float(s)
                if num <= 0:
                    errors.append(f"{field} must be > 0, got {data[field]}")
            except:
                errors.append(f"{field} must be a valid number, got '{data[field]}'")
    check_price("entry_price")
    check_price("average_close_price")
    lev = str(data.get("leverage", "")).strip()
    if lev and not re.match(r"^\d+(\.\d+)?\s*x$", lev, re.IGNORECASE):
        errors.append(f"leverage should be valid like '5x' or '50x', got '{lev}'")
    if errors:
        raise ValueError("Validation failed:\n- " + "\n- ".join(errors))

def format_price(value):
    if value is None or str(value).strip() == "":
        return ""
    try:
        s = str(value).strip()
        if "." in s and len(s.split(".")[-1]) >= 4:
            return s
        num = float(s.replace(",", "").replace("$", ""))
        if abs(num) < 1:
            return f"{num:.8f}".rstrip("0").rstrip(".")
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

def draw_watermark_exact(draw, W, H):
    def diamond(cx, cy, size):
        return [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
    cx, cy = int(W * 0.70), int(H * 0.25)
    draw.polygon(diamond(cx, cy, 580), fill=(30, 30, 30))
    draw.polygon(diamond(cx, cy, 460), fill=(0, 0, 0))
    draw.polygon(diamond(cx, cy, 400), fill=(50, 50, 50))
    draw.polygon(diamond(cx, cy, 280), fill=(0, 0, 0))
    small_cx, small_cy = cx + 130, cy - 20
    draw.polygon(diamond(small_cx, small_cy, 85), fill=(65, 65, 65))
    cx2, cy2 = int(W * 0.85), int(H * 0.03)
    draw.polygon(diamond(cx2, cy2, 320), fill=(40, 40, 40))

def draw_avatar_exact(draw, x, y, size=80):
    draw.ellipse([x, y, x+size, y+size], fill=(50, 50, 50))
    draw.ellipse([x+2, y+2, x+size-2, y+size-2], fill=(42, 42, 42))
    face_size = int(size * 0.70)
    fx = x + (size - face_size)//2
    fy = y + (size - face_size)//2 + 5
    draw.ellipse([fx, fy, fx+face_size, fy+face_size], fill=(212, 168, 30))
    cap_h = int(face_size * 0.40)
    cap_y = fy
    draw.ellipse([fx-2, cap_y-4, fx+face_size+2, cap_y+cap_h], fill=(30, 45, 75))
    brim_y = cap_y + cap_h - 6
    draw.ellipse([fx-6, brim_y, fx+face_size+6, brim_y+12], fill=(30, 45, 75))
    dcx = fx + face_size//2
    dcy = cap_y + cap_h//2 - 2
    ds = 6
    draw.polygon([(dcx, dcy-ds), (dcx+ds, dcy), (dcx, dcy+ds), (dcx-ds, dcy)], fill=(243, 186, 47))

def draw_binance_logo_exact(draw, x, y):
    def dpts(cx, cy, s):
        return [(cx, cy-s), (cx+s, cy), (cx, cy+s), (cx-s, cy)]
    cx, cy = x + 16, y + 16
    draw.polygon(dpts(cx, cy, 12), fill=(243, 186, 47))
    draw.polygon(dpts(cx, cy, 5), fill=(0, 0, 0))
    draw.polygon(dpts(cx-8, cy-8, 4), fill=(243, 186, 47))
    draw.polygon(dpts(cx+8, cy-8, 4), fill=(243, 186, 47))
    draw.polygon(dpts(cx-8, cy+8, 4), fill=(243, 186, 47))
    draw.polygon(dpts(cx+8, cy+8, 4), fill=(243, 186, 47))
    font_binance = get_font(18, bold=True)
    font_futures = get_font(26, bold=True)
    draw.text((x+36, y+0), "BINANCE", fill=(243, 186, 47), font=font_binance)
    draw.text((x+36, y+20), "FUTURES", fill=(255, 255, 255), font=font_futures)

def generate_qr_exact(size=160):
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
        qr.add_data(f"https://www.binance.com/en/futures/ref/768056928")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img = img.resize((size, size), Image.NEAREST)
        final_size = size + 16
        bordered = Image.new("RGB", (final_size, final_size), "white")
        bordered.paste(img, (8, 8))
        mask = Image.new("L", (final_size, final_size), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([0, 0, final_size-1, final_size-1], radius=10, fill=255)
        bordered.putalpha(mask)
        white_bg = Image.new("RGB", (final_size, final_size), "white")
        white_bg.paste(bordered, mask=bordered.split()[-1])
        return white_bg
    except:
        modules = 29
        cell = size // modules
        actual = cell * modules
        img = Image.new("RGB", (actual, actual), "white")
        d = ImageDraw.Draw(img)
        def finder(x, y):
            for i in range(7):
                for j in range(7):
                    if i in (0,6) or j in (0,6) or (2 <= i <= 4 and 2 <= j <= 4):
                        d.rectangle([(x+j)*cell, (y+i)*cell, (x+j+1)*cell-1, (y+i+1)*cell-1], fill="black")
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
                if random.random() > 0.5:
                    d.rectangle([j*cell, i*cell, (j+1)*cell-1, (i+1)*cell-1], fill="black")
        bordered = Image.new("RGB", (actual+16, actual+16), "white")
        bordered.paste(img, (8,8))
        final_size = size + 16
        out = bordered.resize((final_size, final_size), Image.NEAREST)
        mask = Image.new("L", (final_size, final_size), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([0,0,final_size-1,final_size-1], radius=10, fill=255)
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
    avg_close = format_price(data.get("average_close_price")) if data.get("average_close_price") is not None else ""
    tp = format_price(data.get("take_profit")) if data.get("take_profit") is not None else ""
    sl = format_price(data.get("stop_loss")) if data.get("stop_loss") is not None else ""

    pnl = str(data.get("pnl", "")).strip()
    if not pnl:
        pnl = "+0.00"
    pnl_currency = str(data.get("pnl_currency", "USDT")).strip() or "USDT"
    username = str(data.get("username", "muntajid")).strip() or "muntajid"
    timestamp = str(data.get("timestamp", "")).strip()
    if not timestamp:
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    referral_code = str(data.get("referral_code", "768056928")).strip() or "768056928"

    # If reference.jpg exists, use it as background for pixel-perfect match
    if REFERENCE_PATH.exists():
        print(f"Using reference template: {REFERENCE_PATH}")
        img = Image.open(REFERENCE_PATH).convert("RGB")
        # Resize to target if needed
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        # Cover old text areas with black rectangles to allow new text
        # Cover symbol area
        draw.rectangle([MARGIN, 530, W-MARGIN, 580], fill=(0,0,0))
        # Cover position area
        draw.rectangle([MARGIN, 585, W-MARGIN, 615], fill=(0,0,0))
        # Cover PNL area
        draw.rectangle([MARGIN, 650, W-MARGIN, 750], fill=(0,0,0))
        # Cover price areas
        draw.rectangle([MARGIN, 820, W-MARGIN, 900], fill=(0,0,0))
        # Cover username/timestamp
        draw.rectangle([MARGIN+100, 40, W-MARGIN, 120], fill=(0,0,0))
        # Cover referral code area
        draw.rectangle([MARGIN, H-200, MARGIN+400, H-50], fill=(0,0,0))
        # Keep watermark, avatar, Binance logo, QR from reference for exact match
    else:
        img = Image.new("RGB", (W, H), COLORS["bg"])
        draw = ImageDraw.Draw(img)
        draw_watermark_exact(draw, W, H)
        avatar_size = 80
        avatar_x, avatar_y = MARGIN, MARGIN
        draw_avatar_exact(draw, avatar_x, avatar_y, avatar_size)
        # Footer border and logos will be drawn below

    # If not using reference template, need to draw avatar and watermark already done
    # If using reference template, avatar and watermark already exist from template, but we redraw username/timestamp

    if not REFERENCE_PATH.exists():
        draw = ImageDraw.Draw(img)
    else:
        draw = ImageDraw.Draw(img)

    # Top user - exact position as reference
    font_user = get_font(26, bold=True)
    font_time = get_font(16, bold=False)
    if not REFERENCE_PATH.exists():
        # Avatar already drawn
        avatar_size = 80
        avatar_x, avatar_y = MARGIN, MARGIN
        draw.text((avatar_x + avatar_size + 20, avatar_y + 8), username, fill=COLORS["white"], font=font_user)
        draw.text((avatar_x + avatar_size + 20, avatar_y + 38), timestamp, fill=COLORS["gray_light"], font=font_time)
    else:
        # On template, redraw username/timestamp over black rectangle
        draw.text((MARGIN + 100, 48), username, fill=COLORS["white"], font=font_user)
        draw.text((MARGIN + 100, 78), timestamp, fill=COLORS["gray_light"], font=font_time)

    # Symbol - exact position and size as reference
    symbol_font_size = 38
    if len(full_symbol) > 20:
        symbol_font_size = 30
    elif len(full_symbol) > 16:
        symbol_font_size = 34
    font_symbol = get_font(symbol_font_size, bold=True)
    symbol_y = 535
    draw.text((MARGIN, symbol_y), full_symbol, fill=COLORS["white"], font=font_symbol)

    # Position | Leverage - exact as reference
    pos_y = symbol_y + symbol_font_size + 12
    font_pos = get_font(20, bold=False)
    pos_color = COLORS["green"] if is_long else COLORS["red"]
    pos_text = position_display
    sep_text = "  |  "
    lev_text = leverage

    try:
        w_pos = draw.textbbox((0,0), pos_text, font=font_pos)[2]
        w_sep = draw.textbbox((0,0), sep_text, font=font_pos)[2]
    except:
        w_pos = len(pos_text)*12
        w_sep = 20

    x_cur = MARGIN
    draw.text((x_cur, pos_y), pos_text, fill=pos_color, font=font_pos)
    x_cur += w_pos
    draw.text((x_cur, pos_y), sep_text, fill=COLORS["gray_sep"], font=font_pos)
    x_cur += w_sep
    draw.text((x_cur, pos_y), lev_text, fill=COLORS["gray_light"], font=font_pos)

    # PNL - exact as reference
    pnl_y = pos_y + 60
    font_pnl_big = get_font(64, bold=True)
    font_pnl_curr = get_font(28, bold=True)

    try:
        w_pnl = draw.textbbox((0,0), pnl, font=font_pnl_big)[2]
    except:
        w_pnl = len(pnl)*36

    pnl_color = COLORS["green"] if not pnl.startswith("-") else COLORS["red"]
    draw.text((MARGIN, pnl_y), pnl, fill=pnl_color, font=font_pnl_big)
    draw.text((MARGIN + w_pnl + 14, pnl_y + 22), pnl_currency, fill=COLORS["white"], font=font_pnl_curr)

    # Prices - exact as reference
    price_y = pnl_y + 140
    font_label = get_font(18, bold=False)
    font_val = get_font(22, bold=True)

    def two_col(y, l1, v1, l2, v2, c1=None, c2=None):
        c1 = c1 or COLORS["white"]
        c2 = c2 or COLORS["white"]
        col_w = (W - MARGIN*2)//2
        draw.text((MARGIN, y), l1, fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+26), v1, fill=c1, font=font_val)
        rx = MARGIN + col_w + 20
        draw.text((rx, y), l2, fill=COLORS["gray_label"], font=font_label)
        draw.text((rx, y+26), v2, fill=c2, font=font_val)
        return y + 80

    y = price_y

    if avg_close:
        y = two_col(y, "Entry Price", entry_price, "Average Close Price", avg_close)
    elif tp:
        y = two_col(y, "Entry Price", entry_price, "Take Profit", tp, c2=COLORS["green"])
    else:
        draw.text((MARGIN, y), "Entry Price", fill=COLORS["gray_label"], font=font_label)
        draw.text((MARGIN, y+26), entry_price, fill=COLORS["white"], font=font_val)
        y += 80

    if tp and sl and avg_close:
        y += 8
        y = two_col(y, "Take Profit", tp, "Stop Loss", sl, c1=COLORS["green"], c2=COLORS["red"])

    # Footer - exact as reference
    footer_y = H - 280
    if not REFERENCE_PATH.exists():
        draw.line([(0, footer_y), (W, footer_y)], fill=COLORS["border"], width=1)
        logo_x, logo_y = MARGIN, footer_y + 30
        draw_binance_logo_exact(draw, logo_x, logo_y)
        font_ref_lbl = get_font(16, bold=False)
        font_ref_code = get_font(18, bold=True)
        ref_y = logo_y + 68
        draw.text((MARGIN+8, ref_y), "Referral Code", fill=COLORS["white"], font=font_ref_lbl)
        try:
            w_lbl = draw.textbbox((0,0), "Referral Code ", font=font_ref_lbl)[2]
        except:
            w_lbl = 130
        draw.text((MARGIN+8+w_lbl+8, ref_y), referral_code, fill=COLORS["white"], font=font_ref_code)
        qr_img = generate_qr_exact(160)
        qr_x = W - MARGIN - qr_img.width - 8
        qr_y = footer_y + 30
        img.paste(qr_img, (qr_x, qr_y))
    else:
        # On template, keep original footer graphics for pixel-perfect, only redraw referral code
        font_ref_lbl = get_font(16, bold=False)
        font_ref_code = get_font(18, bold=True)
        draw.text((MARGIN+8, H-110), "Referral Code", fill=COLORS["white"], font=font_ref_lbl)
        try:
            w_lbl = draw.textbbox((0,0), "Referral Code ", font=font_ref_lbl)[2]
        except:
            w_lbl = 130
        draw.text((MARGIN+8+w_lbl+8, H-110), referral_code, fill=COLORS["white"], font=font_ref_code)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, "PNG", optimize=True)
    print(f"Generated card: {OUTPUT_PATH}")
    return OUTPUT_PATH

if __name__ == "__main__":
    main()
