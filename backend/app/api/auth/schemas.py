from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_token: str = Field(min_length=1)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    emp_no: str | None = None
    name: str = Field(min_length=1)
    email: EmailStr
    designation: str = Field(min_length=1)
    is_admin: bool = False
    can_manage_feed_sources: bool = False


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee: EmployeeResponse
