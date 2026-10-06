import os
from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.db.models import Product, Rule

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            return

        # Product 1: Liquid Container (Shampoo / Essential Oils)
        bottle = Product(
            id="DEMO-BOTTLE-001",
            name="Liquid Container (500ml Shampoo)",
            asin="B08N5WRWNW",
            sku="LQD-BTL-001",
            category="Liquid / Bottle",
            description="500ml liquid container requiring leak-proof polybag, heat seal, suffocation warning, FNSKU, and barcode covering."
        )
        db.add(bottle)
        
        bottle_rules = [
            Rule(
                id="bottle_polybag_presence",
                product_id="DEMO-BOTTLE-001",
                name="Polybag Presence",
                category="packaging",
                visually_verifiable=True,
                evaluation_type="detect_polybag",
                description="Liquid container must be fully enclosed in a clear, sealed polybag to prevent leaks.",
                required_views="front"
            ),
            Rule(
                id="bottle_polybag_sealing",
                product_id="DEMO-BOTTLE-001",
                name="Polybag Sealing",
                category="packaging",
                visually_verifiable=True,
                evaluation_type="detect_seal",
                description="Polybag must be fully heat-sealed or tape-sealed with no open seams.",
                required_views="front"
            ),
            Rule(
                id="bottle_suffocation_warning",
                product_id="DEMO-BOTTLE-001",
                name="Suffocation Warning",
                category="warning",
                visually_verifiable=True,
                evaluation_type="ocr_warning",
                description="Polybag with 5+ inch opening must display legible suffocation warning text, not obscured by folds.",
                required_views="front"
            ),
            Rule(
                id="bottle_fnsku_placement",
                product_id="DEMO-BOTTLE-001",
                name="FNSKU Placement",
                category="label",
                visually_verifiable=True,
                evaluation_type="barcode_geometry",
                description="FNSKU barcode label must be placed flat on outside package surface, not crossing curved edges or seams.",
                required_views="front"
            ),
            Rule(
                id="bottle_manufacturer_barcode",
                product_id="DEMO-BOTTLE-001",
                name="Original Barcode Covered",
                category="barcode",
                visually_verifiable=True,
                evaluation_type="barcode_visibility",
                description="Original manufacturer UPC/EAN barcode must be fully covered by the FNSKU or opaque label.",
                required_views="back"
            ),
            Rule(
                id="bottle_plastic_thickness",
                product_id="DEMO-BOTTLE-001",
                name="Plastic Thickness (3 mil min)",
                category="packaging",
                visually_verifiable=False,
                evaluation_type="physical_property",
                description="Polybag film thickness must be at least 1.5 mil (3 mil for liquids). Requires physical micrometer measurement.",
                required_views="front"
            )
        ]
        for r in bottle_rules:
            db.add(r)

        # Product 2: Boxed Electronics
        elec = Product(
            id="DEMO-ELEC-002",
            name="Boxed Electronics Hub (Smart Gateway)",
            asin="B09K8Y7Z1X",
            sku="ELE-HUB-002",
            category="Boxed Electronics",
            description="Precision electronic device in corrugated box container requiring flat FNSKU, barcode covering, and handling marks."
        )
        db.add(elec)

        elec_rules = [
            Rule(
                id="elec_fnsku_placement",
                product_id="DEMO-ELEC-002",
                name="FNSKU Placement",
                category="label",
                visually_verifiable=True,
                evaluation_type="barcode_geometry",
                description="FNSKU label must be placed flat on smooth outer box face, not crossing box seams.",
                required_views="front"
            ),
            Rule(
                id="elec_manufacturer_barcode",
                product_id="DEMO-ELEC-002",
                name="Original Barcode Covered",
                category="barcode",
                visually_verifiable=True,
                evaluation_type="barcode_visibility",
                description="Original serial/UPC barcode must be completely covered.",
                required_views="back"
            ),
            Rule(
                id="elec_handling_mark",
                product_id="DEMO-ELEC-002",
                name="Handling Marks Visible",
                category="warning",
                visually_verifiable=True,
                evaluation_type="handling_mark",
                description="Box must prominently display 'THIS WAY UP' or 'FRAGILE' orientation marks.",
                required_views="front"
            ),
            Rule(
                id="elec_drop_test_certification",
                product_id="DEMO-ELEC-002",
                name="Drop-Test Packaging Durability",
                category="packaging",
                visually_verifiable=False,
                evaluation_type="physical_property",
                description="Package must withstand 3-foot corner drop test without box deformation. Laboratory drop test required.",
                required_views="front"
            )
        ]
        for r in elec_rules:
            db.add(r)

        # Product 3: Plush & Soft Goods
        toy = Product(
            id="DEMO-TOY-003",
            name="Plush Bear Toy (Soft Plushie)",
            asin="B07V2X9C8L",
            sku="TOY-PLSH-003",
            category="Plush & Soft Goods",
            description="Soft teddy bear requiring transparent protective polybagging, suffocation warning, and outer FNSKU."
        )
        db.add(toy)

        toy_rules = [
            Rule(
                id="toy_polybag_presence",
                product_id="DEMO-TOY-003",
                name="Polybag Presence",
                category="packaging",
                visually_verifiable=True,
                evaluation_type="detect_polybag",
                description="Plush material must be clean and fully polybagged prior to inbound receiving.",
                required_views="front"
            ),
            Rule(
                id="toy_suffocation_warning",
                product_id="DEMO-TOY-003",
                name="Suffocation Warning Legibility",
                category="warning",
                visually_verifiable=True,
                evaluation_type="ocr_warning",
                description="Polybag must display printed child safety suffocation warning text.",
                required_views="front"
            ),
            Rule(
                id="toy_fnsku_placement",
                product_id="DEMO-TOY-003",
                name="FNSKU Placement",
                category="label",
                visually_verifiable=True,
                evaluation_type="barcode_geometry",
                description="Scannable FNSKU barcode must be affixed to the outer bag.",
                required_views="front"
            )
        ]
        for r in toy_rules:
            db.add(r)

        # Product 4: Fragile Glassware
        fragile = Product(
            id="DEMO-GLASS-004",
            name="Fragile Glassware Mug Set",
            asin="B09MGLASS4",
            sku="GLS-MUG-004",
            category="Fragile Glassware",
            description="Breakable ceramic/glass drinkware requiring protective bubble wrap, FRAGILE handling marks, and FNSKU label."
        )
        db.add(fragile)

        fragile_rules = [
            Rule(
                id="fragile_polybag_presence",
                product_id="DEMO-GLASS-004",
                name="Protective Wrap Presence",
                category="packaging",
                visually_verifiable=True,
                evaluation_type="detect_polybag",
                description="Glassware must be wrapped in protective bubble film or polybag.",
                required_views="front"
            ),
            Rule(
                id="fragile_handling_mark",
                product_id="DEMO-GLASS-004",
                name="Fragile Handling Marks Visible",
                category="warning",
                visually_verifiable=True,
                evaluation_type="handling_mark",
                description="Container must display prominent 'FRAGILE' or 'HANDLE WITH CARE' label.",
                required_views="front"
            ),
            Rule(
                id="fragile_fnsku_placement",
                product_id="DEMO-GLASS-004",
                name="FNSKU Placement",
                category="label",
                visually_verifiable=True,
                evaluation_type="barcode_geometry",
                description="FNSKU label must be placed flat on smooth outer surface.",
                required_views="front"
            )
        ]
        for r in fragile_rules:
            db.add(r)

        # Product 5: Perishable / Expiry Items
        expiry_item = Product(
            id="DEMO-FOOD-005",
            name="Organic Energy Bar Pack (Expiry Item)",
            asin="B08FOODBAR5",
            sku="FOD-BAR-005",
            category="Perishable Expiry Goods",
            description="Grocery/perishable item requiring clear polybagging, FNSKU, covered UPC, and legible Expiry Date after wrapping."
        )
        db.add(expiry_item)

        expiry_rules = [
            Rule(
                id="expiry_polybag_presence",
                product_id="DEMO-FOOD-005",
                name="Polybag Presence",
                category="packaging",
                visually_verifiable=True,
                evaluation_type="detect_polybag",
                description="Packaged food item must be enclosed in transparent protective polybag.",
                required_views="front"
            ),
            Rule(
                id="expiry_date_legibility",
                product_id="DEMO-FOOD-005",
                name="Expiry Date Legible After Wrapping",
                category="expiry",
                visually_verifiable=True,
                evaluation_type="expiry_date",
                description="Expiry date (EXP MM/YYYY) must remain clearly visible and legible after polybag wrapping.",
                required_views="front"
            ),
            Rule(
                id="expiry_fnsku_placement",
                product_id="DEMO-FOOD-005",
                name="FNSKU Placement",
                category="label",
                visually_verifiable=True,
                evaluation_type="barcode_geometry",
                description="FNSKU barcode label placed flat on outer polybag.",
                required_views="front"
            ),
            Rule(
                id="expiry_manufacturer_barcode",
                product_id="DEMO-FOOD-005",
                name="Original Barcode Covered",
                category="barcode",
                visually_verifiable=True,
                evaluation_type="barcode_visibility",
                description="Original product barcode fully covered.",
                required_views="back"
            )
        ]
        for r in expiry_rules:
            db.add(r)

        db.commit()
    finally:
        db.close()
