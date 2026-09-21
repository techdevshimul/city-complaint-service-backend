from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=40)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=100)
    role: str = Field(default='user', pattern='^(user|admin)$')


class UpdateUser(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=40)
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class ForgotPassword(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    username: str
    full_name: str
    role: str
    is_active: bool


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str = Field(default='', max_length=250)


class CategoryOut(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=10, max_length=3000)
    location: str = Field(min_length=3, max_length=250)
    category_id: int
    priority: str = Field(default='medium', pattern='^(low|medium|high|urgent)$')
    image_url: Optional[str] = None


class ComplaintUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=120)
    description: Optional[str] = Field(default=None, min_length=10, max_length=3000)
    location: Optional[str] = Field(default=None, min_length=3, max_length=250)
    category_id: Optional[int] = None
    priority: Optional[str] = Field(default=None, pattern='^(low|medium|high|urgent)$')
    image_url: Optional[str] = None


class AdminComplaintUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern='^(pending|in_progress|resolved|rejected)$')
    priority: Optional[str] = Field(default=None, pattern='^(low|medium|high|urgent)$')
    assigned_to_id: Optional[int] = None
    resolution_note: Optional[str] = Field(default=None, max_length=1000)


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    note: str
    created_at: datetime


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    location: str
    image_url: Optional[str]
    priority: str
    status: str
    reporter_id: int
    category_id: int
    assigned_to_id: Optional[int]
    resolution_note: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    history: list[StatusHistoryOut] = []


class PaginatedComplaints(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int
    total_pages: int
