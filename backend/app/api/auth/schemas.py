from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_token: str = Field(min_length=1)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    emp_no: str = Field(min_length=1)
    name: str = Field(min_length=1)
    email: EmailStr
    designation: str = Field(min_length=1)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee: EmployeeResponse
