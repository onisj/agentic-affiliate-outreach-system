import argparse
import logging
from services.ab_testing import ABTestingService
from database.session import get_db
from database.models import OutreachCampaign, MessageTemplate
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_campaigns():
    """List all available campaigns."""
    db = next(get_db())
    try:
        campaigns = db.query(OutreachCampaign).all()
        print("\nAvailable Campaigns:")
        for campaign in campaigns:
            print(f"ID: {campaign.id}, Name: {campaign.name}")
    finally:
        db.close()

def list_templates():
    """List all available templates."""
    db = next(get_db())
    try:
        templates = db.query(MessageTemplate).all()
        print("\nAvailable Templates:")
        for template in templates:
            print(f"ID: {template.id}, Name: {template.name}")
    finally:
        db.close()

def create_test(campaign_id: str, template_ids: list, duration: int, sample_size: int):
    """Create and start a new A/B test."""
    try:
        service = ABTestingService()
        test = service.create_test(
            campaign_id=campaign_id,
            template_ids=template_ids,
            test_duration_days=duration,
            sample_size_per_variant=sample_size
        )
        
        print("\nTest created successfully:")
        print(json.dumps(test, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Error creating test: {e}")

def get_results(campaign_id: str, metric: str = None):
    """Get A/B test results."""
    try:
        service = ABTestingService()
        
        if metric:
            results = service.get_test_results(campaign_id, metric)
            print(f"\nResults for metric '{metric}':")
            print(json.dumps(results, indent=2, default=str))
        else:
            # Get results for all metrics
            for metric in service.metrics.keys():
                results = service.get_test_results(campaign_id, metric)
                print(f"\nResults for metric '{metric}':")
                print(json.dumps(results, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")

def export_results(campaign_id: str):
    """Export A/B test results to a report."""
    try:
        service = ABTestingService()
        output_path = service.export_test_results(campaign_id)
        
        if output_path:
            print(f"\nResults exported to: {output_path}")
            
            # Print summary
            with open(output_path, 'r') as f:
                report = json.load(f)
                print("\nTest Summary:")
                print(json.dumps(report['summary'], indent=2))
        else:
            print("Failed to export results")
        
    except Exception as e:
        logger.error(f"Error exporting results: {e}")

def main():
    parser = argparse.ArgumentParser(description="A/B Testing Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List campaigns command
    subparsers.add_parser("list-campaigns", help="List all campaigns")
    
    # List templates command
    subparsers.add_parser("list-templates", help="List all templates")
    
    # Create test command
    create_parser = subparsers.add_parser("create-test", help="Create a new A/B test")
    create_parser.add_argument("campaign_id", type=str, help="Campaign ID (UUID)")
    create_parser.add_argument("template_ids", type=str, nargs="+", help="Template IDs (UUIDs) to test")
    create_parser.add_argument("--duration", type=int, default=7, help="Test duration in days")
    create_parser.add_argument("--sample-size", type=int, default=100, help="Sample size per variant")
    
    # Get results command
    results_parser = subparsers.add_parser("get-results", help="Get A/B test results")
    results_parser.add_argument("campaign_id", type=str, help="Campaign ID (UUID)")
    results_parser.add_argument("--metric", help="Specific metric to get results for")
    
    # Export results command
    export_parser = subparsers.add_parser("export-results", help="Export A/B test results")
    export_parser.add_argument("campaign_id", type=str, help="Campaign ID (UUID)")
    
    args = parser.parse_args()
    
    if args.command == "list-campaigns":
        list_campaigns()
    elif args.command == "list-templates":
        list_templates()
    elif args.command == "create-test":
        create_test(args.campaign_id, args.template_ids, args.duration, args.sample_size)
    elif args.command == "get-results":
        get_results(args.campaign_id, args.metric)
    elif args.command == "export-results":
        export_results(args.campaign_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 