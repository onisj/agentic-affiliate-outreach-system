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



### **Twitter API Authentication**

The application supports two types of Twitter API authentication:

1. **Bearer Token (App-Only Authentication)**

   - Used for read-only operations
   - Required for:
     - User profile lookups
     - Search operations
     - Public data access
   - Environment variable: `TWITTER_BEARER_TOKEN`

2. **OAuth 1.0a Authentication**

   - Required for user-specific operations
   - Environment variables:
     - `TWITTER_API_KEY`: Your Twitter API Key
     - `TWITTER_API_SECRET`: Your Twitter API Secret
     - `TWITTER_ACCESS_TOKEN`: User's Access Token
     - `TWITTER_ACCESS_TOKEN_SECRET`: User's Access Token Secret
   - Used for:
     - Sending DMs
     - Posting tweets
     - Accessing private user data

#### **Error Handling**

The API handles various Twitter API errors:

- **Rate Limiting (429)**

  - Returns retry-after time
  - Automatically backs off on subsequent requests

- **Authentication Errors (401)**

  - Invalid or expired tokens
  - Missing credentials

- **Permission Errors (403)**

  - Insufficient permissions
  - User blocking

- **Not Found (404)**

  - User doesn't exist
  - Resource not available

- **Server Errors (5xx)**

  - Twitter service issues
  - Temporary unavailability

#### **Best Practices**

1. **Token Management**

   - Store tokens securely
   - Rotate tokens regularly
   - Use environment variables

2. **Rate Limiting**

   - Implement exponential backoff
   - Cache responses when possible
   - Monitor rate limit headers

3. **Error Handling**

   - Log all API errors
   - Implement retry logic
   - Provide user-friendly error messages

4. **Security**

   - Never expose tokens in logs
   - Use HTTPS for all requests
   - Validate all user input

### **Twitter API Integration Guide**

#### **Setup Instructions**

