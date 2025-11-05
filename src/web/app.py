"""
Main Streamlit web application for AI Architectural Search System.
"""
import streamlit as st
import logging
from pathlib import Path
import sys
import os
import time
import psutil
import torch

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import get_config
from src.processors.search_engine import SearchEngine
from src.web.styles import load_custom_css
from src.web.components import (
    render_example_query_buttons, 
    render_info_message,
    render_error_message,
    render_success_message
)
from src.web.search import render_search_interface
from src.web.results import handle_results_display
from src.web.cache import initialize_performance_optimizations, render_performance_metrics
from src.web.error_handler import ErrorHandler, render_system_health, with_error_handling


def setup_page_config():
    """Configure Streamlit page settings."""
    config = get_config()
    
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Load custom CSS styles
    load_custom_css()


def render_header():
    """Render the application header with title and description."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <h1 style="color: #2E86AB; margin-bottom: 0.5rem;">
            🏗️ AI Architectural Search
        </h1>
        <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
            Find architectural images using natural language descriptions
        </p>
    </div>
    """, unsafe_allow_html=True)


def get_example_queries():
    """Get list of example queries for the interface."""
    return [
        "red brick buildings",
        "glass and steel facades", 
        "stone columns",
        "flat roof structures",
        "large windows",
        "curved architecture",
        "modern office buildings",
        "traditional residential",
        "industrial architecture"
    ]


def render_example_queries():
    """Render example queries section."""
    st.markdown("### 💡 Example Queries")
    
    example_queries = get_example_queries()
    
    # Group queries by category for better organization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Materials:**")
        materials = ["red brick buildings", "glass and steel facades", "stone columns"]
        for query in materials:
            st.markdown(f"• {query}")
    
    with col2:
        st.markdown("**Features:**")
        features = ["flat roof structures", "large windows", "curved architecture"]
        for query in features:
            st.markdown(f"• {query}")
    
    with col3:
        st.markdown("**Styles:**")
        styles = ["modern office buildings", "traditional residential", "industrial architecture"]
        for query in styles:
            st.markdown(f"• {query}")


def render_usage_instructions():
    """Render usage instructions section."""
    with st.expander("📖 How to Use", expanded=False):
        st.markdown("""
        1. **Enter your query**: Type a natural language description of the architectural features you're looking for
        2. **Click Search**: The AI will analyze your query and find matching images
        3. **View results**: Browse the image grid with confidence scores and descriptions
        4. **Refine search**: Try different keywords or combinations for better results
        
        **Tips for better results:**
        - Be specific about materials (brick, glass, steel, stone)
        - Mention architectural features (roof type, windows, columns)
        - Include style descriptors (modern, traditional, industrial)
        """)


def initialize_search_engine():
    """Initialize and cache the search engine with enhanced error handling."""
    if 'search_engine' not in st.session_state:
        try:
            config = get_config()
            
            # Initialize performance optimizations
            cache = initialize_performance_optimizations()
            
            with st.spinner("Loading AI models and image database..."):
                # Check system requirements first
                system_check = perform_system_check()
                if not system_check['ready']:
                    error_msg = "System requirements not met:\n" + "\n".join([f"• {issue}" for issue in system_check['issues']])
                    render_error_message(error_msg, "System Check Failed")
                    st.stop()
                
                # Initialize search engine with retry logic
                search_engine = initialize_with_retry(config, max_retries=3)
                
                # Validate search readiness
                status = search_engine.validate_search_readiness()
                
                if not status['ready']:
                    error_msg = "Search system not ready:\n" + "\n".join([f"• {issue}" for issue in status['issues']])
                    render_error_message(error_msg, "System Initialization Failed")
                    
                    # Provide recovery suggestions
                    render_recovery_suggestions()
                    st.stop()
                
                st.session_state.search_engine = search_engine
                st.session_state.search_stats = status['statistics']
                st.session_state.query_cache = cache
                st.session_state.initialization_time = time.time()
                
        except Exception as e:
            handle_initialization_error(e)
            st.stop()
    
    return st.session_state.search_engine


def render_system_status():
    """Render system status information in sidebar."""
    if 'search_stats' in st.session_state:
        stats = st.session_state.search_stats
        
        st.sidebar.markdown("### 📊 System Status")
        st.sidebar.metric("Images Indexed", stats.get('total_images', 0))
        st.sidebar.metric("Cache Hit Rate", f"{stats.get('cache_hit_rate', 0):.1%}")
        
        if stats.get('total_searches', 0) > 0:
            st.sidebar.metric("Avg Search Time", f"{stats.get('avg_search_time', 0):.2f}s")


