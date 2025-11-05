"""
Results display functionality for the Streamlit web interface.
"""
import streamlit as st
from typing import List, Optional
from pathlib import Path
import os

from ..models.search_models import SearchResult
from .components import (
    render_no_results_message,
    render_error_message,
    render_info_message
)
from .styles import get_confidence_class, format_confidence_score


def check_image_exists(image_path: str) -> bool:
    """
    Check if image file exists and is accessible.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if image exists and is readable
    """
    try:
        path = Path(image_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def render_result_card(result: SearchResult, index: int, column_width: str = "100%"):
    """
    Render a single search result card with enhanced error handling and graceful degradation.
    
    Args:
        result: SearchResult object to display
        index: Index of the result for unique keys
        column_width: CSS width for the card
    """
    # Create card container with custom styling
    st.markdown(f"""
    <div class="result-card" style="width: {column_width}; margin-bottom: 1.5rem;">
    """, unsafe_allow_html=True)
    
    try:
        # Check if image exists and handle gracefully
        image_exists = check_image_exists(result.image_path)
        
        if image_exists:
            try:
                # Display image with caption
                st.image(
                    result.image_path,
                    caption=f"Match: {format_confidence_score(result.confidence_score)}",
                    use_column_width=True
                )
            except Exception as e:
                # Fallback: show placeholder with error info
                render_image_placeholder(result.image_path, str(e))
        else:
            # Show placeholder for missing image
            render_image_placeholder(result.image_path, "Image file not found")
        
        # Confidence score badge (always show)
        confidence_class = get_confidence_class(result.confidence_score)
        st.markdown(f"""
        <div class="{confidence_class}" style="margin: 0.5rem 0;">
            {format_confidence_score(result.confidence_score)} Confidence
        </div>
        """, unsafe_allow_html=True)
        
        # Description (with fallback)
        description = result.description if result.description else "No description available"
        st.markdown(f"**Description:**")
        st.markdown(f"*{description}*")
        
        # Features as tags (with error handling)
        if hasattr(result, 'features') and result.features and len(result.features) > 0:
            st.markdown("**Features:**")
            
            try:
                # Limit features displayed and create tags
                display_features = result.features[:6]  # Show max 6 features
                
                feature_html = ""
                for feature in display_features:
                    # Sanitize feature text
                    clean_feature = str(feature).replace('<', '&lt;').replace('>', '&gt;')
                    feature_html += f'<span class="feature-tag">{clean_feature}</span> '
                
                st.markdown(feature_html, unsafe_allow_html=True)
                
                # Show remaining features count if there are more
                if len(result.features) > 6:
                    st.markdown(f"*+{len(result.features) - 6} more features*")
                    
            except Exception as e:
                st.markdown(f"*Features unavailable: {e}*")
        
        # Additional details in expander (with error handling)
        with st.expander("🔍 View Details", expanded=False):
            try:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Validate similarity score
                    sim_score = getattr(result, 'similarity_score', 0.0)
                    if isinstance(sim_score, (int, float)) and -1 <= sim_score <= 1:
                        st.metric("Similarity Score", f"{sim_score:.3f}")
                    else:
                        st.metric("Similarity Score", "N/A")
                    
                    # File name (with error handling)
                    try:
                        file_name = Path(result.image_path).name
                        st.write(f"**File:** `{file_name}`")
                    except Exception:
                        st.write(f"**File:** `{result.image_path}`")
                
                with col2:
                    st.metric("Confidence", format_confidence_score(result.confidence_score))
                    st.write(f"**Path:** `{result.image_path}`")
                    
                    # Image status
                    if image_exists:
                        st.success("✅ Image accessible")
                    else:
                        st.error("❌ Image missing")
                
                # All features (if available)
                if hasattr(result, 'features') and result.features and len(result.features) > 6:
                    st.markdown("**All Features:**")
                    try:
                        st.write(", ".join(str(f) for f in result.features))
                    except Exception as e:
                        st.write(f"Error displaying features: {e}")
                        
            except Exception as e:
                st.error(f"Error in details section: {e}")
    
    except Exception as e:
        # Fallback error display
        st.error(f"Error rendering result card: {e}")
        st.write(f"**Image Path:** {getattr(result, 'image_path', 'Unknown')}")
        st.write(f"**Confidence:** {getattr(result, 'confidence_score', 'Unknown')}")
    
    # Close card container
    st.markdown("</div>", unsafe_allow_html=True)


def render_image_placeholder(image_path: str, error_message: str):
    """
    Render a placeholder for missing or broken images.
    
    Args:
        image_path: Path to the missing image
        error_message: Error message to display
    """
    st.markdown(f"""
    <div style="
        background: #f8f9fa; 
        border: 2px dashed #dee2e6; 
        border-radius: 8px; 
        padding: 2rem; 
        text-align: center; 
        margin: 1rem 0;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    ">
        <div style="font-size: 3rem; color: #6c757d; margin-bottom: 1rem;">🖼️</div>
        <h4 style="color: #6c757d; margin-bottom: 0.5rem;">Image Unavailable</h4>
        <p style="color: #6c757d; margin-bottom: 0.5rem; font-size: 0.9rem;">{error_message}</p>
        <p style="color: #adb5bd; font-size: 0.8rem; font-family: monospace;">{Path(image_path).name}</p>
    </div>
    """, unsafe_allow_html=True)


def render_results_grid(results: List[SearchResult], columns: int = 3):
    """
    Render search results in a responsive grid layout.
    
    Args:
        results: List of SearchResult objects to display
        columns: Number of columns in the grid (1-4)
    """
    if not results:
        return
    
    # Ensure columns is within reasonable range
    columns = max(1, min(columns, 4))
    
    # Calculate number of rows needed
    num_results = len(results)
    rows = (num_results + columns - 1) // columns
    
    for row in range(rows):
        # Create columns for this row
        cols = st.columns(columns)
        
        for col_idx in range(columns):
            result_idx = row * columns + col_idx
            
            # Check if we have a result for this position
            if result_idx < num_results:
                with cols[col_idx]:
                    render_result_card(results[result_idx], result_idx)


def render_results_list(results: List[SearchResult]):
    """
    Render search results in a single-column list layout.
    
    Args:
        results: List of SearchResult objects to display
    """
    if not results:
        return
    
    for i, result in enumerate(results):
        render_result_card(result, i, "100%")
        
        # Add separator between results (except for last one)
        if i < len(results) - 1:
            st.markdown("---")


def render_results_header(results: List[SearchResult], query: str, stats: dict):
    """
    Render header information for search results.
    
    Args:
        results: List of search results
        query: Search query text
        stats: Search statistics dictionary
    """
    num_results = len(results)
    search_time = stats.get('search_time', 0)
    
    # Results summary
    st.markdown(f"""
    ### 📋 Search Results
    
    Found **{num_results}** images matching "*{query}*" in **{search_time:.2f} seconds**
    """)
    
    if num_results > 0:
        avg_confidence = stats.get('avg_confidence', 0)
        st.markdown(f"Average confidence: **{format_confidence_score(avg_confidence)}**")


def render_results_controls(results: List[SearchResult]) -> dict:
    """
    Render controls for customizing results display.
    
    Args:
        results: List of search results
        
    Returns:
        Dictionary of control settings
    """
    if not results:
        return {}
    
    st.markdown("#### Display Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Layout selection
        layout = st.selectbox(
            "Layout",
            options=["Grid", "List"],
            index=0,
            help="Choose how to display results"
        )
    
    with col2:
        # Grid columns (only show if grid layout selected)
        if layout == "Grid":
            columns = st.selectbox(
                "Columns",
                options=[1, 2, 3, 4],
                index=2,  # Default to 3 columns
                help="Number of columns in grid"
            )
        else:
            columns = 1
    
    with col3:
        # Results limit
        max_display = st.selectbox(
            "Show Results",
            options=[5, 10, 15, 20, "All"],
            index=0,
            help="Maximum number of results to display"
        )
    
    return {
        'layout': layout,
        'columns': columns,
        'max_display': max_display
    }


def render_search_results(results: List[SearchResult], query: str, stats: dict):
    """
    Render complete search results section with controls and display.
    
    Args:
        results: List of SearchResult objects to display
        query: Search query text
        stats: Search statistics dictionary
    """
    if not results:
        render_no_results_message(query)
        return
    
    # Render results header
    render_results_header(results, query, stats)
    
    # Render display controls
    controls = render_results_controls(results)
    
    # Apply display limits
    max_display = controls.get('max_display', 5)
    if max_display != "All":
        display_results = results[:max_display]
        
        if len(results) > max_display:
            st.info(f"Showing top {max_display} of {len(results)} results")
    else:
        display_results = results
    
    # Add spacing
    st.markdown("---")
    
    # Render results based on layout choice
    layout = controls.get('layout', 'Grid')
    columns = controls.get('columns', 3)
    
    if layout == "Grid":
        render_results_grid(display_results, columns)
    else:
        render_results_list(display_results)
    
    # Show additional info if results were limited
    if len(results) > len(display_results):
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-top: 2rem;">
            <p style="margin: 0; color: #666;">
                Showing {len(display_results)} of {len(results)} total results. 
                Adjust "Show Results" to see more.
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_empty_state():
    """Render empty state when no search has been performed."""
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; background: #f8f9fa; border-radius: 10px; margin: 2rem 0;">
        <h3 style="color: #666; margin-bottom: 1rem;">🔍 Ready to Search</h3>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
            Enter a search query above to find architectural images that match your description.
        </p>
        <div style="text-align: left; max-width: 400px; margin: 0 auto;">
            <h4 style="color: #333; margin-bottom: 1rem;">✨ What you can search for:</h4>
            <ul style="color: #666; line-height: 1.8;">
                <li><strong>Materials:</strong> brick, glass, steel, stone, concrete</li>
                <li><strong>Features:</strong> windows, roofs, columns, facades</li>
                <li><strong>Styles:</strong> modern, traditional, industrial</li>
                <li><strong>Colors:</strong> red brick, white walls, dark facades</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)


def handle_results_display():
    """
    Handle the display of search results from session state.
    """
    # Check if we have results in session state
    if 'search_results' in st.session_state and 'last_query' in st.session_state:
        results = st.session_state.search_results
        query = st.session_state.last_query
        stats = st.session_state.get('search_stats', {})
        
        render_search_results(results, query, stats)
    else:
        render_empty_state()