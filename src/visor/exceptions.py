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
    """HTTP 401 — the request was not authenticated.

    Raised when the API key is missing, malformed, or invalid. Check that
    ``VISOR_API_KEY`` is set to a valid key, or pass ``api_key`` explicitly
    when constructing the client.
    """


class ForbiddenError(VisorAPIError):
    """HTTP 403 — the request was authenticated but not authorized.

    Raised when a valid API key does not have permission to access the
    requested resource or perform the requested action. Contact Visor support
    if you believe you should have access.
    """


class NotFoundError(VisorAPIError):
    """404 — resource not found."""


class ValidationError(VisorAPIError):
    """400 — unknown_query_parameter or validation_error."""


class PaymentRequiredError(VisorAPIError):
    """402 — quota exceeded / payment required."""


class RateLimitError(VisorAPIError):
    """HTTP 429 — the API rate limit has been exceeded.

    Attributes:
        retry_after: Number of seconds to wait before retrying, or ``None``
            if the API did not include a usable ``Retry-After`` header. When
            present the value is derived from an integer seconds value or an
            HTTP-date header, whichever the API provides. Build your retry
            loop around this value:

                except RateLimitError as e:
                    wait = e.retry_after if e.retry_after is not None else 2 ** attempt
                    time.sleep(wait)
    """

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
