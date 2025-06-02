from locust import HttpUser, task, between

class AffiliateSystemUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def get_prospects(self):
        self.client.get("/prospects/")
    
    @task
    def create_prospect(self):
        self.client.post("/prospects/", json={
            "email": f"test{self.environment.runner.user_count}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "company": "Test Corp",
            "website": "https://test.com",
            "lead_source": "locust",
            "consent_given": True
        })
    
    @task
    def start_campaign(self):
        self.client.post("/campaigns/550e8400-e29b-41d4-a716-446655440000/start")