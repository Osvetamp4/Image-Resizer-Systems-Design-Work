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
    #we downloaded the img
    response = requests.get(task['image_url'])
    img = Image.open(BytesIO(response.content))
    
    #now we resize img
    width = task['parameters']['width']
    height = task['parameters']['height']
    
    img = img.resize((width, height))
    

    task_id = task['id']
    img.save(f"/shared/resized_{task_id}.png")
    result = {
            "status": "completed",
            "timestamp_queued": task["timestamp"],
            "timestamp_completed": datetime.now().isoformat(),
            "task_id": task_id,
            "result":{
                "resized_image_path": f"/shared/resized_{task_id}.png"
            }
        }
    redis_client.set(f"task_result:{task_id}", json.dumps(result))
    
    

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