import hazelcast
import time
import logging
from threading import Thread


NODES = [
    "127.0.0.1:5701",
    "127.0.0.1:5702",
    "127.0.0.1:5703",
]
CLUSTER_NAME = "lab_1_cluster"



client = hazelcast.HazelcastClient(
    cluster_name=CLUSTER_NAME,
    cluster_members=NODES,
)

distributed_map = client.get_map("my-distributed-map").blocking()


atomic_long = client.cp_subsystem.get_atomic_long("my-atomic-long").blocking()



def increment_counter():
    key = "counter"
    for _ in range(10000):
        counter = distributed_map.get(key)
        if counter is None:
            counter = 0
        distributed_map.put(key, counter + 1)


def increment_counter_with_pessimistic_lock():
    key = "counter"
    for _ in range(10000):
        distributed_map.lock(key) 
        try:
            counter = distributed_map.get(key)
            if counter is None:
                counter = 0
            distributed_map.put(key, counter + 1)
        finally:
            distributed_map.unlock(key)



def increment_counter_with_optimistic_lock():
    key = "counter"
    for _ in range(10000):
        while True:
            counter = distributed_map.get(key)
            new_counter = counter + 1
            if distributed_map.replace_if_same(key, counter, new_counter):
                break



def increment_atomic_long():
    for _ in range(10000):
        atomic_long.increment_and_get()



def run_threads(increment_func, description):
    threads = []
    start_time = time.time()

    for _ in range(10):
        t = Thread(target=increment_func)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    execution_time = time.time() - start_time
    print(f"{description} completed in {execution_time:.2f} seconds")


print("Starting increment without locks...")
run_threads(increment_counter, "Increment without locks")
final_value = distributed_map.get("counter")
print(f"Final counter value (without locks): {final_value}")

print("Starting increment with pessimistic locking...")
distributed_map.put("counter", 0) 
run_threads(
    increment_counter_with_pessimistic_lock, "Increment with pessimistic locking"
)
final_value = distributed_map.get("counter")
print(f"Final counter value (with pessimistic locking): {final_value}")

print("Starting increment with optimistic locking...")
distributed_map.put("counter", 0) 
run_threads(increment_counter_with_optimistic_lock, "Increment with optimistic locking")
final_value = distributed_map.get("counter")
print(f"Final counter value (with optimistic locking): {final_value}")

print("Starting increment with IAtomicLong...")
atomic_long.set(0) 
run_threads(increment_atomic_long, "Increment with IAtomicLong")
final_value = atomic_long.get()
print(f"Final IAtomicLong value: {final_value}")

client.shutdown()
