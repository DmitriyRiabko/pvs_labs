from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from threading import Thread
import time

MONGO_URL = "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"

def increment_likes(write_concern, increments):
  
    client = MongoClient(MONGO_URL)
    db = client["performance_test"]
    collection = db.get_collection("likes_counter", write_concern=write_concern)

    for _ in range(increments):
        collection.find_one_and_update(
            {"_id": 1},
            {"$inc": {"likes": 1}}
        )
    client.close()

def run_test(write_concern, increments, clients):
  
    threads = []
    for _ in range(clients):
        thread = Thread(target=increment_likes, args=(write_concern, increments))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("Test completed.")

if __name__ == "__main__":
    increments_per_client = 10000
    clients_count = 10

    client = MongoClient(MONGO_URL)
    db = client["performance_test"]

    db.likes_counter.update_one({"_id": 1}, {"$set": {"likes": 0}})
    print("Running test with writeConcern = 1...")
    start_time = time.time()
    run_test(WriteConcern(w=1), increments_per_client, clients_count)
    print("Time with writeConcern = 1:", time.time() - start_time)

    likes_count = db.likes_counter.find_one({"_id": 1})["likes"]
    print("Final likes count after writeConcern = 1:", likes_count)

    db.likes_counter.update_one({"_id": 1}, {"$set": {"likes": 0}})
    print("Likes counter reset to 0.")

    print("Running test with writeConcern = majority...")
    start_time = time.time()
    run_test(WriteConcern(w="majority"), increments_per_client, clients_count)
    print("Time with writeConcern = majority:", time.time() - start_time)

    likes_count = db.likes_counter.find_one({"_id": 1})["likes"]
    print("Final likes count after writeConcern = majority:", likes_count)

    client.close()
