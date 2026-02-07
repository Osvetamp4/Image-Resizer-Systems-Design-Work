
import os
import redis
import time



# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def clean_resized_images():
    """we process a singular task from redis q"""
    cursor = 0
    keys = []
    while True:
        cursor, batch = redis_client.scan(cursor=cursor, match="task_result:*", count=100)
        keys.extend(batch)
        if cursor == 0:
            break
    keys = set(map(lambda k: k.split("task_result:")[1], keys))

    for name in os.listdir("/shared"):
        path = os.path.join("/shared", name)
        task_id = name.split("resized_")[1].split(".png")[0]
        if task_id not in keys:
            os.remove(path)
def working_loop():
    """We this every half an hour to wipe away any images in the shared volume that exceeds 1 hour"""
    while True:
        time.sleep(1800)
        clean_resized_images()


if __name__ == '__main__':
    #start_http_server(8000)
    working_loop()