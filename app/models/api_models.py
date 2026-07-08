from typing import Any
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool
    data: Any
    error: dict | None