def perform_system_check():
    """Perform comprehensive system checks before initialization."""
    issues = []
    
    try:
        # Check available memory
        memory = psutil.virtual_memory()
        if memory.available < 2 * 1024 * 1024 * 1024:  # Less than 2GB
            issues.append(f"Low memory: {memory.available / (1024**3):.1f}GB available (2GB+ recommended)")
        
        # Check disk space
        disk = psutil.disk_usage('.')
        if disk.free < 1 * 1024 * 1024 * 1024:  # Less than 1GB
            issues.append(f"Low disk space: {disk.free / (1024**3):.1f}GB free (1GB+ recommended)")
        
        # Check if images directory exists
        config = get_config()
        if not Path(config.image_directory).exists():
            issues.append(f"Images directory not found: {config.image_directory}")
        
        # Check if metadata file exists
        if not Path(config.metadata_file).exists():
            issues.append(f"Metadata file not found: {config.metadata_file}")
        
        # Check PyTorch availability
        if not torch.cuda.is_available():
            logging.info("CUDA not available, using CPU (performance may be slower)")
        
    except Exception as e:
        issues.append(f"System check error: {e}")
    
    return {
        'ready': len(issues) == 0,
        'issues': issues
    }


def initialize_with_retry(config, max_retries=3):
    """Initialize search engine with retry logic."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                st.info(f"Retrying initialization (attempt {attempt + 1}/{max_retries})...")
                time.sleep(2)  # Brief delay between retries
            
            search_engine = SearchEngine(config)
            return search_engine
            
        except Exception as e:
            last_error = e
            logging.warning(f"Initialization attempt {attempt + 1} failed: {e}")
            
            # Clear any partial state
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    # All retries failed
    raise RuntimeError(f"Failed to initialize after {max_retries} attempts. Last error: {last_error}")


def handle_initialization_error(error):
    """Handle initialization errors with detailed diagnostics."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Categorize common errors
    if "CUDA" in error_msg or "GPU" in error_msg:
        render_error_message(
            f"GPU/CUDA Error: {error_msg}\n\n"
            "The system will attempt to use CPU instead. This may be slower but should work.",
            "GPU Initialization Failed"
        )
    elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
        render_error_message(
            f"Memory Error: {error_msg}\n\n"
            "Try closing other applications to free up memory, or restart the application.",
            "Insufficient Memory"
        )
    elif "file" in error_msg.lower() or "directory" in error_msg.lower():
        render_error_message(
            f"File System Error: {error_msg}\n\n"
            "Check that all required files and directories exist and are accessible.",
            "File System Error"
        )
    else:
        render_error_message(
            f"Initialization Error ({error_type}): {error_msg}\n\n"
            "Please check the logs for more details and try restarting the application.",
            "System Initialization Failed"
        )


def render_recovery_suggestions():
    """Render recovery suggestions for common issues."""
    st.markdown("""
    ### 🔧 Recovery Suggestions
    
    **If the system fails to initialize, try these steps:**
    
    1. **Refresh the page** - Sometimes a simple refresh resolves temporary issues
    2. **Check file paths** - Ensure images directory and metadata file exist
    3. **Free up memory** - Close other applications to free system resources
    4. **Restart application** - Stop and restart the Streamlit server
    5. **Check logs** - Look for detailed error messages in the console
    
    **For persistent issues:**
    - Verify all dependencies are installed correctly
    - Check that the images have been processed (run offline processing)
    - Ensure sufficient disk space and memory are available
    """)


def main():
    """Main application function with enhanced error handling."""
    try:
        # Setup page configuration
        setup_page_config()
        
        # Initialize search engine
        search_engine = initialize_search_engine()
        
        # Render header
        render_header()
        
        # Create main layout
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Search input section
            render_search_interface(search_engine)
            
            # Add spacing between search and results
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Results section
            handle_results_display()
        
        # Sidebar content
        with st.sidebar:
            render_system_status()
            
            st.markdown("---")
            
            # System health monitoring
            render_system_health()
            
            st.markdown("---")
            
            # Performance metrics
            render_performance_metrics()
            
            st.markdown("---")
            
            # Example queries
            render_example_queries()
            
            st.markdown("---")
            
            # Usage instructions
            render_usage_instructions()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666; padding: 1rem;'>"
            "AI-powered architectural image search using CLIP technology"
            "</div>", 
            unsafe_allow_html=True
        )
        
    except Exception as e:
        # Global error handler
        st.error("A critical error occurred in the application")
        st.exception(e)
        
        # Provide recovery options
        if st.button("🔄 Restart Application"):
            st.experimental_rerun()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the application
    main()