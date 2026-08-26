from abc import ABC, abstractmethod


class StorageRepositoryInterface(ABC):
    @abstractmethod
    def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Uploads a file and returns its public URL."""
        pass

    @abstractmethod
    def delete_file(self, file_url: str) -> bool:
        """Deletes a file based on its URL."""
        pass
