from enum import Enum


class OutcomeCodes(Enum):
    # Generic
    SUCCESS = "0000"
    ERROR = "1000"

    # Signup
    ERROR_SIGNUP_USER_NOT_WHITELISTED = "1001"
    ERROR_SIGNUP_USER_ALREADY_EXISTS = "1002"

    def is_error(self) -> bool:
        return self.value.startswith("1")

    @property
    def error_message(self) -> str:
        if self.is_error():
            return f"({self.value}) {self.name}"

    @property
    def error_json(self) -> dict:
        if self.is_error():
            return {"error": self.name, "error_code": self.value}
