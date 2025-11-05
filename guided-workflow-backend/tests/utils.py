import uuid


class MockPrefectClient:
    def __init__(self):
        ...

    @staticmethod
    def create_flow_run(*args, **kwargs):
        print("Creating flow run", args, kwargs)
        return str(uuid.uuid4())


class MockS3Client:
    def __init__(self):
        ...

    @staticmethod
    def put_object(*args, **kwargs):
        print("Putting object", args, kwargs)
        return True
