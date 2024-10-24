import psycopg2
from concurrent.futures import ThreadPoolExecutor
import time
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global variables for database connection
DB_NAME = "pvs2"
DB_USER = "admin"
DB_PASSWORD = "admin"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"


def ensure_table_exists():
    conn = psycopg2.connect(
        database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_counter (
            user_id SERIAL PRIMARY KEY,
            counter INTEGER NOT NULL DEFAULT 0,
            version INTEGER NOT NULL DEFAULT 0
        )
    """
    )

    cursor.execute("SELECT COUNT(*) FROM user_counter WHERE user_id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_counter (counter, version) VALUES (0, 0)")

    conn.commit()
    cursor.close()
    conn.close()


def reset_counter():
    conn = psycopg2.connect(
        database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    cursor.execute("UPDATE user_counter SET counter = 0, version = 0 WHERE user_id = 1")
    conn.commit()

    cursor.close()
    conn.close()


def update_counter(query_func, thread_id):
    conn = psycopg2.connect(
        database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor()

    for i in range(10_000):
        query_func(cursor, thread_id, i)
        conn.commit()

    cursor.close()
    conn.close()


def lost_update_query(cursor, thread_id, iteration):
    cursor.execute("SELECT counter FROM user_counter WHERE user_id = 1")
    counter = cursor.fetchone()[0]
    counter += 1
    cursor.execute("UPDATE user_counter SET counter = %s WHERE user_id = 1", (counter,))


def inplace_update_query(cursor, thread_id, iteration):
    cursor.execute(
        "UPDATE user_counter SET counter = counter + 1 WHERE user_id = 1 RETURNING counter"
    )


def row_level_locking_query(cursor, thread_id, iteration):
    cursor.execute("SELECT counter FROM user_counter WHERE user_id = 1 FOR UPDATE")
    counter = cursor.fetchone()[0]
    counter += 1
    cursor.execute("UPDATE user_counter SET counter = %s WHERE user_id = 1", (counter,))


def optimistic_concurrency_query(cursor, thread_id, iteration):
    while True:
        cursor.execute("SELECT counter, version FROM user_counter WHERE user_id = 1")
        counter, version = cursor.fetchone()
        counter += 1
        cursor.execute(
            "UPDATE user_counter SET counter = %s, version = %s WHERE user_id = 1 AND version = %s",
            (counter, version + 1, version),
        )
        if cursor.rowcount > 0:
            break


# Function to measure execution time
def measure_time(query_func, label):
    logging.info(f"Starting test: {label}")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(update_counter, query_func, i) for i in range(10)]
        for future in futures:
            future.result()
    end_time = time.time()
    logging.info(f"{label} completed in {end_time - start_time:.2f} seconds")

 
    logging.info(f"Counter reset after {label}.")


if __name__ == "__main__":
    logging.info("Starting...")

    ensure_table_exists()

    measure_time(lost_update_query, "Lost-update")
    reset_counter()

    measure_time(inplace_update_query, "In-place Update")
    reset_counter()

    measure_time(row_level_locking_query, "Row-level Locking")
    reset_counter()

    measure_time(optimistic_concurrency_query, "Optimistic Concurrency Control")

    logging.info("All tests completed.")
