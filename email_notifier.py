"""
Email Notifier System
====================
Professional email sending system supporting:
- Plain text and HTML
- Jinja2 Templates
- Attachments
- Secure environment variables

Author: nreyes
"""

import smtplib
import os
import logging
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any
from jinja2 import Environment, FileSystemLoader

from email_config import EmailConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailNotifier:
    """
    Main class for sending emails.
    Encapsulates all email sending logic.
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize the notifier.
        
        Args:
            config: Custom configuration. If not provided, uses default EmailConfig().
        """
        self.config = config or EmailConfig()
        self.template_env = self._setup_jinja()
    
    def _setup_jinja(self) -> Environment:
        """Configure Jinja2 environment."""
        current_dir = Path(__file__).parent
        templates_dir = current_dir / 'templates'
        templates_dir.mkdir(exist_ok=True)
        return Environment(loader=FileSystemLoader(str(templates_dir)))
    
    def _get_recipient(self, to_email: Optional[str]) -> Optional[str]:
        """Helper to get recipient email, falling back to default if needed."""
        recipient = to_email or self.config.default_recipient
        if not recipient:
            logger.error("No recipient specified and no default recipient configured.")
        return recipient

    def send_plain_email(
        self,
        subject: str,
        body: str,
        to_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send a plain text email.
        """
        recipient = self._get_recipient(to_email)
        if not recipient:
            return False

        try:
            msg = MIMEText(body, 'plain', self.config.email_charset)
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = recipient
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            return self._send_email(msg, recipient, cc, bcc)
            
        except Exception as e:
            logger.error(f"Error sending plain email: {e}")
            return False
    
    def send_html_email(
        self,
        subject: str,
        html_body: str,
        to_email: Optional[str] = None,
        plain_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an HTML email with an optional plain text fallback.
        """
        recipient = self._get_recipient(to_email)
        if not recipient:
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = recipient
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            if not plain_body:
                plain_body = self._html_to_plain(html_body)
            
            part1 = MIMEText(plain_body, 'plain', self.config.email_charset)
            part2 = MIMEText(html_body, 'html', self.config.email_charset)
            
            msg.attach(part1)
            msg.attach(part2)
            
            return self._send_email(msg, recipient, cc, bcc)
            
        except Exception as e:
            logger.error(f"Error sending HTML email: {e}")
            return False
    
    def send_template_email(
        self,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        to_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email using a Jinja2 template.
        """
        try:
            template = self.template_env.get_template(template_name)
            html_body = template.render(**context)
            plain_body = self._html_to_plain(html_body)
            
            return self.send_html_email(
                subject=subject,
                html_body=html_body,
                to_email=to_email,
                plain_body=plain_body,
                cc=cc,
                bcc=bcc
            )
            
        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return False
    
    def send_email_with_attachment(
        self,
        subject: str,
        body: str,
        attachment_path: str,
        to_email: Optional[str] = None,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email with an attachment.
        """
        recipient = self._get_recipient(to_email)
        if not recipient:
            return False

        try:
            if not os.path.exists(attachment_path):
                logger.error(f"Attachment not found: {attachment_path}")
                return False
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = recipient
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            body_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, body_type, self.config.email_charset))
            
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = os.path.basename(attachment_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
            return self._send_email(msg, recipient, cc, bcc)
            
        except Exception as e:
            logger.error(f"Error sending email with attachment: {e}")
            return False
    
    def _send_email(
        self,
        msg: MIMEMultipart,
        to_email: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Internal method to send the email via SMTP.
        """
        try:
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg, to_addrs=recipients)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
        except smtplib.SMTPAuthenticationError:
            logger.error("Authentication error. Verify your email and password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def _html_to_plain(self, html: str) -> str:
        """
        Convert HTML to plain text.
        """
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()