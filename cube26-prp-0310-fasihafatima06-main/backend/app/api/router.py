from fastapi import APIRouter
from app.api import inspections, products, rules, agent, scenarios

api_router = APIRouter()

api_router.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(rules.router, prefix="/rules", tags=["Rules"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
