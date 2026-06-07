import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


# Валидация: строгие Pydantic-схемы с типами, ограничениями, примерами и описаниями
class Language(str, Enum):
    auto = "auto"  # автоопределение языка — допустимо только для source_lang
    en = "en"
    ru = "ru"
    de = "de"
    fr = "fr"
    es = "es"
    zh = "zh"
    it = "it"
    pt = "pt"
    ja = "ja"
    ko = "ko"
    ar = "ar"
    tr = "tr"
    pl = "pl"
    nl = "nl"
    sv = "sv"
    uk = "uk"
    cs = "cs"
    el = "el"
    hi = "hi"
    id_ = "id"
    vi = "vi"
    th = "th"
    fi = "fi"
    da = "da"
    no = "no"
    ro = "ro"
    hu = "hu"


class TranslateRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Текст, который нужно перевести",
        examples=["Hello, how are you?"],
    )
    source_lang: Language = Field(
        default=Language.auto,
        description="Язык исходного текста, либо 'auto' для автоопределения",
    )
    target_lang: Language = Field(
        default=Language.ru, description="Язык, на который нужно перевести"
    )
    creativity: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Креативность перевода (соответствует temperature модели), 0.0 — точный перевод, 1.0 — творческий",
        examples=[0.3],
    )

    @field_validator("target_lang")
    @classmethod
    def _target_lang_not_auto(cls, value: Language) -> Language:
        if value == Language.auto:
            raise ValueError("target_lang не может быть 'auto' — укажите конкретный язык назначения")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Hello, how are you?",
                    "source_lang": "en",
                    "target_lang": "ru",
                    "creativity": 0.3,
                }
            ]
        }
    )


class TaskEnqueuedResponse(BaseModel):
    task_id: str = Field(..., description="Идентификатор асинхронной задачи перевода")
    status: str = Field(default="PENDING", description="Текущий статус задачи")


class TaskResultPayload(BaseModel):
    source_text: str
    translated_text: str
    source_lang: str = Field(
        ..., description="Фактический язык исходного текста (определённый моделью, если был выбран 'auto')"
    )
    target_lang: Language
    creativity: float


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str = Field(
        ..., description="PENDING | STARTED | SUCCESS | FAILURE", examples=["SUCCESS"]
    )
    result: TaskResultPayload | None = None
    error: str | None = None


class TranslationHistoryItem(BaseModel):
    id: uuid.UUID
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: Language
    creativity: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranslationHistoryPage(BaseModel):
    items: list[TranslationHistoryItem]
    total: int
    limit: int
    offset: int


class LanguagePairStat(BaseModel):
    source_lang: str
    target_lang: str
    count: int


class DailyStat(BaseModel):
    date: str
    count: int


class StatsResponse(BaseModel):
    total_translations: int
    by_language_pair: list[LanguagePairStat]
    by_day: list[DailyStat]


class HealthComponent(BaseModel):
    name: str
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str = Field(..., description="ok | degraded")
    components: list[HealthComponent]
