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


async def stream_response_with_mermaid_buffering(
    content_generator: AsyncGenerator[str, None],
    include_metadata: bool = True
) -> AsyncGenerator[str, None]:
    """
    Stream AI response with Mermaid chart buffering.
    
    Buffers Mermaid code blocks completely before sending to prevent
    frontend rendering errors from incomplete charts.
    
    Args:
        content_generator: Async generator yielding content chunks
        include_metadata: Whether to include metadata messages
        
    Yields:
        SSE-formatted messages with buffered Mermaid charts
    """
    # Safety limits to prevent infinite buffering
    MAX_MERMAID_BUFFER_SIZE = 3000  # characters
    MAX_BUFFER_CHUNKS = 100  # max chunks to buffer
    
    try:
        # Send start message
        if include_metadata:
            yield format_sse_message({
                "type": "start",
                "timestamp": asyncio.get_event_loop().time()
            })
        
        # Buffering state
        in_mermaid_block = False
        mermaid_buffer = ""
        buffer_chunk_count = 0
        total_chunk_count = 0
        
        async for chunk in content_generator:
            total_chunk_count += 1
            
            # Detect start of Mermaid block
            if "```mermaid" in chunk and not in_mermaid_block:
                in_mermaid_block = True
                mermaid_buffer = chunk
                buffer_chunk_count = 1
                logger.debug("Started buffering Mermaid chart")
                continue
            
            # If we're in a Mermaid block
            if in_mermaid_block:
                mermaid_buffer += chunk
                buffer_chunk_count += 1
                
                # Safety check: buffer too large
                if len(mermaid_buffer) > MAX_MERMAID_BUFFER_SIZE:
                    logger.warning(f"Mermaid buffer exceeded size limit ({len(mermaid_buffer)} chars), flushing")
                    yield format_sse_message({
                        "type": "chunk",
                        "content": mermaid_buffer,
                        "chunk_id": total_chunk_count,
                        "done": False,
                        "warning": "Large Mermaid block"
                    })
                    in_mermaid_block = False
                    mermaid_buffer = ""
                    buffer_chunk_count = 0
                    continue
                
                # Safety check: buffering too many chunks
                if buffer_chunk_count > MAX_BUFFER_CHUNKS:
                    logger.warning(f"Mermaid buffer exceeded chunk limit ({buffer_chunk_count} chunks), flushing")
                    yield format_sse_message({
                        "type": "chunk",
                        "content": mermaid_buffer,
                        "chunk_id": total_chunk_count,
                        "done": False,
                        "warning": "Incomplete Mermaid block"
                    })
                    in_mermaid_block = False
                    mermaid_buffer = ""
                    buffer_chunk_count = 0
                    continue
                
                # Check if Mermaid block is complete
                # Look for closing ``` that's not part of ```mermaid
                if "```" in chunk and chunk.strip() != "```mermaid":
                    # Complete Mermaid block - send it all at once
                    logger.debug(f"Completed Mermaid chart ({len(mermaid_buffer)} chars, {buffer_chunk_count} chunks)")
                    yield format_sse_message({
                        "type": "chunk",
                        "content": mermaid_buffer,
                        "chunk_id": total_chunk_count,
                        "done": False
                    })
                    in_mermaid_block = False
                    mermaid_buffer = ""
                    buffer_chunk_count = 0
                continue
            
            # Not in Mermaid block - stream normally
            yield format_sse_message({
                "type": "chunk",
                "content": chunk,
                "chunk_id": total_chunk_count,
                "done": False
            })
        
        # End of stream - flush any remaining Mermaid buffer
        if in_mermaid_block and mermaid_buffer:
            logger.warning("Stream ended with incomplete Mermaid block, flushing")
            yield format_sse_message({
                "type": "chunk",
                "content": mermaid_buffer,
                "chunk_id": total_chunk_count + 1,
                "done": False,
                "warning": "Incomplete Mermaid block at end of stream"
            })
        
        # Send completion message
        yield format_sse_message({
            "type": "done",
            "content": "",
            "total_chunks": total_chunk_count,
            "done": True
        })
        
    except Exception as e:
        logger.error(f"Error in stream_response_with_mermaid_buffering: {e}")
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
