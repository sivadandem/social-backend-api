# Social Backend API (Flask & MySQL)

This project implements a basic social backend API using Flask, Flask-SQLAlchemy, Flask-JWT-Extended, and MySQL. It allows users to register, log in, manage profiles, find other users (with search and pagination), manage friend requests, and view their friends list. Includes automatic database creation check on first run.

## Features Implemented

*   **User Management:**
    *   Registration (Name, Email, Password)
    *   Login (Email, Password) - JWT based
    *   Get User Profile
    *   Update User Profile (Name, Bio)
*   **User Discovery:**
    *   List Other Users (Excluding Self)
    *   **Search:** Filter user list by name (`search` query parameter).
    *   **Pagination:** Paginate user list (`page`, `per_page` query parameters).
    *   Friend Suggestions (Random basic implementation).
*   **Friendship Management:**
    *   Send Friend Request
    *   Accept/Reject Friend Request
    *   List Incoming Pending Requests
    *   List Accepted Friends
*   **Technical:**
    *   JWT Authentication
    *   Secure Password Hashing (Werkzeug)
    *   Database Auto-Creation Check (if DB doesn't exist)
    *   Database Schema Migrations (Flask-Migrate/Alembic)

## Technology Stack

*   **Backend Framework:** Flask
*   **Database:** MySQL
*   **Database Driver:** PyMySQL
*   **ORM:** Flask-SQLAlchemy
*   **Database Migrations:** Flask-Migrate (using Alembic)
*   **Authentication:** Flask-JWT-Extended
*   **Serialization & Validation:** Flask-Marshmallow / Marshmallow
*   **Environment Variables:** python-dotenv
*   **Password Hashing:** Werkzeug Security Helpers
*   **Language:** Python 3.8+
*   **Package Management:** pip & venv

## Setup Instructions

1.  **Prerequisites:**
    *   Python 3.8 or higher installed.
    *   `pip` and `venv` available (usually included with Python).
    *   MySQL Server installed and **running**.

2.  **Clone the Repository (or download source):**
    ```bash
    # If using Git
    git clone <your-repository-url>
    cd social-backend-api
    # Or navigate to the downloaded/extracted project folder
    ```

3.  **Create and Activate Virtual Environment:**
    This isolates project dependencies.
    ```bash
    # Create a virtual environment folder named 'venv'
    python -m venv venv

    # Activate the environment:
    # On Windows PowerShell:
    .\venv\Scripts\activate
    # On Linux/macOS/Git Bash:
    # source venv/bin/activate
    ```
    *(Your terminal prompt should now show `(venv)` at the beginning)*

4.  **Install Dependencies:**
    Install all required Python packages listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    *   Locate the example file `.env.example`. **Rename or copy it** to create a file named exactly `.env` in the project root directory.
    *   **Edit the `.env` file** and fill in your specific details:
        ```dotenv
        # .env (EDIT THIS FILE WITH YOUR VALUES)
        FLASK_APP=run.py
        FLASK_DEBUG=False # Set to True ONLY for development debugging if needed

        # --- IMPORTANT: Configure your MySQL connection ---
        # Replace username, password, host, port (if not 3306), and database_name
        # Format: mysql+pymysql://username:password@host:port/database_name
        # REMEMBER: If your password contains special characters like '@', ':', '/', etc.,
        # they MUST be percent-encoded (e.g., '@' becomes '%40', '&' becomes '%26').
        DATABASE_URI="mysql+pymysql://root:YOUR_PASSWORD%40@localhost:3306/social_api_db" # <- SET YOUR DB NAME

        # --- IMPORTANT: Set strong secret keys ---
        # Generate a strong JWT secret key (e.g., run in python: import secrets; print(secrets.token_hex(32)))
        JWT_SECRET_KEY="YOUR_GENERATED_STRONG_JWT_SECRET_KEY"

        # Generate a strong Flask secret key (e.g., run in python: import secrets; print(secrets.token_hex(32)))
        SECRET_KEY="YOUR_GENERATED_STRONG_FLASK_SECRET_KEY"
        ```
    *   **Security Note:** The `.gitignore` file is configured to prevent committing the actual `.env` file. Never share files containing sensitive credentials.

6.  **Database Setup:**
    *   **Ensure MySQL Server is Running.**
    *   **Automatic Creation Check:** The application will attempt to connect to the MySQL server specified in `DATABASE_URI` and run `CREATE DATABASE IF NOT EXISTS your_db_name` when it first starts. The MySQL user needs permissions for this (usually true for `root`).
    *   **Manual Creation (Alternative/If auto fails):** If needed, manually create the database in MySQL:
        ```sql
        CREATE DATABASE your_db_name; -- Use the exact name from DATABASE_URI
        ```
    *   **Apply Migrations:** Once the database exists, create the necessary tables by running:
        ```bash
        # Ensure your virtual environment is active first!
        flask db upgrade
        ```
        *(You should see output indicating migrations are running or the DB is already up-to-date)*.

7.  **Run the Application:**
    Start the Flask development server:
    ```bash
    # Ensure your virtual environment is active!
    python run.py
    ```
    *(Note: Use this instead of `flask run` due to potential environment variable caching issues encountered during development).*
    *   The API should now be running, typically at `http://127.0.0.1:5000`.

## API Endpoint Documentation

**Base URL:** `http://127.0.0.1:5000`

**Authentication:** Endpoints marked `**(Auth Required)**` require a valid JWT `access_token` obtained from `/auth/login`. Include it in the request header as:
`Authorization: Bearer <your_access_token>`

**Request Body:** For `POST`/`PUT` requests sending data, ensure the header `Content-Type: application/json` is included and the body is valid JSON.

---

**Authentication (`/auth`)**

*   `POST /auth/register`
    *   **Description:** Register a new user.
    *   **Body:** `{ "name": "Test User", "email": "test@example.com", "password": "password123" }`
    *   **Response:** `201 Created` with user details (excluding password).
*   `POST /auth/login`
    *   **Description:** Authenticate and receive a JWT access token.
    *   **Body:** `{ "email": "test@example.com", "password": "password123" }`
    *   **Response:** `200 OK` with `{ "access_token": "eyJ..." }`.

---

**Users (`/users`)**

*   `GET /users/profile` **(Auth Required)**
    *   **Description:** Get the profile of the currently authenticated user.
    *   **Response:** `200 OK` with user profile data.
*   `PUT /users/profile` **(Auth Required)**
    *   **Description:** Update the profile (name, bio) of the currently authenticated user. Partial updates are allowed.
    *   **Body:** `{ "name": "New Name", "bio": "An updated bio." }`
    *   **Response:** `200 OK` with the updated user profile data.
*   `GET /users/` **(Auth Required)**
    *   **Description:** List other registered users (excluding the authenticated user). Supports search and pagination.
    *   **Query Parameters:**
        *   `search=<query>` (Optional): Filter users by name (case-insensitive, partial match). Example: `/users/?search=Alice`
        *   `page=<number>` (Optional): Specify the page number for pagination (default: 1). Example: `/users/?page=2`
        *   `per_page=<number>` (Optional): Specify the number of users per page (default: 10, max: 100). Example: `/users/?per_page=5`
    *   **Response:** `200 OK` with a JSON object containing a list of `users` and `pagination` metadata.
        ```json
        {
          "users": [ /* ... user objects ... */ ],
          "pagination": {
            "total_items": ..., "total_pages": ..., "current_page": ...,
            "per_page": ..., "has_next": ..., "has_prev": ...,
            "next_page": ..., "prev_page": ...
          }
        }
        ```
*   `GET /users/suggestions` **(Auth Required)**
    *   **Description:** Get a list of random user suggestions (up to 5) excluding self, current friends, and users with pending requests.
    *   **Response:** `200 OK` with a list of suggested user objects.

---

**Friend Requests (`/friend-requests`)**

*   `POST /friend-requests/send/<int:recipient_id>` **(Auth Required)**
    *   **Description:** Send a friend request to the user specified by `<recipient_id>`.
    *   **Response:** `201 Created` confirming the request was sent (status: pending).
*   `PUT /friend-requests/<int:request_id>/accept` **(Auth Required)**
    *   **Description:** Accept the incoming friend request specified by `<request_id>`. The authenticated user must be the recipient of the request.
    *   **Response:** `200 OK` confirming acceptance (status: accepted).
*   `PUT /friend-requests/<int:request_id>/reject` **(Auth Required)**
    *   **Description:** Reject the incoming friend request specified by `<request_id>`. The authenticated user must be the recipient of the request.
    *   **Response:** `200 OK` confirming rejection (status: rejected).
*   `GET /friend-requests/incoming` **(Auth Required)**
    *   **Description:** List all friend requests received by the authenticated user that are still pending.
    *   **Response:** `200 OK` with a list of pending friend request objects.
*   `GET /friend-requests/list` **(Auth Required)**
    *   **Description:** List all users who are accepted friends with the authenticated user.
    *   **Response:** `200 OK` with a JSON object `{ "friends": [ ... friend user objects ... ] }`.

## API Testing Tool

*   **Postman:** A Postman collection file (`Social_API.postman_collection.json`) is included in the root of this repository. You can import this file into your Postman application (File -> Import) to get pre-configured requests for all endpoints. Remember to run the "Login" request first to automatically capture the JWT token for authenticated requests.

---
