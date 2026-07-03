from core.exceptions import AppException


class BatchNotFound(AppException):
    def __init__(self, batch_id: int) -> None:
        super().__init__(message=f'Batch with id {batch_id} not found', status_code=404)


class BatchAlreadyClosed(AppException):
    def __init__(self, batch_id: int) -> None:
        super().__init__(message=f'Batch with id {batch_id} already closed', status_code=400)


class DuplicateBatch(AppException):
    def __init__(self, batch_number: int, batch_date: str) -> None:
        super().__init__(
            message=f'Batch {batch_number} on {batch_date} already exists',
            status_code=409,
        )
