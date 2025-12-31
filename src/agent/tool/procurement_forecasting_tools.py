"""
Procurement Forecasting Tools
Combines asset health tracking and churn predictions to forecast asset procurement needs
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ProcurementForecastingTools:
    """Tools for forecasting asset procurement needs"""
    
    @classmethod
    def calculate_asset_demand(
        cls,
        db: Session,
        forecast_months: int = 6
    ) -> Dict[str, Any]:
        """
        Calculate total asset demand based on:
        1. Assets needing refresh (from Asset Health Tracker)
        2. Assets needed for churn replacement (predicted resignations)
        
        Args:
            db: Database session
            forecast_months: Number of months to forecast (default 6 for churn prediction window)
            
        Returns:
            Dictionary with asset demand breakdown
        """
        from src.agent.tool.tools import EmployeeLifecycleTools
        from src.agent.tool.churn_prediction_tools import ChurnPredictionTools
        from src.database.models import Asset, Employee
        
        logger.info(f"Calculating asset demand for {forecast_months} months")
        
        # 1. Get assets needing refresh (>3 years old)
        refresh_result = EmployeeLifecycleTools.get_assets_for_refresh(db)
        
        if not refresh_result.get('success'):
            return {
                'success': False,
                'error': 'Failed to get assets for refresh'
            }
        
        refresh_assets = refresh_result.get('assets_for_refresh', [])
        
        refresh_by_type = defaultdict(lambda: {'urgent': 0, 'recommended': 0, 'assets': []})
        
        for asset in refresh_assets:
            device_type = asset['device_type']
            age_years = asset['age_years']
            
            if age_years >= 5:
                refresh_by_type[device_type]['urgent'] += 1
            else:
                refresh_by_type[device_type]['recommended'] += 1
            
            refresh_by_type[device_type]['assets'].append({
                'asset_id': asset['asset_id'],
                'asset_tag': asset['asset_tag'],
                'age_years': age_years,
                'assigned_to': asset['assigned_to'],
                'priority': 'URGENT' if age_years >= 5 else 'RECOMMENDED'
            })
        
        # 2. Get high-risk employees (likely to resign within 6 months)
        high_risk_employees = ChurnPredictionTools.get_high_risk_employees(db, min_probability=0.7)
        
        churn_assets_by_type = defaultdict(int)
        churn_employees_detail = []
        
        if high_risk_employees.get('success'):
            for emp in high_risk_employees.get('high_risk_employees', []):
                employee_id = emp['employee_id']
                
                # Get assets assigned to this employee
                assigned_assets = db.query(Asset).filter(
                    Asset.assigned_to == employee_id,
                    Asset.status == 'assigned'
                ).all()
                
                employee_assets = []
                for asset in assigned_assets:
                    churn_assets_by_type[asset.device_type] += 1
                    employee_assets.append({
                        'asset_id': asset.asset_id,
                        'asset_tag': asset.asset_tag,
                        'device_type': asset.device_type,
                        'brand': asset.brand,
                        'model': asset.model
                    })
                
                churn_employees_detail.append({
                    'employee_id': employee_id,
                    'employee_name': emp['employee_name'],
                    'churn_probability': emp['probability'],
                    'assets': employee_assets,
                    'asset_count': len(employee_assets)
                })
        
        # 3. Calculate total demand by device type
        total_demand_by_type = defaultdict(lambda: {
            'refresh_needed': 0,
            'churn_replacement': 0,
            'total_demand': 0
        })
        
        for device_type, data in refresh_by_type.items():
            total_demand_by_type[device_type]['refresh_needed'] = data['urgent'] + data['recommended']
        
        for device_type, count in churn_assets_by_type.items():
            total_demand_by_type[device_type]['churn_replacement'] = count
        
        for device_type in total_demand_by_type:
            total_demand_by_type[device_type]['total_demand'] = (
                total_demand_by_type[device_type]['refresh_needed'] +
                total_demand_by_type[device_type]['churn_replacement']
            )
        
        return {
            'success': True,
            'forecast_period_months': forecast_months,
            'forecast_date': datetime.now().isoformat(),
            'refresh_assets': {
                'total_count': len(refresh_assets),
                'by_type': dict(refresh_by_type),
                'summary': {
                    device_type: {
                        'urgent': data['urgent'],
                        'recommended': data['recommended'],
                        'total': data['urgent'] + data['recommended']
                    }
                    for device_type, data in refresh_by_type.items()
                }
            },
            'churn_replacement': {
                'high_risk_employees': len(churn_employees_detail),
                'total_assets_at_risk': sum(churn_assets_by_type.values()),
                'by_type': dict(churn_assets_by_type),
                'employee_details': churn_employees_detail
            },
            'total_demand': dict(total_demand_by_type)
        }
    
    @classmethod
    def get_procurement_recommendations(
        cls,
        db: Session,
        forecast_months: int = 6,
        safety_stock_percent: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate procurement recommendations based on demand vs available stock
        
        Args:
            db: Database session
            forecast_months: Number of months to forecast
            safety_stock_percent: Additional buffer stock (e.g., 0.2 = 20% extra)
            
        Returns:
            Dictionary with procurement recommendations
        """
        from src.database.models import Asset
        
        logger.info("Generating procurement recommendations")
        
        # 1. Calculate demand
        demand_analysis = cls.calculate_asset_demand(db, forecast_months)
        
        if not demand_analysis.get('success'):
            return demand_analysis
        
        # 2. Get available stock by device type
        available_assets = db.query(Asset).filter(
            Asset.status == 'available'
        ).all()
        
        available_by_type = defaultdict(lambda: {'count': 0, 'assets': []})
        
        for asset in available_assets:
            device_type = asset.device_type
            available_by_type[device_type]['count'] += 1
            available_by_type[device_type]['assets'].append({
                'asset_id': asset.asset_id,
                'asset_tag': asset.asset_tag,
                'brand': asset.brand,
                'model': asset.model,
                'condition': asset.condition,
                'age_years': round((datetime.now().date() - asset.purchase_date).days / 365.25, 1)
            })
        
        # 3. Calculate procurement needs
        procurement_recommendations = []
        total_demand = demand_analysis['total_demand']
        
        for device_type, demand_data in total_demand.items():
            total_needed = demand_data['total_demand']
            available_count = available_by_type[device_type]['count']
            
            # Add safety stock buffer
            total_needed_with_buffer = int(total_needed * (1 + safety_stock_percent))
            
            shortage = max(0, total_needed_with_buffer - available_count)
            surplus = max(0, available_count - total_needed_with_buffer)
            
            recommendation = {
                'device_type': device_type,
                'demand_breakdown': {
                    'refresh_needed': demand_data['refresh_needed'],
                    'churn_replacement': demand_data['churn_replacement'],
                    'total_base_demand': total_needed,
                    'safety_buffer': total_needed_with_buffer - total_needed,
                    'total_needed_with_buffer': total_needed_with_buffer
                },
                'inventory': {
                    'available_stock': available_count,
                    'shortage': shortage,
                    'surplus': surplus
                },
                'action_required': shortage > 0,
                'purchase_quantity': shortage,
                'priority': cls._calculate_priority(demand_data, shortage),
                'estimated_timeline': f"{forecast_months} months",
                'recommendation': cls._generate_recommendation_message(
                    device_type, shortage, surplus, demand_data
                )
            }
            
            procurement_recommendations.append(recommendation)
        
        # Sort by priority (highest first)
        procurement_recommendations.sort(
            key=lambda x: (x['action_required'], x['priority'], x['purchase_quantity']),
            reverse=True
        )
        
        # Generate summary message
        urgent_purchases = [r for r in procurement_recommendations if r['action_required']]
        
        if urgent_purchases:
            summary_message = f"⚠️  Procurement needed for {len(urgent_purchases)} device type(s):\n"
            for rec in urgent_purchases:
                summary_message += f"  • {rec['device_type']}: Purchase {rec['purchase_quantity']} units ({rec['priority']} priority)\n"
        else:
            summary_message = "✅ Current inventory is sufficient for forecasted demand."
        
        return {
            'success': True,
            'forecast_period_months': forecast_months,
            'forecast_date': datetime.now().isoformat(),
            'safety_stock_percent': safety_stock_percent,
            'summary': {
                'total_device_types': len(procurement_recommendations),
                'types_needing_procurement': len(urgent_purchases),
                'total_units_to_purchase': sum(r['purchase_quantity'] for r in urgent_purchases),
                'inventory_sufficient': len(urgent_purchases) == 0
            },
            'summary_message': summary_message,
            'recommendations': procurement_recommendations,
            'demand_details': demand_analysis,
            'available_inventory': {
                device_type: data['count']
                for device_type, data in available_by_type.items()
            }
        }
    
    @classmethod
    def _calculate_priority(cls, demand_data: Dict, shortage: int) -> str:
        """Calculate priority level for procurement"""
        if shortage == 0:
            return "NONE"
        
        # High priority if urgent refresh needed or significant shortage
        urgent_refresh = demand_data.get('refresh_needed', 0)
        total_demand = demand_data.get('total_demand', 0)
        
        if urgent_refresh > 0 or shortage >= 5:
            return "HIGH"
        elif shortage >= 2 or total_demand >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    @classmethod
    def _generate_recommendation_message(
        cls,
        device_type: str,
        shortage: int,
        surplus: int,
        demand_data: Dict
    ) -> str:
        """Generate human-readable recommendation message"""
        if shortage > 0:
            reasons = []
            if demand_data['refresh_needed'] > 0:
                reasons.append(f"{demand_data['refresh_needed']} aging assets need replacement")
            if demand_data['churn_replacement'] > 0:
                reasons.append(f"{demand_data['churn_replacement']} assets at risk due to employee churn")
            
            reason_text = " and ".join(reasons)
            return f"Purchase {shortage} {device_type}(s) to meet demand. {reason_text}."
        
        elif surplus > 0:
            return f"Inventory sufficient. {surplus} surplus {device_type}(s) available."
        
        else:
            return f"Inventory matches demand for {device_type}."
    
    @classmethod
    def get_procurement_report(
        cls,
        db: Session,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive procurement report
        
        Args:
            db: Database session
            include_details: Include detailed asset and employee information
            
        Returns:
            Comprehensive procurement forecast report
        """
        logger.info("Generating comprehensive procurement report")
        
        # Get recommendations
        recommendations = cls.get_procurement_recommendations(db)
        
        if not recommendations.get('success'):
            return recommendations
        
        # Build report
        report = {
            'success': True,
            'report_date': datetime.now().isoformat(),
            'forecast_period': f"{recommendations['forecast_period_months']} months",
            'executive_summary': {
                'procurement_needed': not recommendations['summary']['inventory_sufficient'],
                'total_units_to_purchase': recommendations['summary']['total_units_to_purchase'],
                'device_types_affected': recommendations['summary']['types_needing_procurement'],
                'summary_message': recommendations['summary_message']
            },
            'recommendations': recommendations['recommendations'],
            'demand_drivers': {
                'aging_assets': {
                    'total': recommendations['demand_details']['refresh_assets']['total_count'],
                    'by_type': recommendations['demand_details']['refresh_assets']['summary']
                },
                'employee_churn': {
                    'high_risk_employees': recommendations['demand_details']['churn_replacement']['high_risk_employees'],
                    'assets_at_risk': recommendations['demand_details']['churn_replacement']['total_assets_at_risk'],
                    'by_type': recommendations['demand_details']['churn_replacement']['by_type']
                }
            },
            'current_inventory': recommendations['available_inventory']
        }
        
        if include_details:
            report['detailed_analysis'] = {
                'aging_assets': recommendations['demand_details']['refresh_assets']['by_type'],
                'churn_employees': recommendations['demand_details']['churn_replacement']['employee_details']
            }
        
        return report
