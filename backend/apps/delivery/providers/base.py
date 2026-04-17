from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    @abstractmethod
    def send_document(self, phone: str, file_url: str, caption: str) -> str:
        """Send a document to a WhatsApp number.

        Args:
            phone: WhatsApp phone number (e.g. "77001234567")
            file_url: Public URL to the document (presigned MinIO URL)
            caption: Accompanying text message

        Returns:
            External message ID from the provider
        """
        ...
