import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FIXTURE_DIR = Path(__file__).resolve().parent
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)


def draw_label(draw, text_lines, x=50, y=50, w=300, h=150, bg=(255, 255, 255), border=(0, 0, 0)):
    draw.rectangle([x, y, x + w, y + h], fill=bg, outline=border, width=3)
    curr_y = y + 15
    for line in text_lines:
        draw.text((x + 15, curr_y), line, fill=(0, 0, 0))
        curr_y += 25


def create_clean_pallet():
    img = Image.new("RGB", (640, 480), (220, 220, 210))
    draw = ImageDraw.Draw(img)
    # Pallet base
    draw.rectangle([60, 360, 580, 420], fill=(139, 90, 43), outline=(80, 50, 20), width=4)
    # Carton 1
    draw.rectangle([80, 160, 310, 360], fill=(210, 160, 110), outline=(100, 70, 40), width=4)
    draw_label(draw, ["SKU: BLUE-BOTTLE-001", "PO: PO-TEST-001", "CARTON 1 / 2", "QTY: 12 UNITS"], x=95, y=180, w=200, h=110)
    # Carton 2
    draw.rectangle([330, 160, 560, 360], fill=(210, 160, 110), outline=(100, 70, 40), width=4)
    draw_label(draw, ["SKU: BLUE-BOTTLE-001", "PO: PO-TEST-001", "CARTON 2 / 2", "QTY: 12 UNITS"], x=345, y=180, w=200, h=110)
    # Banner
    draw.rectangle([10, 10, 630, 40], fill=(40, 40, 40))
    draw.text((20, 15), "RECEIVING INSPECTION - CLEAN PALLET (2 CARTONS INTACT)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "clean_blue_bottle_pallet.png")


def create_open_carton_12():
    img = Image.new("RGB", (640, 480), (200, 190, 180))
    draw = ImageDraw.Draw(img)
    # Carton box rim
    draw.rectangle([50, 50, 590, 430], fill=(190, 140, 90), outline=(90, 60, 30), width=6)
    draw.rectangle([70, 70, 570, 410], fill=(140, 100, 60))
    # 12 Bottles grid (3x4)
    for row in range(3):
        for col in range(4):
            cx = 120 + col * 120
            cy = 120 + row * 100
            # Bottle body
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(30, 120, 220), outline=(10, 60, 140), width=3)
            # Cap
            draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(240, 240, 240), outline=(0, 0, 0), width=2)
    # Banner
    draw.rectangle([10, 10, 630, 40], fill=(40, 40, 40))
    draw.text((20, 15), "OPENED CARTON VIEW - 12 UNITS COUNTED (FULL COUNT)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "clean_open_carton_12_units.png")


def create_crushed_carton():
    img = Image.new("RGB", (640, 480), (220, 220, 210))
    draw = ImageDraw.Draw(img)
    # Pallet
    draw.rectangle([60, 360, 580, 420], fill=(139, 90, 43), outline=(80, 50, 20), width=4)
    # Carton 1 (Crushed corner)
    points = [(80, 200), (280, 160), (310, 360), (80, 360)]
    draw.polygon(points, fill=(210, 160, 110), outline=(100, 70, 40))
    # Defect crushing hazard overlay
    draw.polygon([(80, 200), (160, 220), (140, 290), (80, 270)], fill=(150, 50, 40), outline=(255, 0, 0), width=3)
    draw_label(draw, ["DEFECT: CRUSHED", "CORNER CRUSHED", "DAMAGE DETECTED"], x=180, y=220, w=120, h=90, bg=(255, 200, 200))
    # Banner
    draw.rectangle([10, 10, 630, 40], fill=(180, 30, 30))
    draw.text((20, 15), "RECEIVING INSPECTION - CARTON DAMAGE (CORNER CRUSHING)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "crushed_carton_face.png")


def create_damaged_unit():
    img = Image.new("RGB", (640, 480), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Bottle
    draw.rectangle([220, 120, 420, 400], fill=(30, 120, 220), outline=(10, 60, 140), width=4)
    # Damage dent
    draw.polygon([(220, 220), (280, 260), (220, 300)], fill=(180, 40, 40), outline=(255, 0, 0), width=3)
    draw_label(draw, ["UNIT DAMAGE", "CRUSHED DENT"], x=430, y=200, w=180, h=80, bg=(255, 220, 220))
    draw.rectangle([10, 10, 630, 40], fill=(180, 30, 30))
    draw.text((20, 15), "SAMPLED UNIT - UNIT DAMAGE DETECTED (BODY CRUSHING)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "damaged_unit_crushed_bottle.png")


def create_wrong_colour():
    img = Image.new("RGB", (640, 480), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Red Bottle instead of Blue
    draw.rectangle([220, 120, 420, 400], fill=(220, 40, 40), outline=(140, 10, 10), width=4)
    draw_label(draw, ["SKU: RED-BOTTLE-999", "COLOUR: RED", "MISMATCH DETECTED"], x=50, y=180, w=160, h=100, bg=(255, 220, 220))
    draw.rectangle([10, 10, 630, 40], fill=(180, 30, 30))
    draw.text((20, 15), "SAMPLED UNIT - WRONG COLOUR (RED INSTEAD OF SPEC BLUE)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "red_bottle_wrong_colour.png")


def create_short_carton_10():
    img = Image.new("RGB", (640, 480), (200, 190, 180))
    draw = ImageDraw.Draw(img)
    # Carton box rim
    draw.rectangle([50, 50, 590, 430], fill=(190, 140, 90), outline=(90, 60, 30), width=6)
    draw.rectangle([70, 70, 570, 410], fill=(140, 100, 60))
    # 10 Bottles grid (2 missing)
    count = 0
    for row in range(3):
        for col in range(4):
            if count >= 10:
                break
            cx = 120 + col * 120
            cy = 120 + row * 100
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(30, 120, 220), outline=(10, 60, 140), width=3)
            draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(240, 240, 240), outline=(0, 0, 0), width=2)
            count += 1
    # Empty slots
    draw.rectangle([330, 290, 410, 370], fill=(80, 50, 30), outline=(255, 0, 0), width=2)
    draw.rectangle([450, 290, 530, 370], fill=(80, 50, 30), outline=(255, 0, 0), width=2)
    draw.rectangle([10, 10, 630, 40], fill=(180, 30, 30))
    draw.text((20, 15), "OPENED CARTON VIEW - 10 UNITS COUNTED (QUANTITY SHORT -2)", fill=(255, 255, 255))
    img.save(FIXTURE_DIR / "open_carton_short_10_units.png")


def generate_manifest():
    manifest = {
        "RCV-0001": {
            "unit_id": "UNIT-0001",
            "description": "Clean receipt case",
            "photo_refs": [
                str(FIXTURE_DIR / "clean_blue_bottle_pallet.png"),
                str(FIXTURE_DIR / "clean_open_carton_12_units.png"),
            ],
        },
        "RCV-0003": {
            "unit_id": "UNIT-0003",
            "description": "Quantity short and carton crushing case",
            "photo_refs": [
                str(FIXTURE_DIR / "crushed_carton_face.png"),
                str(FIXTURE_DIR / "open_carton_short_10_units.png"),
            ],
        },
        "RCV-0007": {
            "unit_id": "UNIT-0007",
            "description": "Wrong colour defect case",
            "photo_refs": [
                str(FIXTURE_DIR / "red_bottle_wrong_colour.png"),
            ],
        },
        "RCV-0042": {
            "unit_id": "UNIT-0042",
            "description": "Unit damage defect case",
            "photo_refs": [
                str(FIXTURE_DIR / "damaged_unit_crushed_bottle.png"),
            ],
        },
    }
    with open(FIXTURE_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("Fixtures and manifest generated successfully!")


if __name__ == "__main__":
    create_clean_pallet()
    create_open_carton_12()
    create_crushed_carton()
    create_damaged_unit()
    create_wrong_colour()
    create_short_carton_10()
    generate_manifest()
