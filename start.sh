#!/bin/bash
service redis-server start && uv run worker.py & uv run app.py