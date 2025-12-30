"""
Email service for sending notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Optional, Dict, Any
from src.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
        cc_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            cc_emails: List of CC emails
            
        Returns:
            Dictionary with send result
        """
        if not settings.email_enabled:
            logger.info(f"Email disabled. Would send to {to_email}: {subject}")
            return {
                "success": True,
                "message": "Email service disabled (demo mode)",
                "to": to_email,
                "subject": subject
            }
        
        if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from_email:
            logger.warning("Email credentials not configured")
            return {
                "success": False,
                "error": "Email credentials not configured",
                "to": to_email
            }
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from_email
            msg["To"] = to_email
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                
                recipients = [to_email]
                if cc_emails:
                    recipients.extend(cc_emails)
                
                server.sendmail(settings.smtp_from_email, recipients, msg.as_string())
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return {
                "success": True,
                "message": f"Email sent successfully",
                "to": to_email,
                "subject": subject
            }
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }
    
    @staticmethod
    def send_asset_return_notice(
        employee_name: str,
        employee_email: str,
        manager_email: Optional[str],
        resignation_date: str,
        return_due_date: str,
        assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send asset return notice to employee and manager
        
        Args:
            employee_name: Employee name
            employee_email: Employee email
            manager_email: Manager email
            resignation_date: Resignation date
            return_due_date: Asset return due date
            assets: List of assets to return
            
        Returns:
            Dictionary with send results
        """
        
        # Build asset table
        asset_rows = ""
        for asset in assets:
            asset_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{asset['asset_tag']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{asset['device_type'].title()}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{asset['brand']} {asset['model']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{asset['condition']}</td>
            </tr>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #4CAF50; color: white; padding: 10px; text-align: left; }}
                .important {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 15px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Asset Return Notice</h2>
                    <p>{settings.company_name}</p>
                </div>
                
                <div class="content">
                    <p>Dear <strong>{employee_name}</strong>,</p>
                    
                    <p>We are writing to inform you that as per your resignation effective on <strong>{resignation_date}</strong>, 
                    you are required to return the following company assets by <strong>{return_due_date}</strong>.</p>
                    
                    <div class="important">
                        <strong>Important:</strong> Please ensure all assets are returned in good condition. 
                        Failure to return assets by the due date may result in deductions from your final settlement.
                    </div>
                    
                    <h3>Assets to Return:</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Asset Tag</th>
                                <th>Device Type</th>
                                <th>Model</th>
                                <th>Condition</th>
                            </tr>
                        </thead>
                        <tbody>
                            {asset_rows}
                        </tbody>
                    </table>
                    
                    <h3>Return Instructions:</h3>
                    <ul>
                        <li>Please arrange to return all assets to the IT department</li>
                        <li>Ensure all data is backed up and devices are factory reset</li>
                        <li>Return assets in the original packaging if possible</li>
                        <li>Obtain a return receipt from the IT department</li>
                    </ul>
                    
                    <p>If you have any questions about asset return, please contact us at:</p>
                    <ul>
                        <li>Email: {settings.support_email or settings.smtp_from_email}</li>
                        {f'<li>Phone: {settings.company_phone}</li>' if settings.company_phone else ''}
                    </ul>
                    
                    <p>Thank you for your service and cooperation.</p>
                    
                    <p>Best regards,<br/>
                    <strong>HR Department</strong><br/>
                    {settings.company_name}</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    {f'<p>Address: {settings.company_address}</p>' if settings.company_address else ''}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send to employee
        result_employee = EmailService.send_email(
            to_email=employee_email,
            subject=f"Asset Return Notice - Due by {return_due_date}",
            html_body=html_body,
            cc_emails=[manager_email] if manager_email else None
        )
        
        return result_employee
