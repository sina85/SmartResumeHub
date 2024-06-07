from fastapi import FastAPI
from celery import Celery

api_key = ''
config_path = 'config.json'
client = None
Capp = Celery('tasks', broker='redis://localhost:6379/1')

sse_connections = []