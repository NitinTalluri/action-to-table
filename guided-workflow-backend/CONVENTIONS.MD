# Coding and Architecture Conventions

This is a FastAPI project. This influences how the project is structured.

New code should go in the V2 directory.

## FastAPI Routes

1. Routes should be defined in the `api/v2/routers` directory.
2. Routes are separated by business objects. For example, engagements is located in `api/v2/routers/engagements.py`.
3. When defining routes, create an APIRouter and define the routes in that router. If you want to use a module, for example, 'admin', then in __init__.py, create a new APIRouter that includes the 'admin' prefix and security dependencies. For nested routes the __init__.py file should include the nested routers. Be sure to use aliases for the nested routers to avoid conflicts.

### FastAPI Route Dependencies

1. All routes, except /healthcheck require User Authentication. This is enforced at the '/api/v2' level with the dependency `decode_bearer`.
2. To access the decoded user, use the dependency `GetUserDep`. This is a chained dependency that uses the `decode_bearer` dependency, SQLAlchemy, and the User model to get the user from the token, correlate it with the user in the database, and return the user object.
3. To access a SQLAlchemy session, use the dependency `GetSessionDep`.
4. It is encouraged to refactor common operations that must run before the route into a dependency. For example, if you always check that a user has permission to access a resource, create a dependency that checks the permission and use it in the route.
5. Other notable dependencies include `GetSettingsDep` (Get App Settings), `PrefectClientDep` (Prefect Client), `S3ClientDep` (S3 Client)

## SQLAlchemy Models
1. To avoid metadata conflicts, all models should inherit from the `V2MetadataBase` class in `api/v2/orm/base.py`.
2. Typically, these correspond to Pydantic models in the `api/v2/models` directory.
3. If there is a clear 1:1 mapping, you can inherit or override the `V2MetadataBase` `create_from_model`, `update_from_model`, and `soft_delete` methods.
4. In this application, records are not deleted. They are instead marked as is_deleted = 'T' or 'F'. 

## SQLAlchemy and SQLModel
1. When querying, you may find sqlmodel's `select` more useful than the SQLAlchemy `select` method. This is because it will handle using scalars as well as improved typing support.
2. Use the 2.0 style of querying using `select` and `.where` rather than `.query` and `.filter`. This will prevent unnecessary refactoring when upgrading 

## Pydantic Models
1. Pydantic models should be defined in the `api/v2/models` directory. Ensure that these models are compatible with the current version of Pydantic.
2. Pydantic models should be used to validate incoming data and to serialize outgoing data. They have the added benefit of being able to be used in the FastAPI documentation.
3. To perform additional validation or transformation, use a validator decorator or a root_validator decorator. This allows you to define custom validation logic that will run before or after the standard validation logic.

## FastAPI Error Handling
1. This application is configured to handle the following exceptions. To opt-out, wrap a statement in a try-except block and handle the exception.
    - NoResultFound
      - This simplifies the code by allowing you to assume that a query will always return a result. Use `.one()` instead of `.one_or_none()`. It returns a 404 error if no result is found.
    - MultipleResultsFound
      - This handles the case where a query returns multiple results. This is not expected in this application. If it occurs, it is a data integrity issue. This returns a 500 error.
    - RequestValidationError
      - This is raised when the request data does not match the Pydantic model. This returns a 422 error as well logs a warning.
    - ResponseValidationError
      - This is raised when the response data does not match the Pydantic model. This returns a 500 error as well logs a warning. The server is trying to return data that does not match the expected schema.

## Importing Modules
1. As the codebase has grown, it has become necessary to import modules in a consistent way. This is to avoid circular imports and to make it easier to reference a model.
2. Each module should import its children and alias as needed.
3. If the number of imports is large, consider defining the ``__all__`` variable to make it easier to import the module. 