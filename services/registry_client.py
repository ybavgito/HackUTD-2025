import os
import requests
import logging
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

# --- Setup ---
# Load environment variables from .env
load_dotenv()

# Get settings from environment
BASE_URL = os.getenv("OPENCORP_BASE", "https://api.opencorporates.com/v0.4")
API_KEY = os.getenv("OPENCORP_API_KEY")

# This is the critical flag for demo stability
USE_MOCK = os.getenv("USE_REGISTRY_MOCK", "false").lower() == "true"

# Configure a simple logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 1. Pydantic Schema (Matches Function Contract) ---
# This validates our output and serves as our data contract
class RegistryResponse(BaseModel):
    """
    Defines the strict return schema for the registry lookup.
    """
    model_config = ConfigDict(coerce_numbers_to_str=True) # Good for IDs

    match: bool
    company_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[Literal["active", "inactive", "dissolved", "unknown", "other"]] = None
    incorporation_date: Optional[str] = None # YYYY-MM-DD


# --- 2. Helper Functions (Mocks & Fallbacks) ---

def _get_no_match_response() -> Dict[str, Any]:
    """
    Returns a valid, standardized "no match" response.
    """
    return RegistryResponse(match=False).model_dump()

def _get_mock_response(query: str) -> Dict[str, Any]:
    """
    Returns a hard-coded "happy path" response for demo stability.
    This is triggered if USE_REGISTRY_MOCK=true in the .env file.
    """
    logger.info(f"REGISTRY: Using MOCK response for query: '{query}'")
    # You can customize this mock to be whatever you need for your demo
    mock_data = {
        "match": True,
        "company_number": "08003277",
        "jurisdiction": "gb",
        "status": "active",
        "incorporation_date": "2012-03-21"
    }
    return RegistryResponse(**mock_data).model_dump()

def _normalize_status(status_str: Optional[str]) -> Literal["active", "inactive", "dissolved", "unknown", "other"]:
    """
    Cleans up the many OpenCorporates status strings into our 5 allowed types.
    """
    if not status_str:
        return "unknown"
    
    s = status_str.lower()
    
    if s in ["active", "company is active"]:
        return "active"
    if s in ["inactive", "in liquidation"]:
        return "inactive"
    if s in ["dissolved", "converted to another form", "closed"]:
        return "dissolved"
    
    # Default for any other complex status
    return "other"


# --- 3. Live API Call Logic ---

def _get_live_response(query: str) -> Dict[str, Any]:
    """
    Hits the live OpenCorporates API to find the best match.
    """
    logger.info(f"REGISTRY: Performing LIVE lookup for query: '{query}'")
    
    search_endpoint = f"{BASE_URL}/companies/search"
    params = {
        "q": query,
        "per_page": "1", # We only care about the best match
    }
    
    if API_KEY:
        params["api_token"] = API_KEY

    try:
        response = requests.get(search_endpoint, params=params, timeout=5)
        
        # Handle non-200 OK responses
        if response.status_code != 200:
            logger.error(f"REGISTRY: API returned status {response.status_code}")
            return _get_no_match_response()

        data = response.json()
        
        # Check if any results were found
        if not data.get("results") or data.get("total_count", 0) == 0:
            logger.warning(f"REGISTRY: No results found for query: '{query}'")
            return _get_no_match_response()

        # --- 4. Parse & Normalize the Response ---
        # We found a match! Take the first (best) one.
        best_match = data["results"]["companies"][0]["company"]
        
        # Normalize the data to fit our schema
        normalized_data = {
            "match": True,
            "company_number": best_match.get("company_number"),
            "jurisdiction": best_match.get("jurisdiction_code"),
            "status": _normalize_status(best_match.get("current_status")),
            "incorporation_date": best_match.get("incorporation_date") # Already in YYYY-MM-DD
        }
        
        # Validate and return the standardized dictionary
        return RegistryResponse(**normalized_data).model_dump()

    except requests.exceptions.RequestException as e:
        logger.error(f"REGISTRY: API request failed: {e}")
        # If the API is down, we MUST return a "no match" to avoid crashing
        return _get_no_match_response()


# --- 5. Main Function (Your Tool's Entry Point) ---

def search_registry(query: str) -> Dict[str, Any]:
    """
    Query company registry (OpenCorporates/mock) by name; return best match.

    This is the main function called by the agent.
    It decides whether to use the mock or live API based on .env settings.
    
    Args:
        query (str): The company name to search for.

    Returns:
        Dict: A dictionary matching the RegistryResponse schema.
    """
    if not query:
        logger.warning("REGISTRY: No query provided.")
        return _get_no_match_response()

    if USE_MOCK:
        # Use the stable, hard-coded mock response
        return _get_mock_response(query)
    else:
        # Use the live, external API
        return _get_live_response(query)