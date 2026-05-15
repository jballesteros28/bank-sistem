from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T


def ok(data: T, message: str = "OK") -> ApiResponse[T]:
    return ApiResponse(success=True, message=message, data=data)

