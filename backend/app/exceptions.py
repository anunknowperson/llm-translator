from fastapi import Request, status
from fastapi.responses import JSONResponse


# Обработка ошибок: кастомные исключения + обработчики, понятный JSON и корректные HTTP-статусы
class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidPromptError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Текст для перевода пуст или некорректен"


class MLServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_message = "ML-сервис временно недоступен, попробуйте позже"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "message": "Произошла непредвиденная ошибка"},
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
