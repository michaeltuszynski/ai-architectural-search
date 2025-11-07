"""
Caching and performance optimization for the Streamlit web interface.
"""
import streamlit as st
import hashlib
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from ..models.search_models import SearchResult, Query


class QueryCache:
    """
    Cache for search queries and results to improve response times.
    """
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 30):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of cached queries
            ttl_minutes: Time-to-live for cached results in minutes
        """
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache in session state if not exists
        if 'query_cache' not in st.session_state:
            st.session_state.query_cache = {}
        
        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_queries': 0
            }
    
    def _generate_cache_key(self, query_text: str, max_results: int, similarity_threshold: float) -> str:
        """
        Generate a unique cache key for a query.
        
        Args:
            query_text: Search query text
            max_results: Maximum results requested
            similarity_threshold: Similarity threshold used
            
        Returns:
            Unique cache key string
        """
        # Normalize query text
        normalized_query = query_text.lower().strip()
        
        # Create cache key from query parameters
        cache_input = f"{normalized_query}|{max_results}|{similarity_threshold:.3f}"
        
        # Generate hash for consistent key
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def get(self, query_text: str, max_results: int = 5, similarity_threshold: float = 0.1) -> Optional[Tuple[List[SearchResult], dict]]:
        """
        Get cached results for a query.
        
        Args:
            query_text: Search query text
            max_results: Maximum results requested
            similarity_threshold: Similarity threshold used
            
        Returns:
            Tuple of (results, stats) if cached, None otherwise
        """
        cache_key = self._generate_cache_key(query_text, max_results, similarity_threshold)
        
        # Update total queries count
        st.session_state.cache_stats['total_queries'] += 1
        
        # Check if key exists in cache
        if cache_key not in st.session_state.query_cache:
            st.session_state.cache_stats['misses'] += 1
            return None
        
        cached_entry = st.session_state.query_cache[cache_key]
        
        # Check if cache entry is still valid (not expired)
        if datetime.now() - cached_entry['timestamp'] > self.ttl:
            # Remove expired entry
            del st.session_state.query_cache[cache_key]
            st.session_state.cache_stats['misses'] += 1
            self.logger.debug(f"Cache entry expired for query: {query_text[:30]}...")
            return None
        
        # Cache hit
        st.session_state.cache_stats['hits'] += 1
        self.logger.debug(f"Cache hit for query: {query_text[:30]}...")
        
        return cached_entry['results'], cached_entry['stats']
    
    def put(self, query_text: str, results: List[SearchResult], stats: dict, 
            max_results: int = 5, similarity_threshold: float = 0.1):
        """
        Store results in cache.
        
        Args:
            query_text: Search query text
            results: Search results to cache
            stats: Search statistics to cache
            max_results: Maximum results requested
            similarity_threshold: Similarity threshold used
        """
        cache_key = self._generate_cache_key(query_text, max_results, similarity_threshold)
        
        # Check cache size and evict oldest entries if needed
        self._evict_if_needed()
        
        # Store in cache
        st.session_state.query_cache[cache_key] = {
            'results': results,
            'stats': stats,
            'timestamp': datetime.now(),
            'query_text': query_text
        }
        
        self.logger.debug(f"Cached results for query: {query_text[:30]}...")
    
    def _evict_if_needed(self):
        """Evict oldest cache entries if cache is full."""
        if len(st.session_state.query_cache) >= self.max_size:
            # Find oldest entry
            oldest_key = None
            oldest_time = datetime.now()
            
            for key, entry in st.session_state.query_cache.items():
                if entry['timestamp'] < oldest_time:
                    oldest_time = entry['timestamp']
                    oldest_key = key
            
            # Remove oldest entry
            if oldest_key:
                del st.session_state.query_cache[oldest_key]
                self.logger.debug("Evicted oldest cache entry")
    
    def clear(self):
        """Clear all cached entries."""
        st.session_state.query_cache.clear()
        st.session_state.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }
        self.logger.info("Query cache cleared")
    
    def get_stats(self) -> dict:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = st.session_state.cache_stats.copy()
        
        # Calculate hit rate
        total_requests = stats['hits'] + stats['misses']
        stats['hit_rate'] = stats['hits'] / total_requests if total_requests > 0 else 0.0
        
        # Add cache size info
        stats['cache_size'] = len(st.session_state.query_cache)
        stats['max_size'] = self.max_size
        
        return stats


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_image_thumbnails(image_paths: List[str]) -> Dict[str, Any]:
    """
    Load and cache image thumbnails for faster display.
    
    Args:
        image_paths: List of image file paths
        
    Returns:
        Dictionary mapping paths to thumbnail data
    """
    thumbnails = {}
    
    for path in image_paths:
        try:
            # For now, just store the path - actual thumbnail generation
            # would require PIL/Pillow image processing
            thumbnails[path] = {
                'path': path,
                'loaded': True,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to load thumbnail for {path}: {e}")
            thumbnails[path] = {
                'path': path,
                'loaded': False,
                'error': str(e)
            }
    
    return thumbnails


@st.cache_resource
def get_cached_search_engine():
    """
    Cache the search engine instance to avoid reloading models.
    
    Returns:
        Cached SearchEngine instance
    """
    from config import AppConfig
    from ..processors.search_engine import SearchEngine
    
    config = AppConfig()
    config.validate()
    
    return SearchEngine(config)


def optimize_session_state():
    """
    Optimize session state by cleaning up old or unnecessary data.
    """
    # Clean up old search results (keep only last 5 searches)
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    # Limit search history size
    max_history = 5
    if len(st.session_state.search_history) > max_history:
        st.session_state.search_history = st.session_state.search_history[-max_history:]
    
    # Clean up temporary UI state
    temp_keys = [key for key in st.session_state.keys() if key.startswith('temp_')]
    for key in temp_keys:
        del st.session_state[key]


def render_performance_metrics():
    """Render enhanced performance metrics in the sidebar."""
    try:
        if 'cache_stats' in st.session_state:
            cache = QueryCache()
            stats = cache.get_stats()
            
            st.sidebar.markdown("### ⚡ Performance")
            
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                st.metric("Cache Hits", stats['hits'])
                st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")
            
            with col2:
                st.metric("Cache Size", f"{stats['cache_size']}/{stats['max_size']}")
                st.metric("Total Queries", stats['total_queries'])
            
            # Additional performance info
            if 'search_engine' in st.session_state:
                try:
                    engine_stats = st.session_state.search_engine.get_search_statistics()
                    
                    st.sidebar.markdown("**Search Performance:**")
                    avg_time = engine_stats['searches']['average_search_time']
                    st.sidebar.write(f"Avg Search Time: {avg_time:.2f}s")
                    
                    if avg_time > 2.0:
                        st.sidebar.warning("⚠️ Slow search performance detected")
                    elif avg_time < 0.5:
                        st.sidebar.success("🚀 Excellent performance")
                    
                except Exception as e:
                    st.sidebar.error(f"Performance data unavailable: {e}")
            
            # Memory usage (if available)
            try:
                import psutil
                memory = psutil.virtual_memory()
                st.sidebar.markdown("**System Resources:**")
                st.sidebar.write(f"Memory Usage: {memory.percent:.1f}%")
                
                if memory.percent > 85:
                    st.sidebar.warning("⚠️ High memory usage")
                
            except ImportError:
                pass  # psutil not available
            except Exception as e:
                st.sidebar.error(f"System info unavailable: {e}")
        
        else:
            st.sidebar.markdown("### ⚡ Performance")
            st.sidebar.info("Performance metrics will appear after first search")
            
    except Exception as e:
        st.sidebar.error(f"Error displaying performance metrics: {e}")


def preload_common_queries():
    """
    Preload results for common queries to improve initial response times.
    """
    common_queries = [
        "red brick buildings",
        "glass facades", 
        "modern architecture",
        "stone buildings",
        "flat roofs"
    ]
    
    # This would be implemented to pre-populate cache with common searches
    # For now, just log the intent
    logging.getLogger(__name__).info(f"Would preload {len(common_queries)} common queries")


class LazyImageLoader:
    """
    Lazy loading implementation for images to improve page load times.
    """
    
    def __init__(self):
        """Initialize lazy loader."""
        self.loaded_images = set()
    
    def should_load_image(self, image_path: str, viewport_position: int = 0) -> bool:
        """
        Determine if an image should be loaded based on viewport position.
        
        Args:
            image_path: Path to the image
            viewport_position: Current viewport position (for future implementation)
            
        Returns:
            True if image should be loaded
        """
        # For now, implement simple loading strategy
        # In a full implementation, this would consider viewport position
        return image_path not in self.loaded_images
    
    def mark_loaded(self, image_path: str):
        """Mark an image as loaded."""
        self.loaded_images.add(image_path)
    
    def get_placeholder_image(self) -> str:
        """
        Get placeholder image for lazy loading.
        
        Returns:
            Path or data URL for placeholder image
        """
        # Return a simple placeholder - in production this could be a base64 encoded image
        return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+"


def initialize_performance_optimizations():
    """
    Initialize all performance optimizations for the web interface.
    """
    # Clean up session state
    optimize_session_state()
    
    # Initialize cache
    cache = QueryCache()
    
    # Initialize lazy loader
    if 'lazy_loader' not in st.session_state:
        st.session_state.lazy_loader = LazyImageLoader()
    
    # Log initialization
    logging.getLogger(__name__).info("Performance optimizations initialized")
    
    return cache