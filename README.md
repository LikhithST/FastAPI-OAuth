# FastAPI Secure Auth & SQL Boilerplate

A robust, lightweight RESTful API boilerplate built with **FastAPI** and **SQLAlchemy**. This project provides a ready-to-use foundation for user management and secure authentication, utilizing modern security standards to protect API endpoints and user data.

## 🔐 Core Authentication & Security

This project implements a highly secure, stateless authentication flow:

*   **OAuth2 Password Bearer Flow:** Native integration with FastAPI's `OAuth2PasswordBearer` for seamless token-based authentication (works natively with Swagger UI).
*   **Stateless JWT Authentication:** Uses `PyJWT` to cryptographically sign JSON Web Tokens with configurable expiration to prevent token hijacking.
*   **Secure Password Hashing:** Utilizes `bcrypt` directly to hash and salt user passwords before database storage. Plain-text passwords are never stored.
*   **Route Protection:** Leverages FastAPI's `Depends()` system. Custom dependencies (`get_current_active_user`) automatically validate JWTs, extract user payloads, and verify user database status before granting route access.

## ✨ Features

*   **User Registration:** Secure endpoint to create new users with automatic password hashing.
*   **JWT Token Generation (`/token`):** Validates credentials and issues a JWT access token.
*   **Full CRUD for Users:** Protected endpoints to Create, Read, Update, and Delete users.
*   **SQLAlchemy ORM:** Configured with a locally managed SQLite database (`sqlite:///sql_db.db`) for easy local development.
*   **Pydantic Data Validation:** Strict validation and serialization for all API requests and responses.

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.8+ installed. You will also need [uv](https://github.com/astral-sh/uv) installed (e.g., via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`).

### Installation

1. Clone the repository and navigate into the project directory.
2. Create and activate a virtual environment using `uv`:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```
3. Install the required dependencies lightning-fast with `uv`:
   ```bash
   uv add fastapi uvicorn sqlalchemy pydantic pyjwt bcrypt
   ```

### Running the Application

Start the development server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## 📚 API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can access:

*   **Swagger UI:** http://127.0.0.1:8000/docs
*   **ReDoc:** http://127.0.0.1:8000/redoc

### Main Endpoints

**Public Routes**
*   `GET /` - Root endpoint welcome message
*   `POST /register` - Register a new user
*   `POST /token` - Authenticate and receive a JWT access token

**Protected Routes (Requires Bearer Token)**
*   `GET /profile` - Retrieve the currently authenticated user's profile
*   `GET /verify-token` - Verify if the current session token is valid
*   `GET /users/` - List all users
*   `POST /users/` - Create a new user (Admin/Internal)
*   `GET /users/{user_id}` - Retrieve a specific user
*   `PUT /users/{user_id}` - Update a specific user
*   `DELETE /user/{user_id}` - Delete a specific user

## 🛠️ Configuration

Security settings can be adjusted at the top of `main.py`:
*   `SECRET_KEY`: Change this to a secure random string in production!
*   `TOKEN_EXPIRES`: Adjust the JWT validity duration (default: 30 minutes).
