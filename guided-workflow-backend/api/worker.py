from uvicorn.workers import UvicornWorker


class ApiUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {"log_config": "/code/logging.json"}
