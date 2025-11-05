"""
Comprehensive error handling and recovery system for the web interface.
"""
import streamlit as st
import logging
import traceback
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import time
from datetime import datetime

from .components import render_error_message, render_info_message, render_success_message


class ErrorHandler:
    """
    Centralized error handling and recovery system.
    """
    
    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.last_error_time = None
        self.recovery_attempts = {}
    
    def handle_search_error(self, error: Exception, query: str) -> bool:
        """
        Handle search-related errors with specific recovery strategies.
        
        Args:
            error: The exception that occurred
            query: The search query that caused the error
            
        Returns:
            True if error was handled and recovery attempted, False otherwise
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        self.logger.error(f"Search error for query '{query}': {error_type}: {error_msg}")
        
        # Categorize and handle specific error types
        if "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
            return self._handle_memory_error(error, query)
        
        elif "file" in error_msg.lower() or "not found" in error_msg.lower():
            return self._handle_file_error(error, query)
        
        elif "model" in error_msg.lower() or "clip" in error_msg.lower():
            return self._handle_model_error(error, query)
        
        elif "embedding" in error_msg.lower() or "similarity" in error_msg.lower():
            return self._handle_embedding_error(error, query)
        
        else:
            return self._handle_generic_error(error, query)
    
    def _handle_memory_error(self, error: Exception, query: str) -> bool:
        """Handle memory-related errors."""
        render_error_message(
            "Memory Error: The system is running low on memory. "
            "Try closing other applications or simplifying your search query.",
            "Memory Issue"
        )
        
        # Suggest recovery actions
        st.markdown("""
        **Recovery Actions:**
        1. 🔄 Refresh the page to clear memory
        2. 💻 Close other browser tabs or applications
        3. 🔍 Try a shorter, simpler search query
        4. ⏳ Wait a moment and try again
        """)
        
        if st.button("🔄 Clear Cache and Retry"):
            self._clear_caches()
            st.experimental_rerun()
        
        return True
    
    def _handle_file_error(self, error: Exception, query: str) -> bool:
        """Handle file system related errors."""
        render_error_message(
            "File System Error: Some image files or metadata may be missing or inaccessible.",
            "File Access Issue"
        )
        
        # Check for common file issues
        missing_files = self._check_file_integrity()
        
        if missing_files:
            st.markdown("**Missing Files Detected:**")
            for file_path in missing_files[:5]:  # Show first 5
                st.write(f"• {file_path}")
            
            if len(missing_files) > 5:
                st.write(f"• ... and {len(missing_files) - 5} more files")
        
        st.markdown("""
        **Recovery Actions:**
        1. 🔍 Check that all image files are in the correct directory
        2. 🔄 Run the offline processing script to regenerate metadata
        3. 📁 Verify file permissions and accessibility
        """)
        
        return True
    
    def _handle_model_error(self, error: Exception, query: str) -> bool:
        """Handle AI model related errors."""
        render_error_message(
            "AI Model Error: There was an issue with the CLIP model. "
            "This may be due to model loading or inference problems.",
            "Model Issue"
        )
        
        st.markdown("""
        **Recovery Actions:**
        1. 🔄 Restart the application to reload the model
        2. 🖥️ Check if you have sufficient system resources (RAM/GPU)
        3. 🌐 Verify internet connection (model may need to download)
        4. 📦 Ensure all dependencies are properly installed
        """)
        
        if st.button("🔄 Reload Model"):
            self._reload_model()
        
        return True
    
    def _handle_embedding_error(self, error: Exception, query: str) -> bool:
        """Handle embedding calculation errors."""
        render_error_message(
            "Embedding Error: There was an issue calculating similarities. "
            "This may be due to corrupted embeddings or calculation problems.",
            "Calculation Issue"
        )
        
        st.markdown("""
        **Recovery Actions:**
        1. 🔄 Try a different search query
        2. 📊 Check if embeddings need to be regenerated
        3. 🔍 Verify metadata integrity
        """)
        
        if st.button("🔄 Regenerate Embeddings"):
            st.info("This would trigger embedding regeneration (not implemented in demo)")
        
        return True
    
    def _handle_generic_error(self, error: Exception, query: str) -> bool:
        """Handle generic errors."""
        render_error_message(
            f"Unexpected Error: {str(error)}\n\n"
            "An unexpected error occurred. Please try again or contact support if the issue persists.",
            "System Error"
        )
        
        # Show error details in expander
        with st.expander("🔍 Error Details", expanded=False):
            st.code(f"Error Type: {type(error).__name__}")
            st.code(f"Error Message: {str(error)}")
            st.code(f"Query: {query}")
            st.code(f"Timestamp: {datetime.now().isoformat()}")
        
        st.markdown("""
        **Recovery Actions:**
        1. 🔄 Refresh the page and try again
        2. 🔍 Try a different search query
        3. ⏳ Wait a moment and retry
        4. 📞 Contact support if the issue persists
        """)
        
        return True
    
    def _check_file_integrity(self) -> list:
        """
        Check for missing or corrupted files.
        
        Returns:
            List of missing file paths
        """
        missing_files = []
        
        try:
            # Check if we have search results with file paths
            if 'search_results' in st.session_state:
                results = st.session_state.search_results
                
                for result in results:
                    if hasattr(result, 'image_path'):
                        if not Path(result.image_path).exists():
                            missing_files.append(result.image_path)
        
        except Exception as e:
            self.logger.warning(f"File integrity check failed: {e}")
        
        return missing_files
    
    def _clear_caches(self):
        """Clear all caches to free memory."""
        try:
            # Clear query cache
            if 'query_cache' in st.session_state:
                st.session_state.query_cache.clear()
            
            # Clear search engine cache
            if 'search_engine' in st.session_state:
                st.session_state.search_engine.clear_caches()
            
            # Clear other session state
            keys_to_clear = ['search_results', 'search_stats', 'last_query']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            render_success_message("Caches cleared successfully", "Memory Freed")
            
        except Exception as e:
            self.logger.error(f"Failed to clear caches: {e}")
            render_error_message(f"Failed to clear caches: {e}", "Cache Clear Failed")
    
    def _reload_model(self):
        """Attempt to reload the AI model."""
        try:
            # Clear existing model from session state
            if 'search_engine' in st.session_state:
                del st.session_state.search_engine
            
            render_info_message("Model reload initiated. Please refresh the page.", "Model Reload")
            
        except Exception as e:
            self.logger.error(f"Failed to reload model: {e}")
            render_error_message(f"Failed to reload model: {e}", "Model Reload Failed")
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """
        Log error with context information.
        
        Args:
            error: The exception that occurred
            context: Additional context information
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        # Log error with full traceback
        self.logger.error(
            f"Error #{self.error_count}: {type(error).__name__}: {str(error)}\n"
            f"Context: {context}\n"
            f"Traceback: {traceback.format_exc()}"
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': self.error_count,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'recovery_attempts': len(self.recovery_attempts)
        }


