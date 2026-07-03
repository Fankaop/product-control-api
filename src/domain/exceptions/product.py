from core.exceptions import AppException


class ProductAlreadyAggregated(AppException):
    def __init__(self, unique_code: str) -> None:
        super().__init__(message=f'Product with id {unique_code} already aggregated',
                          status_code=400)
class ProductNotFound(AppException):
    def __init__(self, unique_code: str) -> None:
        super().__init__(message=f'Product with id {unique_code} not found',
                          status_code=404)

