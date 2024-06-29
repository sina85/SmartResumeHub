#!/bin/bash

# Start a new tmux session named 'celery'
#tmux new-session -d -s celery 'celery -A g_lobal worker --loglevel=info'

# Start the FastAPI app in the current shell
#uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Optional: Attach to the tmux session
# tmux attach -t celery

# Start the Celery worker in the background
# celery -A tasks worker --loglevel=info &

# Start the FastAPI app in the current shell
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Wait for all background processes to finish
#wait
