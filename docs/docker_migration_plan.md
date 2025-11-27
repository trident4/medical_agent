# Docker Migration Plan: PostgreSQL to MySQL

## Objective
Update the Docker configuration to support the new MySQL database architecture, replacing the existing PostgreSQL setup.

---

## 1. Update `docker-compose.yml`

### Database Service (`db`)
- **Change Image:** Replace `postgres:13` with `mysql:8.0`
- **Update Environment Variables:**
  - Remove: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - Add: 
    - `MYSQL_ROOT_PASSWORD`
    - `MYSQL_DATABASE`
    - `MYSQL_USER`
    - `MYSQL_PASSWORD`
- **Update Volumes:** Change path to `/var/lib/mysql`
- **Update Healthcheck:** Use `mysqladmin ping`
- **Add Command:** `--default-authentication-plugin=mysql_native_password` (for broad compatibility)

### Web Service (`web`)
- **Update Environment Variables:**
  - Replace `POSTGRES_*` vars with `MYSQL_*` vars
  - Ensure `DATABASE_URL` uses `mysql+aiomysql` driver
- **Dependencies:** Keep `depends_on` for `db` service

### Admin Interface (`phpmyadmin`)
- **Replace:** `pgadmin` service
- **New Image:** `phpmyadmin/phpmyadmin`
- **Configuration:**
  - `PMA_HOST=db`
  - `MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}`
- **Ports:** Map `8080:80` (or keep 5050 if preferred)

---

## 2. Update `.env_docker`
- Create/Update this file to contain the MySQL credentials matching the `docker-compose.yml` variables.

---

## 3. Verify `Dockerfile` & `entrypoint`
- **Dockerfile:** No changes needed (Python drivers are already installed in `requirements.txt`).
- **docker-entrypoint.sh:** No changes needed (Alembic handles DB connection abstraction).

---

## Example `docker-compose.yml` Structure

```yaml
version: '3.8'

services:
  web:
    # ... (build config)
    environment:
      - MYSQL_HOST=db
      - MYSQL_PORT=3306
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      # ... other app vars
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mysql:8.0
    command: --default-authentication-plugin=mysql_native_password
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    environment:
      PMA_HOST: db
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    ports:
      - "8080:80"
    depends_on:
      - db
```
