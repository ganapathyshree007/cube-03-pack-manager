import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Product, Rule
from app.schemas.pydantic_schemas import ProductSchema, RuleSchema, ProductCreate

router = APIRouter()

@router.get("", response_model=List[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    results = []
    for p in products:
        p_rules = db.query(Rule).filter(Rule.product_id == p.id).all()
        rule_schemas = [RuleSchema.from_orm(r) for r in p_rules]
        results.append(ProductSchema(
            id=p.id,
            name=p.name,
            asin=p.asin,
            sku=p.sku,
            category=p.category,
            description=p.description,
            requirements=rule_schemas
        ))
    return results

@router.post("", response_model=ProductSchema)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """
    Creates a new product with custom preparation rules dynamically.
    """
    existing = db.query(Product).filter(Product.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product ID '{payload.id}' already exists.")

    product = Product(
        id=payload.id,
        name=payload.name,
        asin=payload.asin,
        sku=payload.sku,
        category=payload.category,
        description=payload.description
    )
    db.add(product)

    rule_schemas = []
    for idx, r_data in enumerate(payload.rules):
        rule_id = f"{payload.id.lower()}_{r_data.category}_{idx}_{uuid.uuid4().hex[:4]}"
        rule = Rule(
            id=rule_id,
            product_id=payload.id,
            name=r_data.name,
            category=r_data.category,
            visually_verifiable=r_data.visually_verifiable,
            evaluation_type=r_data.evaluation_type,
            description=r_data.description,
            required_views=r_data.required_views or "front"
        )
        db.add(rule)
        rule_schemas.append(rule)

    db.commit()
    db.refresh(product)

    return ProductSchema(
        id=product.id,
        name=product.name,
        asin=product.asin,
        sku=product.sku,
        category=product.category,
        description=product.description,
        requirements=[RuleSchema.from_orm(r) for r in rule_schemas]
    )

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    rules = db.query(Rule).filter(Rule.product_id == product_id).all()
    rule_schemas = [RuleSchema.from_orm(r) for r in rules]
    return ProductSchema(
        id=product.id,
        name=product.name,
        asin=product.asin,
        sku=product.sku,
        category=product.category,
        description=product.description,
        requirements=rule_schemas
    )

@router.get("/{product_id}/rules", response_model=List[RuleSchema])
def get_product_rules(product_id: str, db: Session = Depends(get_db)):
    rules = db.query(Rule).filter(Rule.product_id == product_id).all()
    return [RuleSchema.from_orm(r) for r in rules]

@router.delete("/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    db.delete(product)
    db.commit()
    return {"message": f"Product '{product_id}' deleted successfully."}
