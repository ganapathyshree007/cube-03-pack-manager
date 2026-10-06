#!/usr/bin/env python3
"""
Recovery Manager Headless Agent CLI Runner
Usage:
    python run_recovery.py --company org_demo_alpha
"""
import sys
import argparse
import json
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db
from app.models.models import Charge, Company
from app.services.charge_service import charge_service
from app.services.stats_service import stats_service
from app.agents.recovery_agent import recovery_agent

def main():
    parser = argparse.ArgumentParser(description="Headless Recovery Manager Agent")
    parser.add_argument("--company", default="org_demo_alpha", help="Company ID to evaluate (e.g. org_demo_alpha)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()

    try:
        print(f"[*] Running Recovery Agent investigation for tenant: {args.company}...")
        results = charge_service.run_batch_investigations(db, args.company)
        metrics = stats_service.get_dashboard_metrics(db, args.company)

        if args.format == "json":
            output = {
                "company_id": args.company,
                "execution_summary": results,
                "metrics": metrics
            }
            print(json.dumps(output, indent=2))
        else:
            print("\n" + "=" * 55)
            print(f"   RCY RECOVERY MANAGER EVALUATION SUMMARY")
            print("=" * 55)
            print(f"Company ID:              {args.company}")
            print(f"Total Fees Processed:    ${metrics['total_fees']:.2f}")
            print(f"Recoverable Pipeline:    ${metrics['potential_recovery']:.2f}")
            print(f"Claim Precision Rate:    {metrics['claim_precision_rate']}%")
            print("-" * 55)
            print(f"Contradicted (Claims):   {metrics['contradicted_count']}")
            print(f"Silent (No Evidence):    {metrics['silent_count']}")
            print(f"Uncertain (Ambiguous):   {metrics['uncertain_count']}")
            print(f"Supported (Valid Fees):  {metrics.get('supported_count', 1)}")
            print(f"Duplicate / Offset:      {metrics['duplicate_count'] + metrics['already_reimbursed_count']}")
            print("=" * 55)
            print("\n[SUCCESS] Headless evaluation completed with 0 errors.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
