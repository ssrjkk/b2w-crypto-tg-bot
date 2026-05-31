"""Application exceptions."""


class PlatformException(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, code: str = "PLATFORM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class SubscriptionError(PlatformException):
    """Subscription-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "SUBSCRIPTION_ERROR")


class PaymentError(PlatformException):
    """Payment-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "PAYMENT_ERROR")


class PaymentExpiredError(PaymentError):
    """Payment invoice has expired."""

    def __init__(self):
        super().__init__("Payment invoice has expired")


class PaymentNotConfirmedError(PaymentError):
    """Payment not yet confirmed on chain."""

    def __init__(self):
        super().__init__("Payment not yet confirmed")


class InsufficientPaymentError(PaymentError):
    """Insufficient payment amount."""

    def __init__(self):
        super().__init__("Insufficient payment amount")


class TradingError(PlatformException):
    """Trading-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "TRADING_ERROR")


class QuoteError(TradingError):
    """Failed to get quote."""

    def __init__(self):
        super().__init__("Failed to get quote from DEX")


class ExecutionError(TradingError):
    """Failed to execute trade."""

    def __init__(self):
        super().__init__("Failed to execute trade")


class RiskError(PlatformException):
    """Risk management errors."""

    def __init__(self, message: str):
        super().__init__(message, "RISK_ERROR")


class RiskLimitExceededError(RiskError):
    """Risk limit exceeded."""

    def __init__(self, limit: str):
        super().__init__(f"Risk limit exceeded: {limit}")


class KillSwitchError(RiskError):
    """Kill switch activated."""

    def __init__(self):
        super().__init__("Kill switch activated - trading disabled")


class AirdropError(PlatformException):
    """Airdrop-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "AIRDROP_ERROR")


class ValidationError(PlatformException):
    """Input validation errors."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class UnauthorizedError(PlatformException):
    """Unauthorized access."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED")


class NotFoundError(PlatformException):
    """Resource not found."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "NOT_FOUND")
