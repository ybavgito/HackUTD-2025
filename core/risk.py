import logging
from datetime import datetime
from typing import Dict, Any, Optional

# --- P1 (Agent) will provide the AgentState schema, (e.g., from core.state) ---
# For this file, we'll assume 'state' is a dictionary matching the AgentState.
# We're primarily interested in state['verifications'].

# Configure a simple logger
logger = logging.getLogger(__name__)

# --- 1. Your (P2's) Normalizer Functions ---

def _calculate_company_age(incorporation_date: Optional[str]) -> int:
    """
    Calculates the company's age in years from its incorporation date.
    
    Args:
        incorporation_date: A string in "YYYY-MM-DD" format.
        
    Returns:
        The company's age in whole years. Returns 0 if date is invalid/missing.
    """
    if not incorporation_date:
        return 0
        
    try:
        incorp_dt = datetime.strptime(incorporation_date, "%Y-%m-%d").date()
        today = datetime.today().date()
        
        # Calculate age in days
        age_timedelta = today - incorp_dt
        
        # Convert to years (using 365.25 to account for leap years)
        age_years = age_timedelta.days / 365.25
        
        return int(age_years)
        
    except ValueError:
        logger.warning(f"RISK: Could not parse incorporation_date: '{incorporation_date}'")
        return 0
    except Exception as e:
        logger.error(f"RISK: Error in _calculate_company_age: {e}")
        return 0

def _get_normalized_signals(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    *** THIS IS YOUR (P2's) CORE TASK ***
    
    This function "normalizes" the raw verification data from the AgentState
    into clean, deterministic boolean/int signals for the risk engine.
    
    Args:
        state: The full AgentState dictionary.
        
    Returns:
        A dictionary of clean risk signals.
    """
    
    # Get the raw verification data (produced by your services)
    registry_data = state.get("verifications", {}).get("registry", {})
    sanctions_data = state.get("verifications", {}).get("sanctions", {})
    
    # --- 1. Registry Signals ---
    
    # Signal: registry.match
    registry_match = registry_data.get('match', False)
    
    # Signal: registry.status == "active"
    is_active = registry_data.get('status') == 'active'
    
    # Signal: incorporation_age_years >= 3
    company_age = _calculate_company_age(registry_data.get('incorporation_date'))
    age_gte_3 = company_age >= 3
    
    # --- 2. Sanctions Signals ---
    
    # Signal: sanctions.match
    # This comes directly from your 'check_sanctions' tool
    sanctions_match = sanctions_data.get('match', False)
    
    # --- 3. (Optional) Advanced Signals ---
    # These were mentioned as optional rules. You could add them here.
    
    # Signal: address_mismatch (bool)
    # (Logic to compare extraction.address vs. a registry.address field)
    address_mismatch = False # Skipped for MVP
    
    # Signal: first_time_bank_details (bool)
    # (Logic to check a DB if bank details have been seen before)
    first_time_bank = False # Skipped for MVP
    
    
    # --- Return the clean signals for P1's compute_risk function ---
    return {
        "registry_match": registry_match,
        "is_active": is_active,
        "age_gte_3": age_gte_3,
        "sanctions_match": sanctions_match,
        "address_mismatch": address_mismatch,
        "first_time_bank": first_time_bank,
        "company_age_actual": company_age # Good for logging
    }


# --- 2. P1's (Agent Lead's) Functions ---
# P1 will write these, but they *depend* on your signals function above.

def _risk_label(score: int) -> str:
    """
    Maps a numeric score to a "low|medium|high" risk label.
    (From section 20.1)
    """
    return "high" if score >= 70 else ("medium" if score >= 40 else "low")

def compute_risk(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic scoring based on extraction + verifications.
    This is the main tool function P1's agent will call.
    (From section 6.4 and 8)
    """
    
    # 1. Get the clean signals from YOUR (P2's) function
    signals = _get_normalized_signals(state)
    
    # 2. Apply the deterministic risk scoring rules
    base = 0
    
    if signals['registry_match']:
        base += 30
    
    if signals['is_active']:
        base += 20
        
    if signals['age_gte_3']:
        base += 15
        
    if signals['address_mismatch']:
        base -= 10 # Optional rule
        
    if signals['first_time_bank']:
        base -= 10 # Optional rule
        
    # The sanctions rule is an override
    if signals['sanctions_match']:
        base = max(base, 90) # Set score to at least 90
        
    # 3. Finalize score and get label
    score = min(100, max(0, base)) # Clamp score between 0 and 100
    label = _risk_label(score)
    
    logger.info(f"RISK: Computed score: {score} ({label}). Signals: {signals}")
    
    # 4. Return the result per the function contract (6.4)
    return {
        "score": score,
        "label": label
    }