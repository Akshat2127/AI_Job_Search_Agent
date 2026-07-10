from backend.app.models.job import Job

def build_cover_letter(job: Job) -> str:
    return f"""Hi {job.company} team,

I am excited to apply for the {job.title} role. My background includes senior business systems analysis, stakeholder management, requirements documentation, process mapping, UAT support, and implementation support for healthcare/claims and workflow systems.

I have led work across digital claim submission, authentication modernization, ServiceNow message-center workflows, SQL-supported data migration, process design, and training/adoption support. This experience aligns well with the responsibilities described for this role.

Thank you for your consideration.

Best,
Gurbani Sharma
"""

def build_recruiter_message(job: Job) -> str:
    return f"""Hi, I came across the {job.title} opening at {job.company}. My background is in Senior Business Systems Analysis with healthcare claims, ServiceNow workflow, UAT, requirements, stakeholder management, SQL, and process mapping experience. I would appreciate the opportunity to be considered. Thank you!"""
