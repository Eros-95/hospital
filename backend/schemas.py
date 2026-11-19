from typing import Literal, Optional

from pydantic import BaseModel, Field

Gender = Literal["男", "女"]


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    gender: Gender
    age: int = Field(ge=0, le=150)
    phone: Optional[str] = None
    id_card: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    gender: Optional[Gender] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    phone: Optional[str] = None
    id_card: Optional[str] = None


class Patient(BaseModel):
    id: int
    name: str
    gender: str
    age: int
    phone: Optional[str] = None
    id_card: Optional[str] = None
    created_at: str
    updated_at: str
