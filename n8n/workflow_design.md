# n8n Workflow
1. Cron daily 7 AM.
2. Read Gmail job-alert labels.
3. Call JobAgent `/jobs` for new jobs.
4. Call `/analytics/summary`.
5. Email daily shortlist.
6. Optional Google Sheets export.
