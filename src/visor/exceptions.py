class VisorError(Exception):
    """Base exception for all visor-python errors."""


class VisorAPIError(VisorError):
    """Raised when the API returns a 4xx or 5xx response."""

    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{status_code}] {error_code}: {message}")


class AuthError(VisorAPIError):
    """401 — authentication failed."""


class ForbiddenError(VisorAPIError):
    """403 — access denied."""


class NotFoundError(VisorAPIError):
    """404 — resource not found."""


class ValidationError(VisorAPIError):
    """400 — unknown_query_parameter or validation_error."""


class PaymentRequiredError(VisorAPIError):
    """402 — quota exceeded / payment required."""


class RateLimitError(VisorAPIError):
    """429 — rate limit exceeded."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(status_code, error_code, message)


class VisorTransportError(VisorError):
    """Raised on network-level failures (timeout, connection refused)."""
