import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

EMAIL_TEMPLATES = {
    "interview_invitation": {
        "name": "Interview Invitation",
        "subject": "Interview Invitation: {role} at HireSwift",
        "body": """Dear {candidate_name},

Thank you for your application for the {role} position. We were impressed by your background and experience, particularly your work with {key_skills}.

We would like to invite you for a 45-minute technical conversation with our engineering team to discuss your past projects and learn more about your career goals.

Please let us know your availability over the next 3-4 business days.

Best regards,
Hiring Team
HireSwift ATS"""
    },
    "shortlist_notification": {
        "name": "Shortlist Notification",
        "subject": "Application Update: You have been shortlisted for {role}",
        "body": """Dear {candidate_name},

Great news! Following an initial review of your profile and qualifications, your application for the {role} role has been shortlisted.

Our recruitment team is currently aligning schedules for the next evaluation round. We will reach out shortly with further details and next steps.

Best regards,
Talent Acquisition Team
HireSwift ATS"""
    },
    "application_update": {
        "name": "Application Update",
        "subject": "Update on your application for {role}",
        "body": """Dear {candidate_name},

Thank you for your interest in HireSwift and for taking the time to apply for the {role} position.

We wanted to inform you that our hiring team is actively reviewing submissions. We will keep you updated as decisions are finalized for your stage.

Best regards,
Hiring Operations
HireSwift ATS"""
    },
    "custom": {
        "name": "Custom Message",
        "subject": "Notice regarding your application at HireSwift",
        "body": """Dear {candidate_name},

We are writing regarding your recent application for {role}.

[Your custom message here]

Sincerely,
HireSwift Recruiting"""
    }
}

def render_email(template_key: str, candidate_name: str, email: str, role: str = "Software Engineer", key_skills: str = "relevant technologies") -> Dict[str, str]:
    tmpl = EMAIL_TEMPLATES.get(template_key, EMAIL_TEMPLATES["interview_invitation"])
    subject = tmpl["subject"].format(candidate_name=candidate_name, role=role)
    body = tmpl["body"].format(candidate_name=candidate_name, role=role, key_skills=key_skills)
    return {
        "to_email": email,
        "candidate_name": candidate_name,
        "subject": subject,
        "body": body,
        "template_name": tmpl["name"]
    }

def process_bulk_email_queue(
    items: List[Dict[str, Any]],
    template_key: str,
    role: str = "Software Engineer",
    dry_run: bool = True,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = 587,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes email queue.
    DEFAULT is strictly DRY RUN.
    Never logs passwords or credentials.
    """
    queue = []
    has_valid_smtp = bool(smtp_host and smtp_port and smtp_user and smtp_password)
    
    for item in items:
        cand_name = item.get("name", "Candidate")
        to_email = item.get("email", "")
        skills = item.get("skills", "your core technical stack")
        
        rendered = render_email(
            template_key=template_key,
            candidate_name=cand_name,
            email=to_email,
            role=role,
            key_skills=skills
        )
        
        # Email format validation
        is_valid_email = bool(to_email and re.match(r"[^@]+@[^@]+\.[^@]+", to_email.strip()))
        
        status_msg = "Prepared (DRY RUN - No email sent)"
        delivered = False
        
        if not is_valid_email:
            status_msg = "Invalid recipient email address"
        elif not dry_run:
            if not has_valid_smtp:
                status_msg = "SMTP not configured — Live dispatch blocked. Operation treated as Dry Run."
            else:
                # Live dispatch attempt
                try:
                    # In real execution smtplib would connect here
                    # For safety, protect against bad hosts
                    server = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    msg = MIMEText(rendered["body"])
                    msg["Subject"] = rendered["subject"]
                    msg["From"] = smtp_user
                    msg["To"] = to_email
                    server.send_message(msg)
                    server.quit()
                    delivered = True
                    status_msg = "Sent successfully via SMTP"
                except Exception as e:
                    # Never print password in error
                    clean_err = str(e).replace(smtp_password or "", "******")
                    status_msg = f"SMTP dispatch failed: {clean_err}"

        queue.append({
            "candidate_id": item.get("id"),
            "candidate_name": cand_name,
            "to_email": to_email,
            "subject": rendered["subject"],
            "body": rendered["body"],
            "status": status_msg,
            "delivered": delivered,
            "dry_run": dry_run or not has_valid_smtp
        })

    return {
        "mode": "DRY RUN" if (dry_run or not has_valid_smtp) else "LIVE",
        "smtp_configured": has_valid_smtp,
        "total_queued": len(queue),
        "total_delivered": sum(1 for q in queue if q["delivered"]),
        "queue": queue
    }
