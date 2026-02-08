import json
import redis
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import time
from prometheus_client import Counter, Histogram, start_http_server
import psycopg
import os



# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

TASKS_PROCESSED = Counter(
    "worker_tasks_processed_total",
    "Total number of tasks processed by the worker",
    ["status"],
)
TASK_PROCESSING_TIME = Histogram(
    "worker_task_processing_seconds",
    "Time spent processing a task in seconds",
)

def process_task(task):
    """we process a singular task from redis q"""
    start_time = time.time()
    #we downloaded the img
    try:
        response = requests.get(task['image_url'])
        response.raise_for_status()
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
        redis_client.set(f"task_result:{task_id}", json.dumps(result), ex=3600)
        TASKS_PROCESSED.labels(status="success").inc()

        persistent_result = {
            "timestamped_queued": task["timestamp"],
            "timestamp_completed": result["timestamp_completed"],
            "task_id": task_id,
            "result":{
                "image_url": task["image_url"],
                "width":width,
                "height":height
            }
        }
        with psycopg.connect(
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO task_results (timestamp_queued, timestamp_completed, task_id, image_url, width, height) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        persistent_result["timestamped_queued"],
                        persistent_result["timestamp_completed"],
                        persistent_result["task_id"],
                        persistent_result["result"]["image_url"],
                        persistent_result["result"]["width"],
                        persistent_result["result"]["height"],
                    )
                )
    except Exception:
        TASKS_PROCESSED.labels(status="error").inc()
        raise
    finally:
        TASK_PROCESSING_TIME.observe(time.time() - start_time)
    
    

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
    start_http_server(8000)
    working_loop()