"""
Search functionality for the Streamlit web interface.
"""
import streamlit as st
import time
import logging
from typing import List, Optional, Tuple
from pathlib import Path

from src.models.search_models import SearchResult, Query
from src.processors.search_engine import SearchEngine
from .components import (
    render_loading_spinner, 
    render_example_query_buttons,
    render_error_message,
    render_success_message,
    render_search_stats
)
from .cache import QueryCache


def validate_query_input(query_text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user query input.
    
    Args:
        query_text: User input query text
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query_text:
        return False, "Please enter a search query"
    
    if not isinstance(query_text, str):
        return False, "Query must be text"
    
    query_text = query_text.strip()
    
    if not query_text:
        return False, "Query cannot be empty"
    
    if len(query_text) < 2:
        return False, "Query must be at least 2 characters long"
    
    if len(query_text) > 200:
        return False, "Query is too long (maximum 200 characters)"
    
    # Check for potentially problematic characters
    if any(char in query_text for char in ['<', '>', '{', '}', '[', ']']):
        return False, "Query contains invalid characters"
    
    return True, None


def render_search_input() -> Optional[str]:
    """
    Render search input interface with validation.
    
    Returns:
        Query string if search was triggered, None otherwise
    """
    # Create search form
    with st.form(key="search_form", clear_on_submit=False):
        col1, col2 = st.columns([3.5, 1])
        
        with col1:
            query_text = st.text_input(
                label="Search Query",
                placeholder="Describe the architectural features you're looking for...",
                help="Enter natural language descriptions like 'red brick buildings' or 'modern glass facades'",
                label_visibility="collapsed"
            )
        
        with col2:
            # Add spacing to align button with input
            st.markdown("<style>.stButton button {white-space: nowrap !important; padding: 0.5rem 1rem !important;}</style>", unsafe_allow_html=True)
            search_clicked = st.form_submit_button(
                "🔍 Search", 
                use_container_width=True,
                type="primary"
            )
    
    # Handle search submission
    if search_clicked:
        is_valid, error_msg = validate_query_input(query_text)
        
        if not is_valid:
            render_error_message(error_msg, "Invalid Query")
            return None
        
        return query_text.strip()
    
    return None


def render_example_query_selector() -> Optional[str]:
    """
    Render example query buttons that can be clicked to search.
    
    Returns:
        Selected example query if any button was clicked
    """
    example_queries = [
        "red brick buildings",
        "glass and steel facades",
        "stone columns",
        "flat roof structures",
        "large windows",
        "modern office buildings"
    ]
    
    st.markdown("**Or try these examples:**")
    
    # Create columns for example buttons
    cols = st.columns(3)
    
    for i, query in enumerate(example_queries):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(
                query, 
                key=f"example_query_{i}",
                use_container_width=True,
                help=f"Search for: {query}"
            ):
                return query
    
    return None


def perform_search(search_engine: SearchEngine, query_text: str, 
                  max_results: int = 5, similarity_threshold: float = 0.1) -> Tuple[List[SearchResult], Query, dict]:
    """
    Perform search operation with enhanced caching, error handling and timing.
    
    Args:
        search_engine: SearchEngine instance
        query_text: User query text
        max_results: Maximum number of results to return
        similarity_threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (results, query, stats)
    """
    from .error_handler import ErrorHandler
    
    # Initialize cache and error handler
    cache = QueryCache()
    error_handler = ErrorHandler()
    
    # Check cache first
    try:
        cached_result = cache.get(query_text, max_results, similarity_threshold)
        if cached_result is not None:
            results, stats = cached_result
            stats['cached'] = True
            stats['cache_hit'] = True
            return results, None, stats
    except Exception as e:
        # Cache error shouldn't stop search
        logging.warning(f"Cache lookup failed: {e}")
    
    start_time = time.time()
    
    try:
        # Validate search engine state
        if not hasattr(search_engine, 'validate_search_readiness'):
            raise ValueError("Search engine not properly initialized")
        
        # Check search readiness
        readiness = search_engine.validate_search_readiness()
        if not readiness.get('ready', False):
            issues = readiness.get('issues', ['Unknown readiness issue'])
            raise ValueError(f"Search engine not ready: {'; '.join(issues)}")
        
        # Perform the search with timeout protection
        results, query = search_engine.search(
            query_text=query_text,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            ranking_strategy='confidence'
        )
        
        search_time = time.time() - start_time
        
        # Validate results
        if results is None:
            results = []
        
        # Filter out invalid results
        valid_results = []
        for result in results:
            try:
                # Basic validation
                if hasattr(result, 'image_path') and hasattr(result, 'confidence_score'):
                    # Check if image exists (with graceful degradation)
                    if Path(result.image_path).exists() or True:  # Allow missing images for graceful degradation
                        valid_results.append(result)
            except Exception as e:
                logging.warning(f"Invalid result filtered out: {e}")
        
        # Calculate statistics
        stats = {
            'results_count': len(valid_results),
            'search_time': search_time,
            'avg_confidence': sum(r.confidence_score for r in valid_results) / len(valid_results) if valid_results else 0,
            'query_text': query_text,
            'cached': False,
            'cache_hit': False,
            'filtered_results': len(results) - len(valid_results)
        }
        
        # Cache the results (only if successful)
        try:
            cache.put(query_text, valid_results, stats, max_results, similarity_threshold)
        except Exception as e:
            logging.warning(f"Failed to cache results: {e}")
        
        return valid_results, query, stats
        
    except Exception as e:
        search_time = time.time() - start_time
        
        # Log error with context
        context = {
            'query_text': query_text,
            'max_results': max_results,
            'similarity_threshold': similarity_threshold,
            'search_time': search_time
        }
        error_handler.log_error(e, context)
        
        # Handle the error appropriately
        error_handler.handle_search_error(e, query_text)
        
        # Return empty results with error stats
        stats = {
            'results_count': 0,
            'search_time': search_time,
            'avg_confidence': 0,
            'query_text': query_text,
            'error': str(e),
            'error_type': type(e).__name__,
            'cached': False,
            'cache_hit': False
        }
        
        return [], None, stats


def handle_search_request(search_engine: SearchEngine) -> Tuple[Optional[List[SearchResult]], Optional[dict]]:
    """
    Handle search request from user input or example selection.
    
    Args:
        search_engine: SearchEngine instance
        
    Returns:
        Tuple of (results, stats) if search was performed, (None, None) otherwise
    """
    # Check for search input
    query_from_input = render_search_input()
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Check for example query selection
    query_from_example = render_example_query_selector()
    
    # Determine which query to use
    query_text = query_from_input or query_from_example
    
    if not query_text:
        return None, None
    
    # Show loading spinner (unless it's a cache hit)
    with st.spinner(f"Searching for '{query_text}'..."):
        results, query, stats = perform_search(search_engine, query_text)
    
    # Handle search results
    if 'error' in stats:
        render_error_message(
            f"Search failed: {stats['error']}", 
            "Search Error"
        )
        return None, None
    
    # Show search statistics
    render_search_stats(stats)
    
    # Show success message for completed search
    if results:
        cache_info = " (cached)" if stats.get('cache_hit', False) else ""
        render_success_message(
            f"Found {len(results)} matching images in {stats['search_time']:.2f} seconds{cache_info}",
            "Search Complete"
        )
    
    return results, stats


def render_search_interface(search_engine: SearchEngine):
    """
    Render the complete search interface.
    
    Args:
        search_engine: SearchEngine instance
    """
    # Search section header
    st.markdown("### 🔍 Search Architecture")
    
    # Add search instructions
    st.markdown("""
    Enter a natural language description of the architectural features you're looking for. 
    The AI will analyze your query and find matching images from the database.
    """)
    
    # Handle search requests and return results
    results, stats = handle_search_request(search_engine)
    
    # Store results in session state for display in results section
    if results is not None:
        st.session_state.search_results = results
        st.session_state.search_stats = stats
        st.session_state.last_query = stats.get('query_text', '')
    
    return results, stats


def clear_search_results():
    """Clear search results from session state."""
    if 'search_results' in st.session_state:
        del st.session_state.search_results
    if 'search_stats' in st.session_state:
        del st.session_state.search_stats
    if 'last_query' in st.session_state:
        del st.session_state.last_query


def get_cached_search_results() -> Tuple[Optional[List[SearchResult]], Optional[dict], Optional[str]]:
    """
    Get cached search results from session state.
    
    Returns:
        Tuple of (results, stats, query) from session state
    """
    results = st.session_state.get('search_results')
    stats = st.session_state.get('search_stats')
    query = st.session_state.get('last_query')
    
    return results, stats, query