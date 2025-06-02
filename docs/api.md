# API Documentation

## Base URL
 `http://localhost:8000`

## Authentication

- **JWT Bearer Token:** Include in `Authorization` header as `Bearer <token>`.

## Endpoints

### **Prospects**

- **POST /prospects/**

    - **Description:** Create a new prospect.
    - **Body:** 
    ```json
    {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Corp",
        "website": "https://example.com",
        "lead_source": "linkedin",
        "consent_given": true
    }
    ```
    - **Response:** 200 OK, prospect details.


- **GET /prospects/**

    - **Description:** List prospects.
    - **Query Params:** skip (int, default=0), limit (int, default=100).
    - **Response:** 200 OK, list of prospects.


- **GET /prospects/{prospect_id}**

    - **Description:** Get a prospect by ID.
    - **Response:** 200 OK, prospect details or 404 Not Found.


- **PUT /prospects/{prospect_id}**

    - **Description:** Update a prospect.
    - **Body:** Partial prospect data.
    - **Response:** 200 OK, updated prospect.


- **POST /prospects/bulk-upload**

    - **Description:** Upload prospects via CSV.
    - **Body:** Form-data with file (CSV).
    - **Response:** 200 OK, upload summary.



### **Templates**

- **POST /templates/**

    - **Description:** Create a message template.
    - **Body:** 
    ```json
    {
        "name": "Welcome Email",
        "subject": "Join Our Affiliate Program",
        "content": "Hi {{first_name}}, ...",
        "message_type": "email"
    }
    ```

    - **Response:** 200 OK, template details.


- **GET /templates/**

    - **Description:** List templates.
    - **Response:** 200 OK, list of templates.


- **GET /templates/{template_id}**

    - **Description:** Get a template by ID.
    - **Response:** 200 OK, template details.


- **PUT /templates/{template_id}**

    - **Description:** Update a template.
    - **Response:** 200 OK, updated template.


- **DELETE /templates/{template_id}**

    - **Description:** Deactivate a template.
    - **Response:** 200 OK, success message.



### **Campaigns**

- **POST /campaigns/**

    - **Description:** Create a campaign.
    - **Body:** 
    ```json
    {
        "name": "Spring Campaign",
        "template_id": "uuid",
        "target_criteria": {"min_score": 70}
    }
    ```

    - **Response:** 200 OK, campaign details.


- **GET /campaigns/**

    - **Description:** List campaigns.
    - **Response:** 200 OK, list of campaigns.


- **GET /campaigns/{campaign_id}**

    - **Description:** Get a campaign by ID.
    - **Response:** 200 OK, campaign details.


- **POST /campaigns/{campaign_id}/start**

    - **Description:** Start a campaign.
    - **Response:** 200 OK, start confirmation.



### **Social Outreach**

- **POST /social/twitter/{prospect_id}**

    - **Description:** Send a Twitter DM.
    - **Body:** {"template_id": "uuid"}
    - **Response:** 200 OK, message ID.


- **POST /social/linkedin/{prospect_id}**

    - **Description:** Send a LinkedIn message.
    - **Body:** {"template_id": "uuid"}
    - **Response:** 200 OK, message ID.



### **Health**

- **GET /health/**
    - **Description:** Check system health.
    - **Response:** 200 OK, {"status": "healthy"}



