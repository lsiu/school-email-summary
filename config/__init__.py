"""Configuration package for Gmail automation."""

from .settings import (
    # Constants
    SCOPES,
    CACHE_DIR,
    
    # Configuration loading
    load_config,
    get_config,
    is_config_loaded,
    
    # Configuration getters
    get_sender_domains,
    get_cache_expiry_hours,
    
    # Configuration values (loaded from YAML)
    CHILDREN,
    SENDER_DOMAINS,
    CACHE_EXPIRY_HOURS,
    GRADE_DIVISIONS,
    
    # Grade calculation functions
    get_school_year,
    calculate_grade,
    get_division,
    get_division_range,
    get_children_info,
    
    # Prompt
    get_summarize_prompt,
)

__all__ = [
    # Constants
    "SCOPES",
    "CACHE_DIR",
    
    # Configuration loading
    "load_config",
    "get_config",
    "is_config_loaded",
    
    # Configuration getters
    "get_sender_domains",
    "get_cache_expiry_hours",
    
    # Configuration values
    "CHILDREN",
    "SENDER_DOMAINS",
    "CACHE_EXPIRY_HOURS",
    "GRADE_DIVISIONS",
    
    # Functions
    "get_school_year",
    "calculate_grade",
    "get_division",
    "get_division_range",
    "get_children_info",
    "get_summarize_prompt",
]
