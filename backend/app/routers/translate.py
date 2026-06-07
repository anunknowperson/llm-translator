import asyncio

from celery.result import AsyncResult
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.celery_app import celery_app
from app.exceptions import InvalidPromptError
from app.schemas import TaskEnqueuedResponse, TaskResultPayload, TaskStatusResponse, TranslateRequest
from app.tasks import translate_task

router = APIRouter(prefix="/translate", tags=["translate"])

_WS_POLL_INTERVAL_SECONDS = 1.0
_TERMINAL_STATES = {"SUCCESS", "FAILURE"}


def _build_status_response(task_id: str) -> TaskStatusResponse:
    async_result = AsyncResult(task_id, app=celery_app)

    if async_result.state == "FAILURE":
        return TaskStatusResponse(task_id=task_id, status="FAILURE", error=str(async_result.result))

    if async_result.state == "SUCCESS":
        return TaskStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            result=TaskResultPayload(**async_result.result),
        )

    return TaskStatusResponse(task_id=task_id, status=async_result.state)


@router.post("", response_model=TaskEnqueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_translation(payload: TranslateRequest) -> TaskEnqueuedResponse:
    if not payload.text.strip():
        raise InvalidPromptError("Текст для перевода не может быть пустым")

    async_result = translate_task.delay(
        payload.text, payload.source_lang.value, payload.target_lang.value, payload.creativity
    )
    return TaskEnqueuedResponse(task_id=async_result.id, status="PENDING")


# Polling: основной способ проверки статуса задачи
@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    return _build_status_response(task_id)


# (*) Проверка статуса задачи посредством WebSocket: сервер сам опрашивает Celery result backend
# и проталкивает обновления клиенту, пока задача не перейдёт в терминальное состояние (SUCCESS/FAILURE)
@router.websocket("/ws/{task_id}")
async def task_status_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            payload = _build_status_response(task_id)
            await websocket.send_json(payload.model_dump(mode="json"))

            if payload.status in _TERMINAL_STATES:
                await websocket.close()
                return

            await asyncio.sleep(_WS_POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
