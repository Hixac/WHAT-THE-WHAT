from typing import Any


class RecognitionError(BaseException):
    def __init__(self, url: str, params: dict[str, Any], message: str) -> None:
        self.url = url
        self.params = params
        self.message = message
        
        super().__init__(f"Error: {message}. Context: url {url}, params {params}")