def with_error_handling(func: Callable) -> Callable:
    """
    Decorator to wrap functions with error handling.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            
            # Extract context information
            context = {
                'function': func.__name__,
                'args': str(args)[:200],  # Limit length
                'kwargs': str(kwargs)[:200],
                'timestamp': datetime.now().isoformat()
            }
            
            error_handler.log_error(e, context)
            
            # Handle specific error types
            if 'query' in kwargs:
                error_handler.handle_search_error(e, kwargs['query'])
            else:
                error_handler._handle_generic_error(e, "Unknown")
            
            return None
    
    return wrapper


def check_system_health() -> Dict[str, Any]:
    """
    Perform system health checks.
    
    Returns:
        Dictionary with health check results
    """
    health = {
        'status': 'healthy',
        'issues': [],
        'warnings': []
    }
    
    try:
        # Check memory usage
        import psutil
        memory = psutil.virtual_memory()
        
        if memory.percent > 90:
            health['issues'].append(f"Critical memory usage: {memory.percent:.1f}%")
            health['status'] = 'critical'
        elif memory.percent > 75:
            health['warnings'].append(f"High memory usage: {memory.percent:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
        # Check disk space
        disk = psutil.disk_usage('.')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 95:
            health['issues'].append(f"Critical disk usage: {disk_percent:.1f}%")
            health['status'] = 'critical'
        elif disk_percent > 85:
            health['warnings'].append(f"High disk usage: {disk_percent:.1f}%")
            if health['status'] == 'healthy':
                health['status'] = 'warning'
        
    except ImportError:
        health['warnings'].append("System monitoring unavailable (psutil not installed)")
    except Exception as e:
        health['warnings'].append(f"Health check error: {e}")
    
    return health


def render_system_health():
    """Render system health status in the sidebar."""
    try:
        health = check_system_health()
        
        st.sidebar.markdown("### 🏥 System Health")
        
        if health['status'] == 'healthy':
            st.sidebar.success("✅ System Healthy")
        elif health['status'] == 'warning':
            st.sidebar.warning("⚠️ System Warning")
        else:
            st.sidebar.error("❌ System Critical")
        
        # Show issues and warnings
        if health['issues']:
            st.sidebar.markdown("**Issues:**")
            for issue in health['issues']:
                st.sidebar.error(f"• {issue}")
        
        if health['warnings']:
            st.sidebar.markdown("**Warnings:**")
            for warning in health['warnings']:
                st.sidebar.warning(f"• {warning}")
        
    except Exception as e:
        st.sidebar.error(f"Health check failed: {e}")