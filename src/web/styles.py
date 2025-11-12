"""
CSS styles for the Streamlit web interface.
"""
import streamlit as st


def load_custom_css():
    """Load custom CSS styles for the application."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    /* Search input styling */
    .search-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    
    /* Results grid styling */
    .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
    }
    
    /* Result card styling */
    .result-card {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid #e9ecef;
    }
    
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    .result-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-bottom: 1px solid #e9ecef;
    }
    
    .result-content {
        padding: 1rem;
    }
    
    /* Relevance score badges with color-coded indicators */
    .relevance-score {
        display: inline-block;
        padding: 0.4rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        border: 2px solid;
    }
    
    .relevance-score.strong {
        background: #d4edda;
        color: #155724;
        border-color: #28a745;
    }
    
    .relevance-score.good {
        background: #fff3cd;
        color: #856404;
        border-color: #ffc107;
    }
    
    .relevance-score.weak {
        background: #e2e3e5;
        color: #383d41;
        border-color: #6c757d;
    }
    
    /* Info icon tooltip styling */
    .info-tooltip {
        display: inline-block;
        margin-left: 0.5rem;
        cursor: help;
        color: #007bff;
        font-size: 1rem;
        vertical-align: middle;
    }
    
    .info-tooltip:hover {
        color: #0056b3;
    }
    
    /* Score explanation section */
    .score-explanation {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .score-explanation h4 {
        color: #007bff;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    
    .result-description {
        font-size: 0.9rem;
        color: #666;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    
    .result-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
        margin-top: 0.5rem;
    }
    
    .feature-tag {
        background: #e9ecef;
        color: #495057;
        padding: 0.2rem 0.4rem;
        border-radius: 10px;
        font-size: 0.7rem;
    }
    
    /* Example queries styling */
    .example-queries {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .example-query {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }
    
    .example-query:hover {
        background: #007bff;
        color: white;
        border-color: #007bff;
    }
    
    /* Loading spinner styling */
    .loading-container {
        text-align: center;
        padding: 3rem;
    }
    
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #007bff;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .results-grid {
            grid-template-columns: 1fr;
        }
        
        .search-container {
            padding: 1rem;
        }
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    /* Metrics styling */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    /* Error and success messages */
    .stAlert > div {
        border-radius: 8px;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e9ecef;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    </style>
    """, unsafe_allow_html=True)


def get_confidence_class(confidence_score: float) -> str:
    """
    Get CSS class for relevance score styling based on CLIP similarity ranges.
    
    Args:
        confidence_score: Similarity score between 0 and 1
        
    Returns:
        CSS class name for styling
    """
    if confidence_score >= 0.35:  # Strong match
        return "relevance-score strong"
    elif confidence_score >= 0.25:  # Good match
        return "relevance-score good"
    else:  # Weak match
        return "relevance-score weak"


def format_confidence_score(confidence_score: float) -> str:
    """
    Format relevance score for display with contextual label.
    
    Args:
        confidence_score: Similarity score between 0 and 1
        
    Returns:
        Formatted relevance score string with match quality indicator
    """
    percentage = confidence_score * 100
    
    # Add match quality label based on score
    if confidence_score >= 0.35:
        quality = "Strong Match"
    elif confidence_score >= 0.25:
        quality = "Good Match"
    else:
        quality = "Weak Match"
    
    return f"{percentage:.1f}% ({quality})"


def get_match_quality_label(confidence_score: float) -> str:
    """
    Get match quality label for a given score.
    
    Args:
        confidence_score: Similarity score between 0 and 1
        
    Returns:
        Match quality label string
    """
    if confidence_score >= 0.35:
        return "Strong Match"
    elif confidence_score >= 0.25:
        return "Good Match"
    else:
        return "Weak Match"