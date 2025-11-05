FROM python:3.10-slim-bookworm AS base


RUN --mount=type=bind,source=requirements.txt,target=/requirements.txt \
    pip install --no-cache-dir --upgrade -r /requirements.txt

