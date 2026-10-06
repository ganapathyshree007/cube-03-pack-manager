import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_sample_images(sample_dir: str = "sample_data"):
    os.makedirs(sample_dir, exist_ok=True)
    
    # 1. Scenario 1: PASS - Bottle correctly polybagged, sealed, warning text, flat FNSKU, covered barcode
    img1 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img1)
    # Draw bottle body
    draw.rounded_rectangle([250, 120, 550, 500], radius=40, fill="#FFFFFF", outline="#0F172A", width=3)
    draw.rectangle([340, 70, 460, 120], fill="#3B82F6", outline="#1E3A8A", width=2) # Cap
    # Draw Polybag outer seal boundary
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=2)
    draw.line([210, 60, 590, 60], fill="#64748B", width=4) # Heat seal top
    # Suffocation warning text box
    draw.rectangle([270, 150, 530, 210], fill="#FEF3C7", outline="#D97706", width=2)
    draw.text((280, 160), "WARNING: TO AVOID DANGER OF\nSUFFOCATION KEEP AWAY FROM BABIES", fill="#92400E")
    # FNSKU Label (placed flat on front container surface)
    draw.rectangle([280, 260, 520, 360], fill="#FFFFFF", outline="#1E293B", width=2)
    draw.text((320, 270), "FNSKU: X001A2B3C4", fill="#000000")
    # Barcode lines
    for bx in range(300, 500, 8):
        draw.line([bx, 295, bx, 345], fill="#000000", width=4)
    img1.save(os.path.join(sample_dir, "scenario_1_pass.jpg"))

    # 2. Scenario 2: FAIL - FNSKU label crossing curved edge of bottle
    img2 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img2)
    # Bottle body with curved right edge at x=550
    draw.rounded_rectangle([250, 120, 550, 500], radius=40, fill="#FFFFFF", outline="#0F172A", width=3)
    draw.rectangle([340, 70, 460, 120], fill="#3B82F6", outline="#1E3A8A", width=2)
    # Polybag
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=2)
    draw.line([210, 60, 590, 60], fill="#64748B", width=4)
    # Suffocation Warning
    draw.rectangle([270, 150, 530, 210], fill="#FEF3C7", outline="#D97706", width=2)
    draw.text((280, 160), "WARNING: SUFFOCATION HAZARD", fill="#92400E")
    # FNSKU Label CROSSING THE CURVED EDGE at x=550! (x range: 460 to 600)
    draw.rectangle([460, 260, 600, 360], fill="#FEE2E2", outline="#DC2626", width=3)
    draw.text((470, 270), "FNSKU: X001A2B3C4", fill="#991B1B")
    for bx in range(475, 585, 8):
        draw.line([bx, 295, bx, 345], fill="#000000", width=4)
    # Curved edge line highlight
    draw.line([550, 120, 550, 500], fill="#EF4444", width=3) # Intersecting curve line!
    img2.save(os.path.join(sample_dir, "scenario_2_fail_curved.jpg"))

    # 3. Scenario 3: FAIL - Original manufacturer UPC barcode visible / uncovered
    img3 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img3)
    # Rear view of bottle/box
    draw.rectangle([250, 120, 550, 500], fill="#FFFFFF", outline="#0F172A", width=3)
    # Polybag
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=2)
    # FNSKU label on top
    draw.rectangle([280, 160, 520, 260], fill="#FFFFFF", outline="#1E293B", width=2)
    draw.text((300, 170), "FNSKU: X001A2B3C4", fill="#000000")
    for bx in range(300, 500, 8):
        draw.line([bx, 190, bx, 240], fill="#000000", width=4)
    # UNCOVERED Original UPC Barcode visible at bottom!
    draw.rectangle([300, 380, 500, 470], fill="#FEF2F2", outline="#EF4444", width=3)
    draw.text((310, 390), "ORIGINAL UPC: 012345678905", fill="#B91C1C")
    for bx in range(320, 480, 6):
        draw.line([bx, 410, bx, 455], fill="#000000", width=3)
    img3.save(os.path.join(sample_dir, "scenario_3_fail_barcode.jpg"))

    # 4. Scenario 4: FAIL - Polybag present but missing suffocation warning text
    img4 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img4)
    # Bottle body
    draw.rounded_rectangle([250, 120, 550, 500], radius=40, fill="#FFFFFF", outline="#0F172A", width=3)
    draw.rectangle([340, 70, 460, 120], fill="#3B82F6", outline="#1E3A8A", width=2)
    # Polybag present
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=2)
    draw.line([210, 60, 590, 60], fill="#64748B", width=4)
    # NO WARNING TEXT! (Blank space where warning should be)
    draw.rectangle([270, 160, 530, 220], outline="#CBD5E1", width=1)
    draw.text((300, 180), "[NO SUFFOCATION WARNING DETECTED]", fill="#94A3B8")
    # FNSKU Label
    draw.rectangle([280, 270, 520, 370], fill="#FFFFFF", outline="#1E293B", width=2)
    draw.text((320, 280), "FNSKU: X001A2B3C4", fill="#000000")
    for bx in range(300, 500, 8):
        draw.line([bx, 305, bx, 355], fill="#000000", width=4)
    img4.save(os.path.join(sample_dir, "scenario_4_fail_warning.jpg"))

    # 5. Scenario 5: UNCERTAIN - Only Front view provided, Rear surface view missing
    img5 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img5)
    # Front view only
    draw.rounded_rectangle([250, 120, 550, 500], radius=40, fill="#FFFFFF", outline="#0F172A", width=3)
    draw.rectangle([340, 70, 460, 120], fill="#3B82F6", outline="#1E3A8A", width=2)
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=2)
    # Suffocation Warning & FNSKU present on front
    draw.rectangle([270, 150, 530, 210], fill="#FEF3C7", outline="#D97706", width=2)
    draw.text((280, 160), "WARNING: SUFFOCATION HAZARD", fill="#92400E")
    draw.rectangle([280, 260, 520, 360], fill="#FFFFFF", outline="#1E293B", width=2)
    draw.text((320, 270), "FNSKU: X001A2B3C4", fill="#000000")
    for bx in range(300, 500, 8):
        draw.line([bx, 295, bx, 345], fill="#000000", width=4)
    # Watermark text
    draw.text((260, 550), "[VIEW: FRONT SURFACE ONLY - REAR MISSING]", fill="#64748B")
    img5.save(os.path.join(sample_dir, "scenario_5_uncertain_rear.jpg"))

    # 6. Scenario 6: UNCERTAIN - Blurry / Severe Glare obscuring barcode
    img6 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img6)
    draw.rounded_rectangle([250, 120, 550, 500], radius=40, fill="#E2E8F0", outline="#64748B", width=3)
    # Severe white glare circle obscuring the barcode region
    draw.ellipse([220, 200, 600, 450], fill="#FFFFFF")
    draw.text((320, 310), "* SEVERE GLARE / BLUR *", fill="#94A3B8")
    # Apply Gaussian Blur filter
    img6 = img6.filter(ImageFilter.GaussianBlur(radius=5))
    img6.save(os.path.join(sample_dir, "scenario_6_uncertain_blurry.jpg"))

    # 7. Scenario 7: PASS - Plush Toy in sealed polybag with warning & FNSKU
    img7 = Image.new("RGB", (800, 600), "#F1F5F9")
    draw = ImageDraw.Draw(img7)
    # Plush toy outline (head, ears, body)
    draw.ellipse([300, 120, 500, 320], fill="#D97706", outline="#78350F", width=3) # Head
    draw.ellipse([270, 100, 330, 160], fill="#D97706", outline="#78350F", width=2) # Ear L
    draw.ellipse([470, 100, 530, 160], fill="#D97706", outline="#78350F", width=2) # Ear R
    draw.ellipse([280, 280, 520, 500], fill="#B45309", outline="#78350F", width=3) # Body
    # Polybag
    draw.rectangle([210, 50, 590, 540], outline="#64748B", width=3)
    draw.line([210, 60, 590, 60], fill="#475569", width=5) # Seal
    # Suffocation Warning
    draw.rectangle([250, 320, 550, 380], fill="#FEF3C7", outline="#D97706", width=2)
    draw.text((260, 335), "WARNING: TO AVOID DANGER OF SUFFOCATION\nKEEP THIS BAG AWAY FROM BABIES & CHILDREN", fill="#92400E")
    # FNSKU Label
    draw.rectangle([280, 400, 520, 480], fill="#FFFFFF", outline="#0F172A", width=2)
    draw.text((310, 410), "FNSKU: X003TOYPLSH", fill="#000000")
    for bx in range(300, 500, 8):
        draw.line([bx, 430, bx, 470], fill="#000000", width=4)
    img7.save(os.path.join(sample_dir, "scenario_7_pass_toy.jpg"))

    print(f"Generated 7 realistic sample images in '{sample_dir}' successfully.")

if __name__ == "__main__":
    generate_sample_images()
