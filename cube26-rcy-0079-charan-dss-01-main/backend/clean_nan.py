from app.database.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
sql = """
UPDATE charges SET unit_id = NULL WHERE unit_id = 'nan';
UPDATE charges SET shipment_id = NULL WHERE shipment_id = 'nan';
UPDATE charges SET order_id = NULL WHERE order_id = 'nan';
UPDATE charges SET sku = NULL WHERE sku = 'nan';
UPDATE charges SET fnsku = NULL WHERE fnsku = 'nan';
UPDATE evidence_records SET unit_id = NULL WHERE unit_id = 'nan';
UPDATE evidence_records SET shipment_id = NULL WHERE shipment_id = 'nan';
UPDATE evidence_records SET order_id = NULL WHERE order_id = 'nan';
UPDATE evidence_records SET sku = NULL WHERE sku = 'nan';
"""
for stmt in sql.strip().split(";"):
    stmt = stmt.strip()
    if stmt:
        db.execute(text(stmt))
db.commit()
print("[SUCCESS] All 'nan' strings cleaned to NULL in Neon PostgreSQL")
db.close()
