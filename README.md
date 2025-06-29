# backend-user-service
A microservice responsible for managing user authentication, profile data, roles, and permissions. It handles user registration, login, token management, and user-related CRUD operations securely and efficiently.

# Start Local Server
Use the command below to start
```bash 
uvicorn main:app --reload
```

# Setting up the Local Database
1. Create Virtual Environment and Install Python Dependencies
   create virtual environment
   ```bash
   python3 -m venv venv
   ```
   active virtual environment (Command for Macos check [here](https://docs.python.org/3/library/venv.html#how-venvs-work) for your os)
   ```bash
   source venv/bin/activate
   ```
   install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Migration Script
   ```bash
   chmod +x ./run_migrations.sh
   ./run_migrations.sh
   ```

3. Run the Migration Command
   ```bash
    alembic revision --autogenerate -m "Migration message"
    ```

4. Apply Migration to the Db
   ```bash
   alembic upgrade head
   ```

5. Start the Servers(redi, celery and fastapi)
   ```bash
   chmod +x ./run_servers.sh && ./run_servers.sh

   ```

6. visit the url
   ```bash
   http://localhost:8000/api/v1/users/
   http://localhost:8000/api/v1/users/login/
   http://localhost:8000/api/v1/addresses/
   ```