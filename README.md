# Scrap Test Task

## Project Overview

This project is an **asynchronous Python scraper** for car listings. It collects detailed information from listings, including title, price, mileage, VIN, images, and seller contact info, and stores the data in a **PostgreSQL database**.  

Additionally, it provides a **scheduler** to create daily database dumps for backup.

**Key Features:**
- Async scraping using `httpx` and `asyncio`
- Robust parsing with `lxml` and regex
- PostgreSQL storage via **async SQLAlchemy**
- Daily database dumps via `scheduler.py` and `pg_dump`
- Fully Dockerized for easy deployment

---

## Project Structure

```

scrap-test-task/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py
├── scheduler.py
├── dump_db.py
├── db.py
├── additional_func.py
├── README.md
└── venv/

````

---

## Prerequisites

- Docker >= 24.0  
- Docker Compose >= 2.17  
- `.env` file at the project root with the following variables (just copy and paste this):

```
# TARGET URL
URL=https://auto.ria.com/uk/search/?indexName=auto

# POSTGRES
POSTGRES_USER=user
POSTGRES_PASSWORD=some_password
POSTGRES_DB=autos
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

---

## Setup & Running with Docker

1. **Build and start services:**

```bash
docker-compose up --build
```

This will:

* Start a PostgreSQL container with persistent volume `db_data`
* Start a Python scraper container

2. **Volume Mapping for Dumps:**

* Database dumps are stored in `./dumps` on your host machine.
* `scheduler.py` creates daily dumps at **12:00 by default**.

---

## Scraper Usage

The scraper runs automatically in the container:

* It parses pages asynchronously with a maximum of `MAX_CONCURRENT=3` requests at a time.
* Pagination continues until no new listings are found.
* Extracted data is inserted into PostgreSQL with duplicate URLs ignored.

---

## Scheduler / Database Dumps

The scheduler (`scheduler.py`) uses the `schedule` library to run daily database backups:

* Dumps are stored in `dumps/` folder with timestamp:

  ```
  dumps/POSTGRES_DB_YYYY-MM-DD_HH-MM-SS.sql
  ```
* Uses `pg_dump` with custom format.

**Important Docker Note:**
Currently, both `scheduler.py` and `main.py` are started in the same container. For production, consider running the scheduler in a **separate container** to ensure proper PID management and reliability.

---

## Database Setup

* Uses **SQLAlchemy Async** with `asyncpg` driver.
* Table: `cars` with columns:

  * `url` (primary key)
  * `title`, `price_usd`, `odometer`
  * `username`, `phone_number`
  * `image_url`, `images_count`
  * `car_number`, `car_vin`
  * `created_at` (UTC timestamp)
* `insert_car` handles conflicts gracefully using `ON CONFLICT DO NOTHING`.

Tables are automatically created on scraper startup via `init_db()`.

---

## Notes & Best Practices

1. **Environment Validation**

   * Ensure `.env` is complete and correct.
   * Scraper and dump scripts rely on proper DB host and credentials.

2. **Docker Networking**

   * Containers communicate via service names (`db` for PostgreSQL).

3. **Scheduler Reliability**

   * Running scheduler and scraper in a single container using `&` may cause termination issues.
   * Recommended: Separate `scheduler` into its own service in Docker Compose.

4. **Logging**

   * Scraper prints detailed logs for fetched pages and parsing errors.
   * Scheduler prints success/error messages for each database dump.

5. **Extensibility**

   * Concurrency, dump schedule, and target URL can be configured via `.env`.

---

## Example Commands

**Start all services:**

```bash
docker-compose up
```

**Start only the scraper:**

```bash
docker-compose run scraper python main.py
```

**Create a manual dump:**

```bash
docker-compose run scraper python dump_db.py
```

**View logs:**

```bash
docker-compose logs -f scraper
```
