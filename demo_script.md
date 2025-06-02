# Agentic Affiliate Outreach System Demo Script

## Objective
Showcase the system's ability to discover affiliates, send personalized outreach, track responses, and display analytics.

## Setup
- Run `docker-compose up --build`.
- Access Gradio at `http://localhost:7860`.
- Ensure `.env` is configured with API keys.

## Steps
1. **Lead Discovery**
   - Navigate to the Gradio "Social Outreach" tab.
   - Enter a prospect ID (pre-populated from Twitter discovery) and a template ID.
   - Select "Twitter" and send a DM, showing the API response.

2. **Prospect Creation**
   - Go to the "Prospects" tab.
   - Enter sample data (email: `test@example.com`, first_name: "John", etc.).
   - Click "Create Prospect" and show the created prospect in the prospect list.

3. **Campaign Creation and Start**
   - In the "Templates" tab, create an email template (name: "Demo Email", subject: "Join Us", content: "Hi {{first_name}}, ...").
   - Create a campaign via API (POST `/campaigns/` with template ID and `min_score: 70`).
   - In the "Campaigns" tab, enter the campaign ID and click "Start Campaign".
   - Show Celery task logs to confirm outreach messages sent.

4. **Response Handling**
   - Simulate a reply ("Looks great!") by calling `handle_prospect_response` via API or database update.
   - Show the follow-up email sent (check `message_log` table or logs).

5. **Analytics**
   - Navigate to the "Analytics" tab.
   - Click "Refresh Analytics" to display response rate, conversion rate, and message status counts.
   - Highlight KPIs (e.g., 10% response rate).

6. **Landing Page**
   - Open `http://localhost:8000/signup`.
   - Fill out the form and submit, showing the success message.
   - Verify the prospect in the database with `consent_given=True`.

## Notes
- Emphasize GDPR compliance (consent checks, unsubscribe links).
- Highlight scalability (Celery, Redis) and autonomy (automated scoring, responses).
- Show error handling (e.g., invalid email validation).

## Duration
10-15 minutes
