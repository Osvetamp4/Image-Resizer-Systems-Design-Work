import json
import redis
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import time



# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def process_task(task):
    """we process a singular task from redis q"""
    response = requests.get(task['image_url'])
    img = Image.open(BytesIO(response.content))
    pass

def working_loop():
    """We constantly run and listen for new tasks in Redis"""
    while True:
        #pop task from Redis q
        task_data = redis_client.brpop('task_queue')

        if task_data:
            task = json.loads(task_data[1])
            process_task(task)
        time.sleep(0.1)


if __name__ == '__main__':
    working_loop()