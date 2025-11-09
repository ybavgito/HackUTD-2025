import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from rapidfuzz import fuzz

# --- Setup ---
SANCTIONS_FILE_PATH = "data/sanctions.csv"
MATCH_THRESHOLD = 86  # As defined in the docs (section 20.2)

# Configure a simple logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 1. Pydantic Schema (Matches Function Contract) ---
class SanctionsResponse(BaseModel):
    """
    Defines the strict return schema for the sanctions check.
    """
    match: bool
    matched_name: Optional[str] = None
    score: int


# --- 2. Module-Level Data Loading ---
def _load_sanctions_data(file_path: str) -> List[str]:
    """
    Loads the sanctions list from the CSV file into memory.
    This runs ONCE when the application starts.
    """
    try:
        df = pd.read_csv(file_path)
        
        # Check if the 'name' column exists
        if 'name' not in df.columns:
            logger.error(f"SANCTIONS: 'name' column not found in {file_path}. List will be empty.")
            return []
            
        # Convert all names to lowercase for consistent matching and store in a list
        name_list = df['name'].str.lower().dropna().tolist()
        
        logger.info(f"SANCTIONS: Successfully loaded {len(name_list)} names from {file_path}")
        return name_list
        
    except FileNotFoundError:
        logger.error(f"SANCTIONS: File not found at {file_path}. Sanctions list will be empty.")
        return []
    except Exception as e:
        logger.error(f"SANCTIONS: Failed to load {file_path}. Error: {e}")
        return []

# Load the data into a global variable (in-memory cache)
# This code runs when the module is first imported.
_SANCTIONS_LIST = _load_sanctions_data(SANCTIONS_FILE_PATH)


# --- 3. Main Function (Your Tool's Entry Point) ---

def check_sanctions(name: str) -> Dict[str, Any]:
    """
    Local fuzzy match against the OFAC list using RapidFuzz partial_ratio.

    Args:
        name (str): The company name to check.

    Returns:
        Dict: A dictionary matching the SanctionsResponse schema.
    """
    
    # Guard clauses
    if not _SANCTIONS_LIST:
        logger.warning("SANCTIONS: Check skipped, sanctions list is empty.")
        return SanctionsResponse(match=False, matched_name=None, score=0).model_dump()
        
    if not name:
        logger.warning("SANCTIONS: Check skipped, provided name is empty.")
        return SanctionsResponse(match=False, matched_name=None, score=0).model_dump()

    # Normalize the input name
    name_lower = name.lower()
    
    # 1. Find the best match from the list
    # We use a lambda to compare the input 'name_lower' against every 'x' in the list
    try:
        best_match_name = max(
            _SANCTIONS_LIST, 
            key=lambda listed_name: fuzz.partial_ratio(name_lower, listed_name)
        )
        
        # 2. Calculate the score for that best match
        # (We do it again to get the score value, max() only gives the name)
        score = fuzz.partial_ratio(name_lower, best_match_name)
        
        # Round the score to the nearest integer
        int_score = int(round(score))
        
    except Exception as e:
        # This can happen if the list is empty and max() fails
        logger.error(f"SANCTIONS: Error during fuzzy matching: {e}")
        return SanctionsResponse(match=False, matched_name=None, score=0).model_dump()

    # 3. Apply threshold logic
    is_match = int_score >= MATCH_THRESHOLD
    
    # 4. Create response
    response = SanctionsResponse(
        match=is_match,
        matched_name=best_match_name.title() if is_match else None, # Capitalize for display
        score=int_score
    )
    
    if is_match:
        logger.warning(f"SANCTIONS: Potential MATCH found for '{name}'. Best: '{best_match_name}', Score: {int_score}")
    else:
        logger.info(f"SANCTIONS: No match for '{name}'. Best: '{best_match_name}', Score: {int_score}")

    return response.model_dump()