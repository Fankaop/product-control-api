from core.exceptions import AppException


class WebhookNotFound(AppException):
    def __init__(self, webhook_id: int) -> None:
        super().__init__(message=f'Webhook with id {webhook_id} not found', status_code=404)


class WebhookAlreadyInactive(AppException):
    def __init__(self, webhook_id: int) -> None:
        super().__init__(message=f'Webhook with id {webhook_id} is already inactive', status_code=400)
