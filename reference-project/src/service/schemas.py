"""Контракт API. Схема — это граница системы: всё, что не прошло валидацию,
не должно доходить до модели. Ограничения (ge/le) взяты из данных,
а не выдуманы: они ловят мусор до того, как он станет тихо неверным предсказанием.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ContractType = Literal["month-to-month", "one_year", "two_year"]
InternetService = Literal["fiber", "dsl", "none"]
PaymentMethod = Literal["electronic_check", "mailed_check", "bank_transfer", "credit_card"]


class Customer(BaseModel):
    tenure_months: int = Field(..., ge=0, le=200, description="Стаж клиента в месяцах")
    monthly_charges: float = Field(..., ge=0, le=1000)
    total_charges: Optional[float] = Field(None, ge=0)
    contract_type: ContractType
    internet_service: InternetService
    payment_method: PaymentMethod
    num_support_calls: int = Field(..., ge=0, le=100)
    has_tech_support: int = Field(..., ge=0, le=1)
    is_senior: int = Field(..., ge=0, le=1)
    avg_monthly_gb: float = Field(..., ge=0, le=5000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tenure_months": 3,
                    "monthly_charges": 89.4,
                    "total_charges": 268.2,
                    "contract_type": "month-to-month",
                    "internet_service": "fiber",
                    "payment_method": "electronic_check",
                    "num_support_calls": 4,
                    "has_tech_support": 0,
                    "is_senior": 0,
                    "avg_monthly_gb": 61.3,
                }
            ]
        }
    }


class BatchRequest(BaseModel):
    # Верхняя граница обязательна: без неё один запрос на миллион строк
    # положит сервис. Отказ с понятным 422 лучше, чем OOM.
    items: list[Customer] = Field(..., min_length=1, max_length=1000)


class Prediction(BaseModel):
    churn_probability: float
    churn: int
    threshold: float
    model_version: str


class BatchPrediction(BaseModel):
    predictions: list[Prediction]
    count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
