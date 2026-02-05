from flask import Flask, request, jsonify, Response, g
import redis
import json
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint"],
)

@app.before_request
def start_timer():
    g.start_time = datetime.now().timestamp()

@app.after_request
def record_metrics(response):
    try:
        latency = datetime.now().timestamp() - g.start_time
        endpoint = request.path
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            http_status=response.status_code,
        ).inc()
    except Exception:
        pass
    return response

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

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
