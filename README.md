# Backend User Service

A microservice responsible for managing user authentication, profile data, roles, and permissions. It handles user registration, login, token management, and user-related CRUD operations securely and efficiently. This service now integrates Stripe for payment processing and uses FastAPI's background tasks for asynchronous operations, removing previous dependencies on Celery, Redis, and Kafka.

## Features

-   **User Management:** Registration, login, profile management, role-based access control.
-   **Authentication:** JWT-based authentication with refresh tokens.
-   **Address Management:** Create, retrieve, update, and delete user addresses.
-   **Product Catalog:** Manage products, categories, tags, and product variants.
-   **Shopping Cart:** Add, update, and remove items from a user's cart.
-   **Order Processing:** Create and manage customer orders.
-   **Payment Integration:** Secure payment processing via Stripe.
-   **Promotions:** Management of promotional codes.
-   **Currency Management:** Support for multiple currencies.
-   **Email Notifications:** (e.g., account activation, password reset).

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)
-   [Python 3.9+](https://www.python.org/downloads/)
-   [pip](https://pip.pypa.io/en/stable/installation/)

### 1. Local Development with Docker Compose (Recommended)

This method uses Docker to run PostgreSQL locally, providing a consistent development environment.

#### 1.1. Environment Setup

1.  Create a `.env.local` file in the project root directory by copying `.env.local.example` (if available) or creating it manually. Populate it with your local development environment variables. At a minimum, you'll need:

    ```ini
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_SERVER=postgres-db # This matches the service name in docker-compose.dev.yml
    POSTGRES_PORT=5432
    POSTGRES_DB=users_db

    SECRET_KEY=your-super-secret-key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_DAYS=7

    STRIPE_SECRET_KEY=sk_test_your_secret_key
    STRIPE_PUBLIC_KEY=pk_test_your_public_key
    STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

    # ... other necessary variables (e.g., email, Firebase credentials if used)
    ```

2.  Ensure the `run_docker.sh` script is executable:

    ```bash
    chmod +x run_docker.sh
    ```

#### 1.2. Running the Services

To start the backend and its dependencies (PostgreSQL) using Docker Compose:

```bash
./run_docker.sh dev up
```

This command will:

-   Build the Docker images.
-   Start the `postgres-db` and `backend` containers.
-   Run database migrations automatically via the `entrypoint.dev.sh` script.

#### 1.3. Accessing the API

Once the services are up, the FastAPI application will be accessible at:

-   **API Docs (Swagger UI):** `http://localhost:8000/docs`
-   **API ReDoc:** `http://localhost:8000/redoc`

### 2. Local Development with Supabase PostgreSQL

If you prefer to use an external PostgreSQL database like Supabase, follow these steps:

#### 2.1. Environment Setup

1.  Create a `.env.local` file in the project root directory. Populate it with your Supabase PostgreSQL connection details and other environment variables. Example:

    ```ini
    POSTGRES_USER=your_supabase_user
    POSTGRES_PASSWORD=your_supabase_password
    POSTGRES_SERVER=your_supabase_host.supabase.co
    POSTGRES_PORT=5432
    POSTGRES_DB=postgres

    SECRET_KEY=your-super-secret-key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_DAYS=7

    STRIPE_SECRET_KEY=sk_test_your_secret_key
    STRIPE_PUBLIC_KEY=pk_test_your_public_key
    STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

    # ... other necessary variables
    ```

2.  Install Python dependencies:

    ```bash
    pip install -r backend/requirements.txt
    ```

#### 2.2. Running Migrations

Before starting the server, ensure your database schema is up-to-date. You'll need to run Alembic migrations:

```bash
cd backend
alembic upgrade head
cd ..
```

#### 2.3. Starting the FastAPI Server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2.4. Accessing the API

Once the server is running, the FastAPI application will be accessible at:

-   **API Docs (Swagger UI):** `http://localhost:8000/docs`
-   **API ReDoc:** `http://localhost:8000/redoc`

## Deployment (Production)

For production deployment, use the `prod` environment with the `run_docker.sh` script.

#### 3.1. Environment Setup

1.  Create a `.env.production` file in the project root directory. This file should contain your production-ready environment variables, including actual secret keys, Stripe live keys, and your production database connection details.

    ```ini
    POSTGRES_USER=your_prod_db_user
    POSTGRES_PASSWORD=your_prod_db_password
    POSTGRES_SERVER=your_prod_db_host # e.g., your Supabase host or RDS endpoint
    POSTGRES_PORT=5432
    POSTGRES_DB=your_prod_db_name

    SECRET_KEY=your-production-secret-key-VERY-IMPORTANT
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=15
    REFRESH_TOKEN_EXPIRE_DAYS=7

    STRIPE_SECRET_KEY=sk_live_your_secret_key
    STRIPE_PUBLIC_KEY=pk_live_your_public_key
    STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

    DOMAIN=your-production-domain.com
    ENVIRONMENT=production
    # ... other production variables
    ```

2.  Ensure the `run_docker.sh` script is executable:

    ```bash
    chmod +x run_docker.sh
    ```

#### 3.2. Running Production Services

```bash
./run_docker.sh prod up
```

This command will:

-   Build the Docker images using `Dockerfile.prod`.
-   Start the `backend` container.
-   Run database migrations automatically via the `entrypoint.prod.sh` script.

## API Documentation

Detailed API endpoints, request/response schemas, and authentication information can be found in [api.md](api.md).

Alternatively, you can access the interactive Swagger UI at `/docs` or ReDoc at `/redoc` when the server is running.

## Running Tests

(Instructions for running tests will go here once tests are implemented)

## Contributing

(Guidelines for contributing to the project)

## License

(Project license information)
