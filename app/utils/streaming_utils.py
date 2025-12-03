"""
Streaming utilities for Server-Sent Events (SSE) responses.
Provides helpers for streaming AI responses in real-time.
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def format_sse_message(data: Dict[str, Any], event: Optional[str] = None) -> str:
    """
    Format data as Server-Sent Events (SSE) message.
    
    Args:
        data: Dictionary to send as JSON
        event: Optional event type
        
    Returns:
        Formatted SSE message string
    """
    message = ""
    if event:
        message += f"event: {event}\n"
    message += f"data: {json.dumps(data)}\n\n"
    return message


async def stream_response(
    content_generator: AsyncGenerator[str, None],
    include_metadata: bool = True
) -> AsyncGenerator[str, None]:
    """
    Stream AI response as SSE messages.
    
    Args:
        content_generator: Async generator yielding content chunks
        include_metadata: Whether to include metadata messages
        
    Yields:
        SSE-formatted messages
    """
    try:
        # Send start message
        if include_metadata:
            yield format_sse_message({
                "type": "start",
                "timestamp": asyncio.get_event_loop().time()
            })
        
        # Stream content chunks
        chunk_count = 0
        async for chunk in content_generator:
            chunk_count += 1
            yield format_sse_message({
                "type": "chunk",
                "content": chunk,
                "chunk_id": chunk_count,
                "done": False
            })
        
        # Send completion message
        yield format_sse_message({
            "type": "done",
            "content": "",
            "total_chunks": chunk_count,
            "done": True
        })
        
    except Exception as e:
        logger.error(f"Error in stream_response: {e}")
        # Send error message
        yield format_sse_message({
            "type": "error",
            "error": str(e),
            "done": True
        })


async def stream_ai_response(
    agent_stream,
    extract_text: bool = True
) -> AsyncGenerator[str, None]:
    """
    Wrapper for PydanticAI streaming responses.
    
    Args:
        agent_stream: PydanticAI stream result
        extract_text: Whether to extract text from structured responses
        
    Yields:
        Text chunks from the AI response
    """
    try:
        async for chunk in agent_stream:
            # PydanticAI returns different chunk types
            # We need to extract the text content
            if hasattr(chunk, 'data'):
                # Structured response
                if extract_text:
                    yield str(chunk.data)
                else:
                    yield chunk.data
            elif hasattr(chunk, 'content'):
                # Text response
                yield chunk.content
            elif hasattr(chunk, 'delta'):
                # Delta update
                yield chunk.delta
            else:
                # Fallback: convert to string
                yield str(chunk)
                
    except Exception as e:
        logger.error(f"Error in stream_ai_response: {e}")
        raise


async def collect_stream(stream: AsyncGenerator[str, None]) -> str:
    """
    Collect all chunks from a stream into a single string.
    Useful for testing or fallback scenarios.
    
    Args:
        stream: Async generator yielding string chunks
        
    Returns:
        Complete concatenated string
    """
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    return "".join(chunks)


class StreamBuffer:
    """
    Buffer for managing streaming responses with backpressure.
    Useful for rate-limiting or batching chunks.
    """
    
    def __init__(self, max_buffer_size: int = 100):
        self.buffer = []
        self.max_buffer_size = max_buffer_size
        
    async def add(self, chunk: str) -> Optional[str]:
        """
        Add chunk to buffer. Returns buffered content if threshold reached.
        
        Args:
            chunk: Text chunk to add
            
        Returns:
            Buffered content if ready to flush, None otherwise
        """
        self.buffer.append(chunk)
        
        if len(self.buffer) >= self.max_buffer_size:
            return self.flush()
        return None
    
    def flush(self) -> str:
        """
        Flush buffer and return all content.
        
        Returns:
            All buffered content as single string
        """
        content = "".join(self.buffer)
        self.buffer = []
        return content
