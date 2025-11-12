"""
Reusable UI components for the Streamlit web interface.
"""
import streamlit as st
from typing import List, Optional
from pathlib import Path

from src.models.search_models import SearchResult
from .styles import get_confidence_class, format_confidence_score


def render_loading_spinner(message: str = "Processing..."):
    """
    Render a loading spinner with message.
    
    Args:
        message: Loading message to display
    """
    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-spinner"></div>
        <p style="color: #666; font-size: 1.1rem;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_example_query_buttons(example_queries: List[str]) -> Optional[str]:
    """
    Render clickable example query buttons.
    
    Args:
        example_queries: List of example query strings
        
    Returns:
        Selected query string if any button was clicked
    """
    st.markdown("**Try these examples:**")
    
    # Create columns for example queries
    cols = st.columns(min(len(example_queries), 3))
    
    selected_query = None
    
    for i, query in enumerate(example_queries):
        col_idx = i % len(cols)
        with cols[col_idx]:
            if st.button(query, key=f"example_{i}", use_container_width=True):
                selected_query = query
    
    return selected_query


def render_search_stats(stats: dict):
    """
    Render search statistics in a compact format.
    
    Args:
        stats: Dictionary containing search statistics
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Images Found", 
            stats.get('results_count', 0),
            help="Number of matching images"
        )
    
    with col2:
        st.metric(
            "Search Time", 
            f"{stats.get('search_time', 0):.2f}s",
            help="Time taken to process query"
        )
    
    with col3:
        st.metric(
            "Avg Relevance", 
            f"{stats.get('avg_confidence', 0):.1%}",
            help="Average relevance score across all results"
        )


def render_result_card(result: SearchResult, index: int):
    """
    Render a single search result card.
    
    Args:
        result: SearchResult object to display
        index: Index of the result for unique keys
    """
    # Check if image file exists
    image_path = Path(result.image_path)
    
    if not image_path.exists():
        st.error(f"Image not found: {result.image_path}")
        return
    
    # Create result card container
    with st.container():
        # Display image
        try:
            st.image(
                str(image_path), 
                caption=f"Relevance: {format_confidence_score(result.confidence_score)}",
                use_column_width=True
            )
        except Exception as e:
            st.error(f"Error loading image: {e}")
            return
        
        # Relevance score badge with color-coded indicator
        confidence_class = get_confidence_class(result.confidence_score)
        st.markdown(f"""
        <div class="{confidence_class}">
            Match Strength: {format_confidence_score(result.confidence_score)}
        </div>
        """, unsafe_allow_html=True)
        
        # Description
        st.markdown(f"**Description:** {result.description}")
        
        # Features tags
        if result.features:
            st.markdown("**Features:**")
            feature_tags = " ".join([
                f'<span class="feature-tag">{feature}</span>' 
                for feature in result.features[:5]  # Limit to 5 features
            ])
            st.markdown(feature_tags, unsafe_allow_html=True)
        
        # Additional details in expander
        with st.expander("Details", expanded=False):
            st.write(f"**File:** {image_path.name}")
            st.write(f"**Similarity Score:** {result.similarity_score:.3f}")
            if len(result.features) > 5:
                st.write(f"**All Features:** {', '.join(result.features)}")


def render_results_grid(results: List[SearchResult], columns: int = 3):
    """
    Render search results in a responsive grid layout.
    
    Args:
        results: List of SearchResult objects to display
        columns: Number of columns in the grid
    """
    if not results:
        st.info("No results found. Try adjusting your search terms.")
        return
    
    # Calculate number of rows needed
    rows = (len(results) + columns - 1) // columns
    
    for row in range(rows):
        cols = st.columns(columns)
        
        for col_idx in range(columns):
            result_idx = row * columns + col_idx
            
            if result_idx < len(results):
                with cols[col_idx]:
                    render_result_card(results[result_idx], result_idx)


def render_no_results_message(query: str):
    """
    Render a helpful message when no results are found.
    
    Args:
        query: The search query that returned no results
    """
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
        <h3 style="color: #666; margin-bottom: 1rem;">🔍 No Results Found</h3>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
            We couldn't find any images matching "<strong>{}</strong>"
        </p>
        <div style="text-align: left; max-width: 500px; margin: 0 auto;">
            <h4 style="color: #333; margin-bottom: 1rem;">💡 Try these suggestions:</h4>
            <ul style="color: #666; line-height: 1.6;">
                <li>Use more general terms (e.g., "brick" instead of "red brick")</li>
                <li>Try different architectural features (roof, windows, materials)</li>
                <li>Check spelling and try synonyms</li>
                <li>Combine multiple features (e.g., "glass steel modern")</li>
            </ul>
        </div>
    </div>
    """.format(query), unsafe_allow_html=True)


def render_error_message(error: str, title: str = "Error"):
    """
    Render a styled error message.
    
    Args:
        error: Error message to display
        title: Error title
    """
    st.markdown(f"""
    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
                padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        <h4 style="margin-bottom: 0.5rem;">⚠️ {title}</h4>
        <p style="margin: 0;">{error}</p>
    </div>
    """, unsafe_allow_html=True)


def render_success_message(message: str, title: str = "Success"):
    """
    Render a styled success message.
    
    Args:
        message: Success message to display
        title: Success title
    """
    st.markdown(f"""
    <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; 
                padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        <h4 style="margin-bottom: 0.5rem;">✅ {title}</h4>
        <p style="margin: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_info_message(message: str, title: str = "Info"):
    """
    Render a styled info message.
    
    Args:
        message: Info message to display
        title: Info title
    """
    st.markdown(f"""
    <div style="background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; 
                padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        <h4 style="margin-bottom: 0.5rem;">ℹ️ {title}</h4>
        <p style="margin: 0;">{message}</p>
    </div>
    """, unsafe_allow_html=True)