1. **Create a Twitter Developer Account**

   - Go to [developer.twitter.com](https://developer.twitter.com)
   - Sign up for a developer account
   - Create a new project and app
   - Enable the required API access levels

2. **Configure App Permissions**

   - Enable "Read" access for profile lookups
   - Enable "Write" access for sending DMs
   - Set up OAuth 2.0 settings
   - Configure callback URLs if needed

3. **Environment Setup**

   ```bash
      # Required environment variables
      TWITTER_API_KEY=your_api_key
      TWITTER_API_SECRET=your_api_secret
      TWITTER_BEARER_TOKEN=your_bearer_token
      TWITTER_ACCESS_TOKEN=your_access_token
      TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   ```

#### **API Rate Limits**

1. **App-Only Authentication (Bearer Token)**

   - User lookup: 900 requests/15 minutes
   - Search: 450 requests/15 minutes
   - Tweet lookup: 900 requests/15 minutes

2. **User Authentication (OAuth 1.0a)**

   - DM sending: 1000 requests/24 hours
   - User lookup: 900 requests/15 minutes
   - Tweet posting: 300 requests/3 hours

3. **Rate Limit Headers**

   ```bash
   x-rate-limit-limit: Maximum requests per window
   x-rate-limit-remaining: Remaining requests
   x-rate-limit-reset: Time until limit resets (UTC)
   ```

#### **Troubleshooting Guide**

1. **Common Error Codes**

   ```
   401: Authentication failed
   403: Permission denied
   404: Resource not found
   429: Rate limit exceeded
   500: Twitter server error
   ```

2. **Authentication Issues**
   - Check token expiration
   - Verify API key permissions
   - Ensure correct OAuth flow
   - Validate callback URLs

3. **Rate Limit Issues**
   - Implement exponential backoff
   - Use rate limit headers
   - Cache responses
   - Monitor usage

4. **DM Sending Issues**
   - Verify user follows you
   - Check DM settings
   - Validate message length
   - Ensure proper formatting

#### **Best Practices**

1. **Security**
   - Rotate tokens regularly
   - Use environment variables
   - Implement HTTPS
   - Validate user input
   - Sanitize message content

2. **Performance**
   - Cache user profiles
   - Batch requests when possible
   - Use webhooks for real-time updates
   - Implement retry logic

3. **Monitoring**
   - Track API usage
   - Monitor error rates
   - Log rate limit hits
   - Set up alerts

4. **User Experience**
   - Handle errors gracefully
   - Provide clear feedback
   - Implement fallbacks
   - Cache responses

#### **Example Usage**

1. **Sending a DM**

   ```python
      from app.services.social_service import SocialService
      
      social_service = SocialService()
      result = social_service.send_twitter_dm(
         prospect_id="123",
         user_id="456",
         template="Hello {{first_name}}!",
         prospect_data={"first_name": "John"}
      )
   ```

2. **Handling Rate Limits**

   ```python
      try:
         response = social_service.send_twitter_dm(...)
      except tweepy.TooManyRequests as e:
         retry_after = e.response.headers.get("x-rate-limit-reset")
         # Implement backoff logic
   ```

3. **Error Handling**

   ```python
      try:
         response = social_service.send_twitter_dm(...)
      except tweepy.Unauthorized:
         # Handle authentication error
      except tweepy.Forbidden:
         # Handle permission error
      except tweepy.NotFound:
         # Handle not found error
   ```

#### **Support and Resources**

1. **Official Documentation**
   - [Twitter API v2 Docs](https://developer.twitter.com/en/docs/twitter-api)
   - [OAuth 2.0 Guide](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
   - [Rate Limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits)

2. **Community Resources**
   - [Twitter Developer Forum](https://twittercommunity.com)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/twitter-api)
   - [GitHub Issues](https://github.com/twitterdev/twitter-api-v2-sample-code/issues)

3. **Getting Help**
   - Check error logs
   - Review rate limit headers
   - Test in development environment
   - Contact Twitter Developer Support

## LinkedIn API Integration

### Setup

1. Create a LinkedIn Developer Application:
   - Go to https://www.linkedin.com/developers/
   - Click "Create App"
   - Fill in the required information
   - Note down the Client ID and Client Secret

2. Configure OAuth 2.0:
   - Add the redirect URL: `http://localhost:8000/auth/linkedin/callback`
   - Request the following scopes:
     - `r_liteprofile`
     - `r_emailaddress`
     - `w_member_social`

3. Update your `.env` file with LinkedIn credentials:

```env
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URL=http://localhost:8000/auth/linkedin/callback
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_TOKEN_EXPIRY=5184000  # 60 days in seconds
```

### Authentication

The application supports two authentication methods:

1. OAuth 2.0 Client Credentials Flow:
   - Used for server-to-server API calls
   - Requires client ID and secret
   - Tokens expire after 60 days

2. OAuth 2.0 Authorization Code Flow:
   - Used for user-specific operations
   - Requires user authorization
   - Tokens expire after 60 days

### Rate Limits

LinkedIn API has the following rate limits:

- 100 requests per day for profile data
- 100 messages per day
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

### Error Handling

The application handles the following LinkedIn API errors:

1. Authentication Errors (401):
   - Invalid or expired access token
   - Solution: Refresh the token using `refresh_linkedin_token()`

2. Permission Errors (403):
   - Insufficient scope
   - Solution: Request additional scopes in LinkedIn Developer Console

3. Rate Limit Errors (429):
   - Too many requests
   - Solution: Implement exponential backoff

4. Validation Errors:
   - Invalid URN format
   - Missing required fields
   - Solution: Validate input before sending

### Best Practices

1. Token Management:
   - Store tokens securely
   - Implement token refresh before expiry
   - Use environment variables for credentials

2. Error Handling:
   - Implement retry logic with exponential backoff
   - Log all API errors
   - Handle rate limits gracefully

3. Message Sending:
   - Personalize messages using templates
   - Keep messages under 1000 characters
   - Include clear call-to-action

4. Profile Data:
   - Cache profile data when possible
   - Validate URN format before requests
   - Handle missing fields gracefully

### Example Usage

```python
from app.services.social_service import SocialService

# Initialize service
social_service = SocialService()

# Send LinkedIn message
result = social_service.send_linkedin_message(
    prospect_id="123",
    urn="urn:li:person:456",
    template="Hi {{first_name}}, I noticed you work at {{company}}...",
    prospect_data={
        "first_name": "John",
        "company": "Tech Corp"
    }
)

# Handle response
if result["success"]:
    print(f"Message sent successfully: {result['message_id']}")
else:
    print(f"Error: {result['error']}")
```

### Troubleshooting

1. Authentication Issues:

   - Verify client ID and secret
   - Check token expiration
   - Ensure correct redirect URL

2. Rate Limiting:

   - Monitor rate limit headers
   - Implement request queuing
   - Use bulk operations when possible

3. Message Delivery:

   - Verify message format
   - Check recipient URN
   - Monitor delivery status

4. Profile Access:

   - Verify required scopes
   - Check profile visibility
   - Handle private profiles

### LinkedIn API Features

#### Profile Management

1. **Fetch Profile**

      ```python
      result = social_service.get_linkedin_profile(urn="urn:li:person:123")
      if result["success"]:
         profile = result["profile"]
         print(f"Name: {profile['firstName']} {profile['lastName']}")
         print(f"Headline: {profile['headline']}")
      ```

2. **Profile Fields**

- Basic Info: id, firstName, lastName, headline
- Professional: industry, positions, skills
- Education: educations
- Location: location
- Contact: emailAddress

#### Connection Management

1. **List Connections**

      ```python
      result = social_service.get_linkedin_connections(start=0, count=50)
      if result["success"]:
         connections = result["connections"]
         total = result["total"]
         print(f"Found {total} connections")
      ```

2. **Send Connection Invitation**

      ```python
      result = social_service.send_linkedin_invitation(
         prospect_id="123",
         urn="urn:li:person:456",
         message="I'd like to connect with you..."
      )
      if result["success"]:
         print(f"Invitation sent: {result['invitation_id']}")
      ```

#### Message Analytics

1. **Get Message Analytics**

      ```python
      result = social_service.get_linkedin_analytics(message_id="msg_123")
      if result["success"]:
         analytics = result["analytics"]
         print(f"Views: {analytics['views']}")
         print(f"Clicks: {analytics['clicks']}")
         print(f"Responses: {analytics['responses']}")
      ```

2. **Analytics Metrics**
   - Views: Number of times message was viewed
   - Clicks: Number of link clicks
   - Responses: Number of replies
   - Sent At: Message send timestamp
   - Last Viewed: Last view timestamp

#### Best Practices for New Features

1. **Profile Fetching**
   - Cache profile data
   - Implement rate limiting
   - Handle missing fields
   - Validate URN format

2. **Connection Management**
   - Respect connection limits
   - Personalize invitations
   - Track invitation status
   - Handle connection requests

3. **Analytics**
   - Store analytics data
   - Set up monitoring
   - Track engagement
   - Generate reports

4. **Error Handling**
   - Handle API errors
   - Implement retries
   - Log failures
   - Monitor rate limits

#### Example Workflows

1. **Prospect Research**

   ```python
   # Fetch prospect profile
   profile = social_service.get_linkedin_profile(urn)
   
   # Check connection status
   connections = social_service.get_linkedin_connections()
   is_connected = any(c["id"] == urn for c in connections["connections"])
   
   # Send appropriate message
   if is_connected:
       social_service.send_linkedin_message(...)
   else:
       social_service.send_linkedin_invitation(...)
   ```

2. **Campaign Analytics**

   ```python
   # Get message analytics
   analytics = social_service.get_linkedin_analytics(message_id)
   
   # Calculate engagement rate
   views = analytics["analytics"]["views"]
   responses = analytics["analytics"]["responses"]
   engagement_rate = (responses / views) * 100 if views > 0 else 0
   
   # Track performance
   print(f"Engagement Rate: {engagement_rate}%")
   ```

3. **Connection Growth**

   ```python
   # Get current connections
   connections = social_service.get_linkedin_connections()
   current_count = connections["total"]
   
   # Send invitations to prospects
   for prospect in prospects:
       if not is_connected(prospect["urn"]):
           social_service.send_linkedin_invitation(
               prospect_id=prospect["id"],
               urn=prospect["urn"],
               message=generate_invitation_message(prospect)
           )
   ```

#### Troubleshooting New Features

1. **Profile Fetching Issues**
   - Check URN format
   - Verify API permissions
   - Handle rate limits
   - Cache responses

2. **Connection Problems**
   - Monitor invitation limits
   - Check connection status
   - Handle rejections
   - Track success rate

3. **Analytics Issues**
   - Verify message IDs
   - Check data freshness
   - Handle missing data
   - Implement fallbacks

4. **Performance Optimization**
   - Implement caching
   - Batch requests
   - Use webhooks
   - Monitor usage



