   # Subscription Service Microservice
   This is a backend microservice that manages user subscriptions for a SaaS platform. It allows users to subscribe to various plans, manage their subscriptions, and retrieve their subscription details.

    ## Table of Contents
    - [Features](#features)
    - [Technical Stack](#technical-stack)
    - [Project Structure](#project-structure)
    - [Prerequisites](#prerequisites)
    - [Setup and Installation](#setup-and-installation)
    - [Environment Variables](#environment-variables)
    - [Running the Application](#running-the-application)
    - [API Endpoints](#api-endpoints)
    - [Running Scheduled Tasks](#running-scheduled-tasks)
    - [Testing](#testing)
    - [Further Considerations](#further-considerations)

    ## Features
    - User Subscription Management: Create, Retrieve, Update, Cancel subscriptions.
    - Plan Management: Define and Retrieve subscription plans.
    - Subscription Status Handling: ACTIVE, INACTIVE, CANCELLED, EXPIRED.
    - Automatic Subscription Expiration.
    - JWT Based Authentication.

    ## Technical Stack
    - **Language:** Python 3.x
    - **Framework:** Flask
    - **Database:** MongoDB (interfaced via MongoEngine ODM)
    - **Authentication:** JWT
    - **Data Validation/Serialization:** Pydantic
    - **Background Tasks:** APScheduler (with Flask-APScheduler)
    - **Retry Logic:** Tenacity

    ## Project Structure
    ```
    subscription_service/
    ├── app/
    │   ├── __init__.py             # Flask app factory
    │   ├── api/                    # API Endpoints (Blueprints)
    │   ├── services/               # Business logic
    │   ├── models/                 # Database models (MongoEngine)
    │   ├── schemas/                # Pydantic schemas
    │   ├── core/                   # Core components (config, db, security)
    │   ├── utils/                  # Utility functions (enums, error handlers)
    │   └── tasks/                  # Background tasks (expiration checker)
    ├── .env.example                # Example environment variables
    ├── .gitignore
    ├── requirements.txt
    ├── run.py                      # Script to run the dev server
    └── README.md
    ```

    ## Prerequisites
    - Python 3.8+
    - Pip (Python package installer)
    - MongoDB instance (local or MongoDB Atlas)
    - (Optional) Docker for running MongoDB locally

    ## Setup and Installation
    1.  **Clone the repository:**
        ```bash
        git clone <repository_url>
        cd subscription_service
        ```
    2.  **Create and activate a virtual environment:**
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    3.  **Install dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    4.  **Set up MongoDB:**
        - Ensure you have a MongoDB instance running.
        - For MongoDB Atlas, make sure your current IP address is whitelisted under "Network Access".

    ## Environment Variables
    Create a `.env` file in the project root directory by copying `.env.example`:
    ```bash
    cp .env.example .env
    ```
    Then, edit the `.env` file with your specific configurations:
    - `MONGODB_SETTINGS_HOST`: Your MongoDB connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true&w=majority`). **Remember to include the database name in the SRV string.**
    - `SECRET_KEY`: A strong, random string for JWT signing (e.g., generate with `python -c 'import secrets; print(secrets.token_hex(32))'`).
    - `JWT_ALGORITHM`: Default is `HS256`.
    - `FLASK_APP`: Should be `run.py`.
    - `FLASK_ENV`: Set to `development` for development mode, `production` for production.
    - `SCHEDULER_API_ENABLED`: Set to `True` to enable the background job for expiring subscriptions, `False` to disable.

    ## Running the Application
    ```bash
    flask run
    ```
    The application will be available at `http://127.0.0.1:5000` by default.
    - Health check: `GET http://127.0.0.1:5000/health`

    ## API Endpoints

    All API endpoints are prefixed with `/api`. Authentication is required for subscription management endpoints, using a Bearer token in the `Authorization` header.

    **Authentication (Test Token Generation - Debug Mode Only)**
    - `GET /get-token/<user_id>`: Generates a test JWT for the given `user_id`.
      - Example: `GET http://127.0.0.1:5000/get-token/user123`

    **Plans**
    - `GET /plans`: Retrieve all available subscription plans.
      - Response: `200 OK` with a list of plans.
    - `GET /plans/<plan_id>`: Retrieve a specific plan by its ID.
      - Response: `200 OK` with plan details, or `404 Not Found`.

    **Subscriptions**
    *(Requires `Authorization: Bearer <jwt_token>` header)*
    - `POST /subscriptions`: Create a new subscription for the authenticated user.
      - Request Body: `{"plan_id": "string_object_id_of_plan"}`
      - Response: `201 Created` with new subscription details, or error (e.g., `400`, `404`, `409`, `500`).
    - `GET /subscriptions/<user_id>`: Retrieve the current subscription for the specified `user_id`. (User can only access their own).
      - Response: `200 OK` with subscription details, or `404 Not Found`.
    - `PUT /subscriptions/<user_id>`: Update (upgrade/downgrade) the active subscription for the specified `user_id`.
      - Request Body: `{"plan_id": "string_object_id_of_new_plan"}`
      - Response: `200 OK` with updated subscription details, or error.
    - `DELETE /subscriptions/<user_id>`: Cancel the active subscription for the specified `user_id`.
      - Response: `200 OK` with cancelled subscription details (status set to CANCELLED), or error.

    ## Running Scheduled Tasks
    The subscription expiration task runs automatically if `SCHEDULER_API_ENABLED` is `True`.
    - Default interval: Every 1 hour (configurable in `app/tasks/expiration_checker.py`).
    - Logs its activity to the Flask console.

    ## Testing
    - Use an API client like Postman or Insomnia to test the endpoints.
    - Manually insert initial plan data into MongoDB to test `GET /plans`.
    - To test JWT-protected routes:
      1. Generate a token using `GET /get-token/<some_user_id>`.
      2. Include the token in the `Authorization` header as `Bearer <token_value>`.
    - To test subscription expiration:
      1. Create a subscription.
      2. Manually set its `end_date` in MongoDB to a past datetime.
      3. Ensure its `status` is "ACTIVE".
      4. Set a short interval for the `expire_subscriptions_job` in `app/tasks/expiration_checker.py` (e.g., `seconds=30`).
      5. Monitor logs and database to confirm the status changes to "EXPIRED". Remember to revert the interval.

    ## Further Considerations
    - **Production Deployment:** Use a production-grade WSGI server (e.g., Gunicorn, uWSGI) behind a reverse proxy (e.g., Nginx).
    - **Comprehensive Testing:** Add unit and integration tests (e.g., using Pytest).
    - **API Documentation:** Generate OpenAPI/Swagger documentation (e.g., using Flasgger or Pydantic's schema export).
    - **Enhanced Security:** Rate limiting, more robust CSRF protection if web forms were involved, detailed audit logging.
    - **Message Queue for Asynchronous Updates (Bonus):** For operations like sending email notifications upon subscription changes, a message queue (RabbitMQ, Kafka, Redis Streams) could be integrated.
    - **Configuration Management:** For production, use a more robust configuration management system or environment variable injection by the deployment platform.
    ```

*   **B. API Docs (Swagger/OpenAPI):**
    This would involve integrating a library like `Flasgger` or manually crafting an OpenAPI specification.
    *   **Flasgger:** You'd add OpenAPI spec snippets in the docstrings of your API route functions. Pydantic models can often be converted to Marshmallow schemas or directly to OpenAPI schema components for Flasgger.
    *   **Pydantic's `model_json_schema()`:** Pydantic models have a `.model_json_schema()` (V2) or `.schema()` (V1) method that outputs a JSON Schema, which is a good part of an OpenAPI spec. You could collect these and build the full spec.
    This is a more involved step. For now, the `README.md` provides a good textual description of the API.

