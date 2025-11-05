import logging
import os
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .dependencies import login_required
from .health import healthcheck_router
from .log_utils import request_scope_var
from .v2 import v2_router as v2_api_router
from .v2.services import ServiceException

if TYPE_CHECKING:
    from fastapi import Request

logger = logging.getLogger("api")


@asynccontextmanager
async def app_lifespan(_app):
    from .log_utils import setup_logging

    setup_logging()
    logger.info("Starting up")
    yield
    from .dependencies.database import ENGINE

    if ENGINE is not None:
        logger.info("Closing database connection")
        ENGINE.dispose()


app = FastAPI(
    docs_url="/docs",
    title="Data Canvas API",
    swagger_ui_parameters={
        "docExpansion": "none",
        "persistAuthorization": True,
        "tagsSorter": "alpha",
    },
    lifespan=app_lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://devdatacanvaswf.cisco.com",
    "https://devdatacanvaswf.cisco.com",
    "http://localhost:8080",
    "http://localhost:80",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.urandom(32).hex())

app.include_router(
    v2_api_router, prefix="/api/v2", dependencies=[Depends(login_required)]
)

app.include_router(healthcheck_router, prefix="/healthcheck")


@app.exception_handler(NoResultFound)
async def no_result_found_exception_handler(request: "Request", exc: NoResultFound):
    """
    This exception handler is used to catch sqlalchemy NoResultFound exceptions.
    It includes the error in the response body.
    """
    logger.error(
        "Assertion that a database query returns a single result failed request.url=%r request.method=%r",
        request.url,
        request.method,
    )
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content=jsonable_encoder({"detail": "Record not found"}),
    )


@app.exception_handler(MultipleResultsFound)
async def multiple_results_found_exception_handler(
    request: "Request", exc: MultipleResultsFound
):
    """
    This exception handler is more serious than NoResultFound, as it indicates a data integrity issue.

    I.e. calling .one() for a user returned multiple results.
    """
    logger.error(
        "Multiple records found when only one was expected request.url=%r request.method=%r",
        request.url,
        request.method,
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"detail": "Multiple records found"}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: "Request", exc: RequestValidationError):
    """
    This exception handler is used to catch validation errors that occur from incoming requests.
    It includes the errors in the response body as well as the original request body.
    """
    user = request.scope.get("user", None)
    username = user.username if user else "Unknown User"
    path_params = request.path_params

    logger.error(
        "Client from username=%r sent data not meeting the expected schema request.url=%s, path_params=%r, request.method=%r "
        "errors: %r\n"
        "received : %r",
        username,
        str(request.url),
        path_params,
        request.method,
        exc.errors(),
        exc.body,
    )

    error_message = ", ".join(
        [msg for msg in [e.get("msg") for e in exc.errors()] if msg]
    )

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": error_message, "body": exc.body}),
    )


@app.exception_handler(StarletteHTTPException)
async def unauthorized_exception_handler(
    request: "Request", exc: StarletteHTTPException
):
    """
    Listen for HTTP 401 and 403 errors and log them with additional information.
    """

    user = request.scope.get("user", None)
    username = user.username if user else "Unknown User"
    path_params = request.path_params

    match exc.status_code:
        case 401 | 403:
            logger.warning(
                "HTTP_%d username=%r request.url=%s, path_params=%r, request.method=%r",
                exc.status_code,
                username,
                str(request.url),
                path_params,
                request.method,
            )
        case _:
            ...  # Do nothing

    return await http_exception_handler(request, exc)


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(
    request: "Request", exc: ResponseValidationError
):
    """
    This exception handler is used to catch validation errors that occur from outgoing responses.
    It includes the errors in the response body as well as the original response body.
    """
    user = request.scope.get("user", None)
    username = user.username if user else "Unknown User"
    path_params = request.path_params

    logger.error(
        "Server attempted to send data to username=%r not meeting the expected schema request.url=%s, path_params=%r, request.method=%r "
        "errors: %r\n"
        "returned : %r",
        username,
        str(request.url),
        path_params,
        request.method,
        exc.errors(),
        exc.body,
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(ServiceException)
async def service_exception_handler(request: "Request", exc: ServiceException):
    """
    This exception handler is used to catch ServiceException exceptions (raised by our 'Service' classes).
    This exception indicates the appropriate code and detail message to return to the client.
    """
    msg = (
        "Service Exception request.url=%r request.method=%r exc.code=%r exc.msg=%r",
        request.url,
        request.method,
        exc.code,
        exc.msg,
    )
    logger.error(msg)
    return JSONResponse(
        status_code=exc.code,
        content=jsonable_encoder({"detail": exc.msg}),
    )


@app.middleware("http")
async def profile_slow_response(request: "Request", call_next):
    start_time = time.time()
    response = await call_next(request)
    elapsed_time = time.time() - start_time
    if elapsed_time > 1:
        logger.info(
            "SLOW RESPONSE | Request to %s %s%s %s took %.3f seconds",
            request.method,
            request.url.path,
            request.url.query,
            request.path_params,
            elapsed_time,
        )
    return response


@app.middleware("http")
async def add_extra_log_info(request: "Request", call_next):
    request_scope_var.set(request.scope)
    response = await call_next(request)

    return response
