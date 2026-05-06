from locust import HttpUser, task, between


FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJiMzZhYjQxYTczOTJlMTRlNjM1ZmRlM2M2YWYwOWZlYmFhM2YyZDYiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiaWJyYWhpbSBpYnJhaGltIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0o2eTZFQ3V1UFZMUFZsLWhPUmg3bUQzcXJLUk9SNW8yR2t1YVZTRHZQUFMyY1Z6R1p6PXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2FpLWJ1ZGdldC1jb2FjaC1lMmU2NyIsImF1ZCI6ImFpLWJ1ZGdldC1jb2FjaC1lMmU2NyIsImF1dGhfdGltZSI6MTc3Nzc0MTQ4OSwidXNlcl9pZCI6IjJtcmFXM0NDV3RiamRhMmk0Y2k3allsUVRBdDEiLCJzdWIiOiIybXJhVzNDQ1d0YmpkYTJpNGNpN2pZbFFUQXQxIiwiaWF0IjoxNzc3NzQxNDg5LCJleHAiOjE3Nzc3NDUwODksImVtYWlsIjoiYm9iaWJyYWhpbTc3MUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMzM2MzM2NzM4MDMxMzgwNjIwMCJdLCJlbWFpbCI6WyJib2JpYnJhaGltNzcxQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.vqQM_p5aSUm8xaIOgZVeEQTlTNQW8pmEJvH-WI_cgokfYsElZLRzNlGH-F9IlxF2lM3OVRTPqo5iISsSVPVaRTG3eJMlmJeRIDxYGaJTTjaYC3j0Xxw8AENmRo_XAFbfpnSDTjtUfuVDB2jJyGQX3e7CjWWDk4uLwRTS-jwd2nocZ-CjMtLphS0hywYeWt9uWm82SDht664v-bo2rxy8BzUC8-Tm9JgnLvRUiLMbiGBCWLw81zUPwQBuyDSuauDTwzlmZ-wYWztLDdcnlOPdD_FH5qEEjMaQ5C3yrbQIycSd89ndCe7KfgdEQ6srevWGlH9l0xT8cFwXnmwVtaPrCw"

class AIBudgetCoachUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.headers = {
            "Authorization": f"Bearer {FIREBASE_TOKEN}"
        }

    @task(1)
    def test_health(self):
        self.client.get("/health")

    @task(3)
    def test_insights_monthly(self):
        self.client.get(
            "/v1/insights?user_id=user_1&period=monthly",
            headers=self.headers
        )