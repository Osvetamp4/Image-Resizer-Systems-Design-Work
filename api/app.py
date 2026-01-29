from flask import Flask, request, jsonify
import redis
import json
from datetime import datetime

app = Flask(__name__)

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/queue-task', methods=['POST'])
def queue_task():
    """
    Queue a task to Redis
    Expects JSON: {
        "image_url": "...",
        "parameters": {
            "width": 100,
            "height": 100
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Missing data"}), 400
        
        #this is the task object
        task = {
            "image_url": data.get("image_url"),
            "timestamp": datetime.now().isoformat(),
            "parameters": data.get("parameters", {})
        }
        
        #send this task to redis container
        task_id = redis_client.incr("task_counter")
        task["id"] = task_id
        redis_client.lpush("task_queue", json.dumps(task))
        
        #this gets sent back to nginx frontend
        return jsonify({
            "status": "queued",
            "task_id": task_id
        }), 202
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/task-status/<int:task_id>', methods=['GET'])
def task_status(task_id):
    """Check status of a task"""
    try:
        result = redis_client.get(f"task_result:{task_id}")
        
        if result is None:
            return jsonify({"status": "pending"}), 200
        
        return jsonify(json.loads(result)), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
