"""
LangGraph pipeline orchestrator for the Medical Assistant.

This module builds and compiles the StateGraph that orchestrates
the 4-step Agentic RAG pipeline:
- Step A: Intent Extraction
- Step B: Entity Resolution
- Step C: Database Query
- Step D: Response Generation
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from app.graph.state import ConversationState, INTENT_CHITCHAT, INTENT_ANALYTICS
from app.graph.nodes import (
    extract_intent,
    resolve_entities,
    query_database,
    generate_response,
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton instances (thread-safe for async)
_connection_pool: AsyncConnectionPool = None
_checkpointer: AsyncPostgresSaver = None
_compiled_graph = None


def route_by_intent(state: ConversationState) -> str:
    """
    Conditional routing based on extracted intent.

    Routes:
    - error -> generate_response (graceful degradation)
    - chitchat -> generate_response (skip B, C)
    - analytics -> query_database (skip B)
    - search/detail/summarize -> resolve_entities (full pipeline)
    """
    # Handle errors - go straight to response
    if state.get("error"):
        logger.warning("Error detected, routing to generate_response")
        return "generate_response"

    intent = state.get("intent")

    if intent == INTENT_CHITCHAT:
        logger.info("Chitchat intent, skipping entity resolution and database query")
        return "generate_response"  # Skip B, C

    if intent == INTENT_ANALYTICS:
        logger.info("Analytics intent, skipping entity resolution")
        return "query_database"  # Skip B (no entity resolution needed)

    logger.info(f"Intent '{intent}', proceeding to entity resolution")
    return "resolve_entities"


def build_graph() -> StateGraph:
    """
    Build the LangGraph state machine.

    Graph structure:
    extract_intent -> [conditional routing]
        -> resolve_entities -> query_database -> generate_response -> END
        -> query_database -> generate_response -> END (analytics)
        -> generate_response -> END (chitchat/errors)
    """
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("extract_intent", extract_intent)
    graph.add_node("resolve_entities", resolve_entities)
    graph.add_node("query_database", query_database)
    graph.add_node("generate_response", generate_response)

    # Set entry point
    graph.set_entry_point("extract_intent")

    # Conditional edges from extract_intent
    graph.add_conditional_edges(
        "extract_intent",
        route_by_intent,
        {
            "resolve_entities": "resolve_entities",
            "query_database": "query_database",
            "generate_response": "generate_response",
        },
    )

    # Linear edges for the rest of the pipeline
    graph.add_edge("resolve_entities", "query_database")
    graph.add_edge("query_database", "generate_response")
    graph.add_edge("generate_response", END)

    return graph


def _get_db_url() -> str:
    """Get and convert DATABASE_URL to psycopg3 format."""
    db_url = settings.DATABASE_URL

    # If using asyncpg format, convert for psycopg
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")

    # If using SQLAlchemy format, convert for psycopg
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")

    return db_url


async def get_connection_pool() -> AsyncConnectionPool:
    """Get or create singleton connection pool."""
    global _connection_pool
    if _connection_pool is None:
        db_url = _get_db_url()
        logger.info("Creating PostgreSQL connection pool...")
        _connection_pool = AsyncConnectionPool(conninfo=db_url, open=False)
        await _connection_pool.open()
        logger.info("✅ PostgreSQL connection pool opened")
    return _connection_pool


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create singleton checkpointer.

    Uses PostgreSQL for persistent conversation state.
    Creates tables with autocommit connection (required for CREATE INDEX CONCURRENTLY).
    """
    global _checkpointer
    if _checkpointer is None:
        db_url = _get_db_url()

        # First, try to run setup with a direct autocommit connection
        # This is required because CREATE INDEX CONCURRENTLY cannot run in a transaction
        import psycopg
        import asyncio

        logger.info("Running checkpointer setup with autocommit...")
        try:
            # Add timeout to prevent hanging
            async with asyncio.timeout(10):
                async with await psycopg.AsyncConnection.connect(
                    db_url, autocommit=True
                ) as conn:
                    setup_checkpointer = AsyncPostgresSaver(conn)
                    await setup_checkpointer.setup()
                    logger.info("✅ Checkpoint tables created successfully")
        except asyncio.TimeoutError:
            logger.warning("Checkpointer setup timed out - tables may already exist")
        except Exception as e:
            # Tables might already exist, or other issue - continue anyway
            logger.warning(f"Checkpointer setup note: {type(e).__name__}: {e}")

        # Now create the pool-based checkpointer for runtime use
        pool = await get_connection_pool()
        logger.info("Initializing PostgreSQL checkpointer with connection pool...")
        _checkpointer = AsyncPostgresSaver(pool)
        logger.info("✅ PostgreSQL checkpointer initialized")

    return _checkpointer


async def get_compiled_graph():
    """
    Get or create singleton compiled graph.

    The graph is compiled once at startup and reused for all requests.
    This includes the checkpointer for persistent state.
    """
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_graph()
        checkpointer = await get_checkpointer()
        _compiled_graph = graph.compile(checkpointer=checkpointer)
        logger.info("✅ LangGraph pipeline compiled with PostgreSQL checkpointer")
    return _compiled_graph
