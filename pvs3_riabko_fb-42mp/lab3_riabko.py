from neo4j import GraphDatabase
import threading
import time

URI = "neo4j+s://e02971e1.databases.neo4j.io"
USER = "neo4j"
PASSWORD = ""

THREADS = 10
INCREMENTS_PER_THREAD = 10000
ITEM_NAME = "Smartphone"


def increment_likes(item_name, increments):
    driver = GraphDatabase.driver(
        URI, auth=(USER, PASSWORD)
    )
    with driver.session() as session:
        for _ in range(increments):
            session.run(
                """
                MATCH (i:Item {name: $item_name})
                SET i.likes = i.likes + 1
            """,
                item_name=item_name,
            )
    driver.close()


if __name__ == "__main__":
    threads = []

    start_time = time.time()

    for _ in range(THREADS):
        thread = threading.Thread(
            target=increment_likes, args=(ITEM_NAME, INCREMENTS_PER_THREAD)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Кінець заміру часу
    end_time = time.time()

    print(f"Increment completed: {ITEM_NAME}!")
    print(f"Total time: {end_time - start_time:.2f} sec.")
