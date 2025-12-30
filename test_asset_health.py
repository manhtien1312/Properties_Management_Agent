"""
Test script for the Asset Health & Refresh Tracker
"""

from src.database.database import SessionLocal
from src.agent.asset_assignment_agent import get_employee_lifecycle_agent
from src.agent.tools import EmployeeLifecycleTools


def test_asset_refresh_tracking():
    """Test asset refresh tracking"""
    
    db = SessionLocal()
    
    print("=" * 70)
    print("ASSET HEALTH & REFRESH TRACKER - TEST")
    print("=" * 70)
    
    try:
        agent = get_employee_lifecycle_agent()
        
        # Test with 3-year threshold
        print("\n1️⃣ Testing Asset Refresh Tracking (3-year threshold):")
        print("-" * 70)
        
        result = agent.track_asset_health(db, age_threshold_years=3)
        
        if result.get("success"):
            print(f"✓ Total Assets: {result['total_assets']}")
            print(f"✓ Assets for Refresh: {result['refresh_count']}")
            print(f"✓ Total Refresh Value: ${result['total_refresh_value']:,.2f}")
            print(f"✓ Age Threshold: {result['age_threshold_years']} years")
            
            if result["refresh_assets"]:
                print(f"\nAssets Marked for Refresh (Top 5):")
                for i, asset in enumerate(result["refresh_assets"][:5], 1):
                    print(f"  {i}. {asset['asset_tag']} ({asset['device_type']})")
                    print(f"     - Brand/Model: {asset['brand']} {asset['model']}")
                    print(f"     - Age: {asset['age_years']} years")
                    print(f"     - Condition: {asset['condition']}")
                    print(f"     - Status: {asset['refresh_status']}")
                    print(f"     - Value: ${asset['current_value']:.2f}")
                
                if len(result["refresh_assets"]) > 5:
                    print(f"  ... and {len(result['refresh_assets']) - 5} more assets")
        else:
            print(f"✗ Error: {result.get('error')}")
        
        # Test health summary
        print(f"\n{'─' * 70}")
        print("\n2️⃣ Testing Asset Health Summary:")
        print("-" * 70)
        
        summary_result = EmployeeLifecycleTools.get_asset_health_summary(db)
        
        if summary_result.get("success"):
            summary = summary_result.get("health_summary", {})
            print(f"✓ Total Assets: {summary_result['total_assets']}")
            
            if "age_statistics" in summary:
                age_stats = summary["age_statistics"]
                print(f"\nAge Statistics:")
                print(f"  - Average Age: {age_stats.get('average_age_years', 'N/A')} years")
                print(f"  - Oldest Asset: {age_stats.get('oldest_asset_years', 'N/A')} years")
                print(f"  - Newest Asset: {age_stats.get('newest_asset_years', 'N/A')} years")
            
            if "age_categories" in summary:
                age_cat = summary["age_categories"]
                print(f"\nAge Categories:")
                print(f"  - New (0-1 years): {age_cat.get('new_0_1_years', 0)} assets")
                print(f"  - Mid-Age (1-3 years): {age_cat.get('mid_age_1_3_years', 0)} assets")
                print(f"  - Old (3+ years): {age_cat.get('old_over_3_years', 0)} assets")
            
            if "condition_distribution" in summary:
                print(f"\nCondition Distribution:")
                for condition, count in summary["condition_distribution"].items():
                    print(f"  - {condition.title()}: {count} assets")
            
            if "device_type_distribution" in summary:
                print(f"\nDevice Type Distribution:")
                for device_type, count in summary["device_type_distribution"].items():
                    print(f"  - {device_type.title()}: {count} assets")
            
            print(f"\nFinancial Metrics:")
            print(f"  - Total Asset Value: ${summary.get('total_asset_value', 0):,.2f}")
            print(f"  - Depreciation: {summary.get('depreciation_percent', 0)}%")
        else:
            print(f"✗ Error: {summary_result.get('error')}")
        
        # Test comprehensive health report
        print(f"\n{'─' * 70}")
        print("\n3️⃣ Testing Comprehensive Health Report:")
        print("-" * 70)
        
        report = agent.get_asset_health_report(db)
        
        if report.get("success"):
            refresh_summary = report.get("refresh_summary", {})
            print(f"✓ Total Assets: {report['total_assets']}")
            print(f"\nRefresh Summary:")
            print(f"  - Total for Refresh: {refresh_summary.get('total_for_refresh', 0)}")
            print(f"  - Urgent (5+ years): {refresh_summary.get('urgent_refresh', 0)}")
            print(f"  - Recommended (3-5 years): {refresh_summary.get('recommended_refresh', 0)}")
            print(f"  - Total Refresh Value: ${refresh_summary.get('total_refresh_value', 0):,.2f}")
            
            if report.get("urgent_assets"):
                print(f"\nUrgent Assets (5+ years old) - Top 3:")
                for i, asset in enumerate(report["urgent_assets"][:3], 1):
                    print(f"  {i}. {asset['asset_tag']}: {asset['age_years']} years old")
            
            if report.get("recommended_assets"):
                print(f"\nRecommended Assets (3-5 years old) - Top 3:")
                for i, asset in enumerate(report["recommended_assets"][:3], 1):
                    print(f"  {i}. {asset['asset_tag']}: {asset['age_years']} years old")
        else:
            print(f"✗ Error: {report.get('error')}")
        
        print(f"\n{'=' * 70}")
        print("TEST COMPLETED SUCCESSFULLY")
        print(f"{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_age_range_filtering():
    """Test filtering assets by age range"""
    
    db = SessionLocal()
    
    print("=" * 70)
    print("ASSET AGE RANGE FILTERING - TEST")
    print("=" * 70)
    
    try:
        # Test different age ranges
        age_ranges = [
            (0, 1, "New Assets (0-1 years)"),
            (1, 3, "Mid-Age Assets (1-3 years)"),
            (3, 10, "Old Assets (3-10 years)")
        ]
        
        for min_years, max_years, label in age_ranges:
            print(f"\n{label}:")
            print("-" * 70)
            
            result = EmployeeLifecycleTools.get_assets_by_age_range(
                db,
                min_years=min_years,
                max_years=max_years
            )
            
            if result.get("success"):
                print(f"✓ Assets Found: {result['asset_count']}")
                
                if result["assets"]:
                    for i, asset in enumerate(result["assets"][:3], 1):
                        print(f"  {i}. {asset['asset_tag']}: {asset['age_years']} years")
                    
                    if len(result["assets"]) > 3:
                        print(f"  ... and {len(result['assets']) - 3} more")
            else:
                print(f"✗ Error: {result.get('error')}")
        
        print(f"\n{'=' * 70}")
        print("TEST COMPLETED")
        print(f"{'=' * 70}\n")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    # Run asset refresh tracking test
    test_asset_refresh_tracking()
    
    # Run age range filtering test
    test_age_range_filtering()
