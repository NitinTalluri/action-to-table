# 
FROM 837578041534.dkr.ecr.us-east-1.amazonaws.com/bases/uvicorn:python3.10-dev

# Add htop for resource monitoring via SSH

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        htop; \
    rm -rf /var/lib/apt/lists/*

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt
COPY ./logging.json /code/logging.json

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./api /code/api
COPY --chmod=774 entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "api.main:app", "-k", "api.worker.ApiUvicornWorker", "--bind","0.0.0.0:8080"]