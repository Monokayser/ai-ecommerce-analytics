"""User-safe exception hierarchy for application services."""


class AppError(Exception):
    """Base exception whose message is safe to show to users."""


class DataLoadError(AppError):
    """Dataset loading or upload validation failed."""


class SchemaValidationError(AppError):
    """Dataset schema could not be interpreted safely."""


class QueryValidationError(AppError):
    """Generated query failed structural validation."""


class UnsafeQueryError(QueryValidationError):
    """Generated query attempted a prohibited operation."""


class QueryExecutionError(AppError):
    """A validated query could not be executed."""


class LLMResponseError(AppError):
    """An LLM response was unavailable or invalid."""


class ExportError(AppError):
    """Report or chart export failed."""
