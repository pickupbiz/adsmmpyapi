"""
Email and notification service for workflow approvals.

Supports:
- Email notifications for PO approvals
- Material movement notifications  
- Escalation alerts
- Async email sending
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration."""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@aerospace-materials.com"
    from_name: str = "Aerospace Materials System"
    use_tls: bool = True
    enabled: bool = False  # Disabled by default, enable in production


# Get config from settings if available
try:
    email_config = EmailConfig(
        smtp_host=getattr(settings, 'SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=getattr(settings, 'SMTP_PORT', 587),
        smtp_user=getattr(settings, 'SMTP_USER', ''),
        smtp_password=getattr(settings, 'SMTP_PASSWORD', ''),
        from_email=getattr(settings, 'FROM_EMAIL', 'noreply@aerospace-materials.com'),
        from_name=getattr(settings, 'FROM_NAME', 'Aerospace Materials System'),
        enabled=getattr(settings, 'EMAIL_ENABLED', False)
    )
except Exception:
    email_config = EmailConfig()


class NotificationType:
    """Notification type constants."""
    PO_SUBMITTED = "po_submitted"
    PO_APPROVED = "po_approved"
    PO_REJECTED = "po_rejected"
    PO_PENDING_APPROVAL = "po_pending_approval"
    
    MATERIAL_RECEIVED = "material_received"
    MATERIAL_INSPECTION_REQUIRED = "material_inspection_required"
    MATERIAL_INSPECTION_PASSED = "material_inspection_passed"
    MATERIAL_INSPECTION_FAILED = "material_inspection_failed"
    MATERIAL_ISSUED = "material_issued"
    
    WORKFLOW_APPROVAL_REQUIRED = "workflow_approval_required"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_ESCALATED = "workflow_escalated"
    
    HIGH_VALUE_APPROVAL = "high_value_approval"


class EmailTemplates:
    """Email templates for different notification types."""
    
    @staticmethod
    def po_pending_approval(
        po_number: str,
        total_amount: float,
        currency: str,
        supplier_name: str,
        requestor_name: str,
        approver_name: str,
        approval_url: str = ""
    ) -> Dict[str, str]:
        """Generate PO approval request email."""
        subject = f"[Action Required] PO {po_number} Pending Your Approval"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a5276;">Purchase Order Approval Required</h2>
                
                <p>Dear {approver_name},</p>
                
                <p>A Purchase Order requires your approval:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PO Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{po_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Supplier</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{supplier_name}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Amount</td>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #1a5276;">{currency} {total_amount:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Requested By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{requestor_name}</td>
                    </tr>
                </table>
                
                <p>Please review and take action on this request.</p>
                
                {f'<p><a href="{approval_url}" style="background-color: #1a5276; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Review PO</a></p>' if approval_url else ''}
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from the Aerospace Materials Management System.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Purchase Order Approval Required
        
        Dear {approver_name},
        
        A Purchase Order requires your approval:
        
        PO Number: {po_number}
        Supplier: {supplier_name}
        Total Amount: {currency} {total_amount:,.2f}
        Requested By: {requestor_name}
        
        Please login to the system to review and take action.
        
        --
        Aerospace Materials Management System
        """
        
        return {"subject": subject, "html": body_html, "text": body_text}
    
    @staticmethod
    def po_approved(
        po_number: str,
        total_amount: float,
        currency: str,
        approver_name: str,
        requestor_name: str,
        comments: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate PO approved notification email."""
        subject = f"[Approved] PO {po_number} Has Been Approved"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #27ae60;">✓ Purchase Order Approved</h2>
                
                <p>Dear {requestor_name},</p>
                
                <p>Your Purchase Order has been approved:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PO Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{po_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Amount</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{currency} {total_amount:,.2f}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Approved By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{approver_name}</td>
                    </tr>
                    {f'<tr><td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Comments</td><td style="padding: 10px; border: 1px solid #ddd;">{comments}</td></tr>' if comments else ''}
                </table>
                
                <p>The PO is now ready to be sent to the supplier.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from the Aerospace Materials Management System.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Purchase Order Approved
        
        Dear {requestor_name},
        
        Your Purchase Order has been approved:
        
        PO Number: {po_number}
        Total Amount: {currency} {total_amount:,.2f}
        Approved By: {approver_name}
        {f'Comments: {comments}' if comments else ''}
        
        The PO is now ready to be sent to the supplier.
        
        --
        Aerospace Materials Management System
        """
        
        return {"subject": subject, "html": body_html, "text": body_text}
    
    @staticmethod
    def po_rejected(
        po_number: str,
        total_amount: float,
        currency: str,
        approver_name: str,
        requestor_name: str,
        rejection_reason: str
    ) -> Dict[str, str]:
        """Generate PO rejected notification email."""
        subject = f"[Rejected] PO {po_number} Has Been Rejected"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c;">✗ Purchase Order Rejected</h2>
                
                <p>Dear {requestor_name},</p>
                
                <p>Your Purchase Order has been rejected:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PO Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{po_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Total Amount</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{currency} {total_amount:,.2f}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Rejected By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{approver_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Reason</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #e74c3c;">{rejection_reason}</td>
                    </tr>
                </table>
                
                <p>Please review the feedback and make necessary changes before resubmitting.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from the Aerospace Materials Management System.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Purchase Order Rejected
        
        Dear {requestor_name},
        
        Your Purchase Order has been rejected:
        
        PO Number: {po_number}
        Total Amount: {currency} {total_amount:,.2f}
        Rejected By: {approver_name}
        Reason: {rejection_reason}
        
        Please review the feedback and make necessary changes before resubmitting.
        
        --
        Aerospace Materials Management System
        """
        
        return {"subject": subject, "html": body_html, "text": body_text}
    
    @staticmethod
    def material_inspection_required(
        grn_number: str,
        po_number: str,
        material_name: str,
        quantity: float,
        unit: str,
        inspector_name: str,
        received_by: str
    ) -> Dict[str, str]:
        """Generate material inspection required email."""
        subject = f"[QA Action Required] Material Inspection - GRN {grn_number}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f39c12;">⚠ Material Inspection Required</h2>
                
                <p>Dear {inspector_name},</p>
                
                <p>Material has been received and requires your inspection:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">GRN Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{grn_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">PO Number</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{po_number}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Material</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{material_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Quantity</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{quantity} {unit}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Received By</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{received_by}</td>
                    </tr>
                </table>
                
                <p>Please proceed with the quality inspection.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from the Aerospace Materials Management System.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Material Inspection Required
        
        Dear {inspector_name},
        
        Material has been received and requires your inspection:
        
        GRN Number: {grn_number}
        PO Number: {po_number}
        Material: {material_name}
        Quantity: {quantity} {unit}
        Received By: {received_by}
        
        Please proceed with the quality inspection.
        
        --
        Aerospace Materials Management System
        """
        
        return {"subject": subject, "html": body_html, "text": body_text}
    
    @staticmethod
    def workflow_escalation(
        workflow_type: str,
        reference_number: str,
        amount: float,
        currency: str,
        original_approver: str,
        escalated_to: str,
        pending_since: str
    ) -> Dict[str, str]:
        """Generate workflow escalation email."""
        subject = f"[Escalation] {workflow_type} {reference_number} Requires Attention"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c;">🔺 Workflow Escalation</h2>
                
                <p>Dear {escalated_to},</p>
                
                <p>A workflow approval has been escalated to you due to no action taken:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Type</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{workflow_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Reference</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{reference_number}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Amount</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{currency} {amount:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Original Approver</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{original_approver}</td>
                    </tr>
                    <tr style="background-color: #fff3cd;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Pending Since</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #e74c3c;">{pending_since}</td>
                    </tr>
                </table>
                
                <p>Please take action as soon as possible.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">This is an automated message from the Aerospace Materials Management System.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Workflow Escalation
        
        Dear {escalated_to},
        
        A workflow approval has been escalated to you:
        
        Type: {workflow_type}
        Reference: {reference_number}
        Amount: {currency} {amount:,.2f}
        Original Approver: {original_approver}
        Pending Since: {pending_since}
        
        Please take action as soon as possible.
        
        --
        Aerospace Materials Management System
        """
        
        return {"subject": subject, "html": body_html, "text": body_text}


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, config: EmailConfig = email_config):
        self.config = config
        self._notification_log: List[Dict[str, Any]] = []
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email notification.
        
        Returns True if sent successfully, False otherwise.
        In development mode (enabled=False), logs the email instead of sending.
        """
        # Log the notification
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "to": to_email,
            "cc": cc,
            "subject": subject,
            "sent": False,
            "error": None
        }
        
        if not self.config.enabled:
            logger.info(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            log_entry["sent"] = True
            log_entry["note"] = "Email disabled - logged only"
            self._notification_log.append(log_entry)
            return True
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ", ".join(cc)
            
            # Attach both text and HTML versions
            msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(self.config.from_email, recipients, msg.as_string())
            
            log_entry["sent"] = True
            logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            log_entry["error"] = str(e)
            logger.error(f"Failed to send email to {to_email}: {e}")
            self._notification_log.append(log_entry)
            return False
        
        self._notification_log.append(log_entry)
        return True
    
    def notify_po_pending_approval(
        self,
        approver_email: str,
        approver_name: str,
        po_number: str,
        total_amount: float,
        currency: str,
        supplier_name: str,
        requestor_name: str,
        approval_url: str = ""
    ) -> bool:
        """Send PO pending approval notification."""
        template = EmailTemplates.po_pending_approval(
            po_number=po_number,
            total_amount=total_amount,
            currency=currency,
            supplier_name=supplier_name,
            requestor_name=requestor_name,
            approver_name=approver_name,
            approval_url=approval_url
        )
        return self.send_email(
            to_email=approver_email,
            subject=template["subject"],
            body_html=template["html"],
            body_text=template["text"]
        )
    
    def notify_po_approved(
        self,
        requestor_email: str,
        requestor_name: str,
        po_number: str,
        total_amount: float,
        currency: str,
        approver_name: str,
        comments: Optional[str] = None
    ) -> bool:
        """Send PO approved notification."""
        template = EmailTemplates.po_approved(
            po_number=po_number,
            total_amount=total_amount,
            currency=currency,
            approver_name=approver_name,
            requestor_name=requestor_name,
            comments=comments
        )
        return self.send_email(
            to_email=requestor_email,
            subject=template["subject"],
            body_html=template["html"],
            body_text=template["text"]
        )
    
    def notify_po_rejected(
        self,
        requestor_email: str,
        requestor_name: str,
        po_number: str,
        total_amount: float,
        currency: str,
        approver_name: str,
        rejection_reason: str
    ) -> bool:
        """Send PO rejected notification."""
        template = EmailTemplates.po_rejected(
            po_number=po_number,
            total_amount=total_amount,
            currency=currency,
            approver_name=approver_name,
            requestor_name=requestor_name,
            rejection_reason=rejection_reason
        )
        return self.send_email(
            to_email=requestor_email,
            subject=template["subject"],
            body_html=template["html"],
            body_text=template["text"]
        )
    
    def notify_material_inspection_required(
        self,
        inspector_email: str,
        inspector_name: str,
        grn_number: str,
        po_number: str,
        material_name: str,
        quantity: float,
        unit: str,
        received_by: str
    ) -> bool:
        """Send material inspection required notification."""
        template = EmailTemplates.material_inspection_required(
            grn_number=grn_number,
            po_number=po_number,
            material_name=material_name,
            quantity=quantity,
            unit=unit,
            inspector_name=inspector_name,
            received_by=received_by
        )
        return self.send_email(
            to_email=inspector_email,
            subject=template["subject"],
            body_html=template["html"],
            body_text=template["text"]
        )
    
    def notify_workflow_escalation(
        self,
        escalated_to_email: str,
        escalated_to_name: str,
        workflow_type: str,
        reference_number: str,
        amount: float,
        currency: str,
        original_approver: str,
        pending_since: str
    ) -> bool:
        """Send workflow escalation notification."""
        template = EmailTemplates.workflow_escalation(
            workflow_type=workflow_type,
            reference_number=reference_number,
            amount=amount,
            currency=currency,
            original_approver=original_approver,
            escalated_to=escalated_to_name,
            pending_since=pending_since
        )
        return self.send_email(
            to_email=escalated_to_email,
            subject=template["subject"],
            body_html=template["html"],
            body_text=template["text"]
        )
    
    def get_notification_log(self) -> List[Dict[str, Any]]:
        """Get the notification log (useful for debugging/testing)."""
        return self._notification_log.copy()


# Global notification service instance
notification_service = NotificationService()
