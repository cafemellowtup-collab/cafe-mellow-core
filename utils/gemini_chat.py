import asyncio
import logging
from backend.core.titan_v3.unified_engine import get_titan_engine

logger = logging.getLogger(__name__)

# Global variable to hold the engine instance
_titan_engine_instance = None


def get_lazy_engine():
    """
    Lazy-loads the TITAN engine only when needed.
    Prevents server crash if Google Credentials are missing at startup.
    """
    global _titan_engine_instance
    if _titan_engine_instance is None:
        try:
            logger.info("Initializing TITAN v3 Engine...")
            _titan_engine_instance = get_titan_engine()
            logger.info("TITAN v3 Engine ready.")
        except Exception as e:
            logger.error(f"Failed to initialize TITAN v3: {e}")
            # Return None or a dummy to prevent immediate crash,
            # allowing the error to be handled during the chat request instead.
            raise e
    return _titan_engine_instance


async def stream_chat(user_message: str):
    """
    Adapter function to connect Chat UI -> TITAN v3 Engine.
    """
    try:
        # Initialize engine just-in-time
        engine = get_lazy_engine()

        # Process the query
        response = await engine.process_query(user_message)

        # Extract content
        if hasattr(response, "content"):
            yield response.content
        else:
            yield str(response)

    except Exception as e:
        logger.error(f"TITAN v3 Runtime Error: {e}")
        yield f"AI Error: {str(e)}\n(Check server logs for credentials issues)"


# --- Compatibility Stubs ---
def chat_with_gemini(message, *args, **kwargs):
    """Sync wrapper for legacy calls"""
    try:
        engine = get_lazy_engine()
        return asyncio.run(engine.process_query(message)).content
    except Exception as e:
        return f"System Error: {str(e)}"
