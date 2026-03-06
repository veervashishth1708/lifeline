import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class N8NService:
    @staticmethod
    async def trigger_sos_webhook(payload: dict):
        """
        Trigger n8n webhook with SOS alert details.
        Retries up to 3 times on failure.
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        settings.N8N_WEBHOOK_URL,
                        json=payload,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    logger.info(f"Successfully triggered n8n webhook for device {payload.get('device_id')}")
                    return True
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    logger.warning(f"Attempt {attempt + 1} failed to trigger n8n webhook: {str(e)}")
                    if attempt == 2:
                        logger.error(f"Failed to trigger n8n webhook after 3 attempts.")
            return False

n8n_service = N8NService()
