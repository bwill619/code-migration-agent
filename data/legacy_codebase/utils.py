import requests
import time
from flask import jsonify

def fetch_user(user_id: int):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return jsonify(response.json())

def fetch_posts(user_id: int):
    response = requests.get(f"https://api.example.com/users/{user_id}/posts")
    return jsonify(response.json())

def slow_operation(duration: int):
    time.sleep(duration)
    return {"status": "done"}
