# Requirement Traceability Matrix

This document links the functional requirements defined in the proposal
to the backend architecture implemented in the GitHub repository.

The goal is to ensure the implementation follows the proposal
without introducing features outside the approved scope.

---

## Mapping Requirements to Implementation

| FR ID | Requirement | Description | GitHub Location | Main Files | Database |
|------|-------------|-------------|----------------|-----------|----------|
| FR-1 | Transaction Data Reception | The system receives anonymized financial transaction data from client applications through a secure REST API and supports both batch and incremental submissions. | backend/app/api | transactions.py | transactions |
| FR-2 | Transaction Data Validation | The system validates the format and completeness of incoming transaction data and rejects invalid requests with appropriate error responses. | backend/app/schema | transaction_schema.py | - |
| FR-3 | Transaction Storage | The system securely stores validated transaction data in the database while ensuring no personally identifiable information is recorded. | backend/app/models | transaction.py | transactions |
| FR-4 | Transaction Categorization | The system classifies transactions into predefined spending categories and allows re-categorization if additional information becomes available. | backend/app/services | categorization_service.py | categories |
| FR-5 | Spending Summary Generation | The system generates aggregated spending summaries over configurable time periods such as weekly or monthly and groups results by category. | backend/app/api + services | insights.py | transactions |
| FR-6 | Recurring Expense Detection | The system identifies recurring transactions such as subscriptions or regular payments and exposes them through the API. | backend/app/services | recurring_service.py | recurring_expenses |
| FR-7 | Cashflow Forecasting | The system generates short-term cashflow forecasts based on historical transaction data and updates forecasts when new transactions are added. | backend/app/services | forecast_service.py | forecasts |
| FR-8 | Financial Insight Generation | The system analyzes transaction data to generate financial insights such as spending trends and unusual spending patterns. | backend/app/services | insight_service.py | insights |
| FR-9 | Insight Retrieval | The system allows client applications to request generated financial insights and returns them using a defined response structure. | backend/app/api | insights.py | insights |
| FR-10 | Conversational Query Support | The system allows users to ask questions about their financial insights in natural language and responds using previously generated insights. | backend/app/services | conversational_service.py | insights |
| FR-11 | Authentication and Authorization | The system ensures that all API requests are authenticated and that only authorized client applications can access the service. | backend/app/core | auth/config modules | - |
| FR-12 | User Context Management | The system associates financial insights with an anonymized user identifier and isolates data to prevent cross-user access. | backend/app/services | user_context_service.py | user_context |
| FR-13 | System Logging | The system records API requests and processing events for monitoring and auditing while ensuring logs do not contain sensitive financial information. | backend/app/core | logging module | api_logs |
| FR-14 | Error Handling and Reporting | The system detects processing errors and returns meaningful error messages to client applications while maintaining stable operation. | backend/app/api + core | error handlers | - |
| FR-15 | Configuration Management | The system allows system parameters such as analysis windows or forecasting settings to be modified without interrupting the service. | backend/app/core | config.py | - |
| FR-16 | Personalized Insight Adaptation | The system adapts financial insights for each user based on their evolving spending behavior over time. | backend/app/services | insight_service.py | insights |
| FR-17 | Anomalous Spending Detection | The system detects spending patterns that significantly deviate from the user's normal spending behavior and flags them as insights. | backend/app/services | anomaly_service.py | insights |
| FR-18 | Model Update and Learning Support | The system supports periodic updates of analytical models to improve prediction accuracy while maintaining system availability. | backend/app/services | model_update_service.py | model_versions |
| FR-19 | Explainable AI Output | The system provides clear human-readable explanations describing how financial insights or predictions were generated. | backend/app/services | explainability_service.py | insights |
| FR-20 | Confidence and Insights Metadata | The system attaches confidence scores and additional contextual metadata to AI-generated insights to indicate reliability. | backend/app/services | insight_service.py | insights |


---

## Purpose

This matrix ensures that every feature implemented in the codebase
corresponds to a requirement defined in the project proposal.
