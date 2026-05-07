# Complete Agent Flow Diagram with Code Explanation

## 1. MAIN PIPELINE FLOW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│  USER INPUT                                                              │
│  └─> state.last_user_message = text                                     │
│  └─> state.conversation_turns += 1                                      │
│                                                                           │
│  ↓ (Line 3532-3541)                                                     │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  CONTROL LAYER: apply_control(state, text)  (Line 3547-3550)    │   │
│  │  • Check for explicit human request                              │   │
│  │  • Check if attempts > max_attempts (immediate handover)         │   │
│  │  • Calculate escalation_score                                    │   │
│  │  • Check correction loops                                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                     ↓                                                     │
│  ┌─────────────────┴──────────────────┬──────────────────┐               │
│  │                                    │                  │               │
│ YES                                  NO              No control           │
│  │                                    │                  │               │
│  ↓                                    ↓                  ↓               │
│                                                                           │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐     │
│  │ CONTROL TRIGGERED        │  │ NORMAL FLOW                      │     │
│  │ action = control[action] │  │ Continue to state checks         │     │
│  └──────────────────────────┘  └──────────────────────────────────┘     │
│         ↓                                    ↓                            │
│  ┌──────────────────────────┐               │                           │
│  │ if action=="handover"    │               │                           │
│  │   ↓                      │               │                           │
│  │ HUMAN HANDOVER           │               │                           │
│  │ (Line 3560-3569)         │               │                           │
│  │                          │               │                           │
│  │ if action=="reset"       │               │                           │
│  │   ↓                      │               │                           │
│  │ SOFT RESET               │               │                           │
│  │ (Line 3575-3583)         │               │                           │
│  └──────────────────────────┘               │                           │
│                                             ↓                            │
│                          ┌──────────────────────────────────┐            │
│                          │ Check state.intent & state.      │            │
│                          │ awaiting_new_issue               │            │
│                          │ (Line 3589-3595)                 │            │
│                          └──────────────────────────────────┘            │
│                                             ↓                            │
│                          ┌──────────────────────────────────┐            │
│                          │ INITIAL CASE EXTRACTION (NEW)    │            │
│                          │ • extract_full() - full mode     │            │
│                          │ • update_state() - store results │            │
│                          │ • update_case() - global mode    │            │
│                          │ (Line 3597-3611)                 │            │
│                          └──────────────────────────────────┘            │
│                                             ↓                            │
│                          ┌──────────────────────────────────┐            │
│                          │ Check if just_reset              │            │
│                          │ (Line 3617-3625)                 │            │
│                          │                                  │            │
│                          │ YES: ask_reverify_low_confidence │            │
│                          │ NO:  Continue                    │            │
│                          └──────────────────────────────────┘            │
│                                             ↓                            │
│                          ┌──────────────────────────────────┐            │
│                          │ Check missing_fields             │            │
│                          │ (Line 3631-3636)                 │            │
│                          │                                  │            │
│                          │ YES: ask_missing()               │            │
│                          │ NO:  Go to verification          │            │
│                          └──────────────────────────────────┘            │
│                                             ↓                            │
│                          ┌──────────────────────────────────┐            │
│                          │ build_verification_response()    │            │
│                          │ • Create summary                 │            │
│                          │ • Ask user to confirm            │            │
│                          │ (Line 3642-3646)                 │            │
│                          └──────────────────────────────────┘            │
│                                                                           │
│  ... (More flows below)                                                  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CONTROL LAYER - apply_control() 

**Location**: Line 3289-3365

### Execution Flow:

```
apply_control(state, text)
│
├─ Step 1: Check explicit human request (Line 3297-3305)
│  └─ Keywords: "human", "agent", "representative", "real person"
│  └─ Action: IMMEDIATE HANDOVER
│
├─ Step 2: Direct attempts threshold (Line 3313-3318)
│  ├─ Parameters: state.attempts > state.max_attempts (3)
│  ├─ Condition: attempts > 3
│  ├─ Action: SET sentiment="high" + HANDOVER
│  └─ Reason: "max_attempts_exceeded"
│
├─ Step 3: Repetition fatigue (Line 3320-3321)
│  ├─ Detects: Same question asked multiple times
│  └─ Action: SET sentiment="high"
│
├─ Step 4: Field correction drift (Line 3323-3327)
│  ├─ Detects: detect_correction_drift()
│  ├─ Condition: Same field corrected 3+ times
│  └─ Action: SET sentiment="high"
│
├─ Step 5: Multi-pass drift (Line 3329-3333)
│  ├─ Detects: detect_multi_pass_drift()
│  ├─ Condition: All fields corrected + corrections happening again
│  └─ Action: SET sentiment="high"
│
├─ Step 6: Corrections exceed fields (Line 3335-3339)
│  ├─ Detects: check_total_corrections_exceed_fields()
│  ├─ Condition: correction_count > department_field_count
│  └─ Action: SET sentiment="high"
│
├─ Step 7: Calculate escalation score (Line 3341)
│  ├─ Formula: (attempts*0.4) + (corrections*0.3) + (sentiment*0.3)
│  │
│  ├─ Sub-step 7a: Check score >= 0.75 (Line 3343-3347)
│  │  ├─ Parameters: escalation_score >= 0.75
│  │  └─ Action: HANDOVER (reason: "escalation_score_critical")
│  │
│  └─ Sub-step 7b: Check score >= 0.55 (Line 3349-3353)
│     ├─ Condition: score >= 0.55 AND NOT just_reset
│     └─ Action: SOFT RESET (reason: "escalation_score_high")
│
└─ Step 8: Correction loop (Line 3355-3363)
   ├─ Condition: awaiting_correction AND attempts >= 2 AND NOT just_reset
   └─ Action: SOFT RESET (reason: "correction_loop")

Return: None (if no control action) OR {action, reason}
```

### Code Block: apply_control()

```python
def apply_control(self, state, text):
    """
    PARAMETERS:
    - state: CaseState (current conversation state)
    - text: str (user input)
    
    RETURNS:
    - None (if no control action needed)
    - {action, reason} dict (if control action triggered)
    """
    
    t = str(text or "").lower().strip()
    
    # ========== CHECK 1: EXPLICIT HUMAN REQUEST ==========
    human_keywords = ["human", "agent", "representative", "real person"]
    if any(word in t for word in human_keywords):
        # IMMEDIATE HANDOVER - Don't ask questions, just transfer
        return {"action": "handover", "reason": "user_requested_human"}
    
    # ========== CHECK 2: DIRECT ATTEMPTS THRESHOLD ==========
    # CRITICAL FIX: This prevents infinite loops
    if state.attempts > state.max_attempts:  # max_attempts = 3
        state.sentiment = "high"
        # IMMEDIATE HANDOVER without waiting for score calculation
        return {"action": "handover", "reason": "max_attempts_exceeded"}
    
    # ========== CHECK 3-6: DETECT PROBLEMATIC PATTERNS ==========
    # These all trigger sentiment="high" which increases escalation score
    
    if self.u.detect_repetition_fatigue(state):
        state.sentiment = "high"
    
    is_field_drift, _ = state.detect_correction_drift()
    if is_field_drift:
        state.sentiment = "high"
    
    is_multi_pass, _ = state.detect_multi_pass_drift()
    if is_multi_pass:
        state.sentiment = "high"
    
    exceeds_fields, _ = state.check_total_corrections_exceed_fields()
    if exceeds_fields:
        state.sentiment = "high"
    
    # ========== CHECK 7: CALCULATE ESCALATION SCORE ==========
    escalation_score = self._calculate_escalation_score(state)
    
    # If score critical, immediate handover
    if escalation_score >= 0.75:
        return {"action": "handover", "reason": "escalation_score_critical"}
    
    # If score high (but not critical), trigger soft reset
    if escalation_score >= 0.55 and not state.just_reset:
        return {"action": "reset", "reason": "escalation_score_high"}
    
    # ========== CHECK 8: CORRECTION LOOP DETECTION ==========
    # If stuck in correction loop, reset
    if (state.awaiting_correction and 
        state.attempts >= 2 and 
        not state.just_reset):
        return {"action": "reset", "reason": "correction_loop"}
    
    # No control action needed
    return None
```

---

## 3. ESCALATION SCORE CALCULATION

**Location**: Line 3458-3478

### Parameters Used:

```
┌──────────────────────────────────────────────────────────────┐
│ ESCALATION SCORE FORMULA                                     │
│                                                               │
│ Score = (Attempt*0.4) + (Correction*0.3) + (Sentiment*0.3)  │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ COMPONENT 1: ATTEMPT SCORE (Weight: 0.4)                    │
│ ├─ Formula: min(1.0, attempts / max_attempts)               │
│ ├─ Parameters:                                               │
│ │  • attempts: Current attempt count (int)                   │
│ │  • max_attempts: 3 (hardcoded threshold)                  │
│ ├─ Range: 0.0 to 1.0                                        │
│ ├─ Examples:                                                 │
│ │  • 0 attempts → 0.0 score (0/3 = 0%)                     │
│ │  • 1 attempt  → 0.33 score (1/3 = 33%)                   │
│ │  • 2 attempts → 0.67 score (2/3 = 67%)                   │
│ │  • 3+ attempts → 1.0 score (capped at 1.0)               │
│ └─ Impact on total: Up to +0.4 points                       │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ COMPONENT 2: CORRECTION SCORE (Weight: 0.3)                 │
│ ├─ Formula: min(1.0, corrections / max_corrections)         │
│ ├─ Parameters:                                               │
│ │  • correction_count: Number of user corrections (int)     │
│ │  • max_correction_count: 5 (hardcoded threshold)         │
│ ├─ Range: 0.0 to 1.0                                        │
│ ├─ Examples:                                                 │
│ │  • 0 corrections → 0.0 score                              │
│ │  • 2 corrections → 0.4 score (2/5 = 40%)                 │
│ │  • 5+ corrections → 1.0 score (capped at 1.0)            │
│ └─ Impact on total: Up to +0.3 points                       │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ COMPONENT 3: SENTIMENT SCORE (Weight: 0.3)                  │
│ ├─ Mapping:                                                  │
│ │  • "high"       → 0.7 score (likely frustrated user)      │
│ │  • "medium_high"→ 0.4 score (some frustration)            │
│ │  • "medium"     → 0.1 score (neutral)                     │
│ │  • other        → 0.1 score                               │
│ │  • None         → 0.05 score (no sentiment detected)      │
│ ├─ Range: 0.05 to 0.7                                       │
│ └─ Impact on total: Up to +0.21 points (0.7 * 0.3)          │
│                                                               │
└──────────────────────────────────────────────────────────────┘

TOTAL ESCALATION SCORE RANGE: 0.05 to 1.0

THRESHOLDS:
├─ 0.00-0.54: No escalation action
├─ 0.55-0.74: SOFT RESET (non-destructive, ask user to restart)
└─ 0.75-1.00: HANDOVER (immediate transfer to human agent)
```

### Code Block: _calculate_escalation_score()

```python
def _calculate_escalation_score(self, state):
    """
    PARAMETERS:
    - state: CaseState object containing:
        • state.attempts (int): Number of failed field extractions
        • state.correction_count (int): Number of user corrections
        • state.max_attempts (int): 3
        • state.max_correction_count (int): 5
        • state.sentiment (str): "high", "medium_high", "medium", None
    
    RETURNS:
    - float: Score between 0.0 and 1.0
    
    USAGE: Determines if soft reset or human handover is needed
    """
    
    # ========== COMPONENT 1: ATTEMPT SCORE ==========
    # Normalize attempts (0-1 range)
    # If user has made 3 attempts on same field, this = 1.0
    attempt_score = min(1.0, state.attempts / state.max_attempts)
    # min(1.0, 2/3) = 0.67 for 2 attempts
    
    # ========== COMPONENT 2: CORRECTION SCORE ==========
    # Normalize corrections (0-1 range)
    # If user has corrected 5 fields, this = 1.0
    correction_score = min(
        1.0, 
        state.correction_count / float(state.max_correction_count)
    )
    # min(1.0, 3/5) = 0.6 for 3 corrections
    
    # ========== COMPONENT 3: SENTIMENT SCORE ==========
    # Map sentiment to numeric score
    if state.sentiment == "high":
        # User is clearly frustrated/distressed
        sentiment_score = 0.7
    elif state.sentiment == "medium_high":
        # User showing some frustration
        sentiment_score = 0.4
    elif state.sentiment is not None:
        # Other sentiment values (medium, low)
        sentiment_score = 0.1
    else:
        # No sentiment detected yet
        sentiment_score = 0.05
    
    # ========== CALCULATE TOTAL SCORE ==========
    # Weighted average: attempts(40%) + corrections(30%) + sentiment(30%)
    total_score = (
        attempt_score * 0.4 +      # Attempt component
        correction_score * 0.3 +   # Correction component
        sentiment_score * 0.3      # Sentiment component
    )
    
    return total_score
    
    # EXAMPLES:
    # Scenario 1: No problems
    # • attempts=0, corrections=0, sentiment=None
    # • score = (0*0.4) + (0*0.3) + (0.05*0.3) = 0.015 ✓ No action
    #
    # Scenario 2: User frustrated but low attempts
    # • attempts=1, corrections=0, sentiment="high"
    # • score = (0.33*0.4) + (0*0.3) + (0.7*0.3) = 0.345 ✓ No action
    #
    # Scenario 3: Multiple problems combined
    # • attempts=2, corrections=2, sentiment="high"
    # • score = (0.67*0.4) + (0.4*0.3) + (0.7*0.3) = 0.57 ⚠️ SOFT RESET
    #
    # Scenario 4: Critical situation
    # • attempts=3, corrections=5, sentiment="high"
    # • score = (1.0*0.4) + (1.0*0.3) + (0.7*0.3) = 1.0 🚨 HANDOVER
```

---

## 4. SOFT RESET FLOW

**Location**: Line 3575-3583 (triggered), Line 313-325 (executed)

### Parameters and Behavior:

```
TRIGGER CONDITIONS:
├─ escalation_score >= 0.55 (Line 3349-3353)
├─ correction_loop detected (Line 3355-3363)
└─ Direct attempts threshold (Line 3313-3318)

STATE CHANGES ON SOFT RESET:
├─ CLEARED:
│  ├─ attempts → 0 (reset attempt counter)
│  ├─ field_attempts → {} (clear per-field attempts)
│  ├─ correction_count → 0 (reset correction count)
│  ├─ correction_passes → 0
│  └─ fields_corrected_in_pass → set()
│
├─ PRESERVED:
│  ├─ entities → All extracted field values (keep data)
│  ├─ entity_confidence → Confidence scores (keep reliability info)
│  ├─ sentiment → Current sentiment (keep emotional context)
│  ├─ language → Detected language (keep language info)
│  └─ All other entity/extraction data
│
└─ SET FOR REVERIFICATION:
   ├─ just_reset = True
   ├─ awaiting_new_issue = True
   └─ Triggers low-confidence field reverification

PURPOSE:
• User gets fresh start without losing context
• Effort counters reset (no penalty for previous failures)
• Can re-collect information with better understanding
• Low-confidence fields reverified (< 0.80 confidence)
```

### Code Block: soft_reset()

```python
def soft_reset(self):
    """
    NON-DESTRUCTIVE RESET
    
    Clears effort/attempt counters but PRESERVES extracted data
    Used when escalation score gets too high or correction loop detected
    
    PARAMETERS: None (operates on self)
    
    RETURNS: None (modifies state in-place)
    """
    
    # ========== CLEAR EFFORT COUNTERS ==========
    # These track how hard we've tried to get the field
    self.attempts = 0  # Reset field extraction attempts
    self.field_attempts = {}  # Clear per-field attempt tracking
    
    # ========== CLEAR CORRECTION TRACKING ==========
    # These track how many times user has corrected
    self.correction_count = 0  # Reset total corrections count
    self.correction_passes = 0  # Reset number of correction passes
    self.fields_corrected_in_pass = set()  # Clear fields corrected in current pass
    
    # ========== PRESERVE EXTRACTED DATA ==========
    # IMPORTANT: DO NOT clear entities, confidence, sentiment, language
    # User data stays intact so we don't lose information
    # Example: If user said "John" for name, we keep that
    
    # ========== SET FLAGS FOR NEW FLOW ==========
    self.just_reset = True  # Flag that we just reset
    self.awaiting_new_issue = True  # Prepare to re-explain issue
    self.awaiting_reverify_confirmation = False  # Clear reverify state
    
    # ========== RESET SPECIFIC FIELD TRACKING ==========
    self.last_corrected_field = None  # Clear last corrected field info
    self.reverify_attempts = 0  # Clear reverification attempts
    
    return
    
    # EFFECT ON NEXT FLOW:
    # 1. System asks: "Let me start fresh. Can you explain again?"
    # 2. User explains issue again (from fresh perspective)
    # 3. System extracts intent & entities again
    # 4. If just_reset == True:
    #    - Low-confidence fields (< 0.80) are reverified
    #    - User asked: "Is [field] = [value] correct?"
    # 5. If user confirms/corrects → confidence boosted to 0.95
    # 6. Continue with normal flow (missing fields, verification)
```

---

## 5. HUMAN HANDOVER FLOW

**Location**: Line 3560-3569

### Triggers:

```
HANDOVER TRIGGERS (Immediate Transfer):
├─ Explicit user request (Line 3301-3305)
│  └─ Keywords: "human", "agent", "representative", "real person"
│
├─ Max attempts exceeded (Line 3313-3318)
│  └─ state.attempts > 3
│
├─ Escalation score critical (Line 3343-3347)
│  └─ escalation_score >= 0.75
│
└─ Risk indicators detected
   └─ Keywords: "assault", "abuse", "threat", "suicide", etc.

PARAMETERS USED:
├─ state.sentiment (set to "high" before handover)
├─ state.escalate_reason (reason for escalation)
└─ state.entities (all collected data sent to human)
```

### Code Block: human_handover()

```python
def human_handover(self, state):
    """
    IMMEDIATE TRANSFER TO HUMAN AGENT
    
    Called when escalation_score >= 0.75 or explicit request
    
    PARAMETERS:
    - state: CaseState with all collected information
    
    RETURNS:
    - {text: handover_message, action: "handover"}
    """
    
    # ========== LOG ESCALATION REASON ==========
    # Record why this case was escalated
    state.escalate("conversation_complexity")
    # or other reasons: "max_attempts", "user_frustration", etc.
    
    # ========== GENERATE HANDOVER MESSAGE ==========
    # Inform user they're being transferred
    return {
        "text": """
I understand you're having difficulty with this process.
I'm connecting you to a human agent who has full access 
to your account and can provide personalized assistance.

Please hold while I transfer you...
        """,
        "action": "handover"
    }
    
    # WHAT HAPPENS NEXT:
    # 1. User input stops being processed by agents
    # 2. Human agent receives:
    #    - Full conversation history
    #    - All extracted data: state.entities
    #    - Confidence scores: state.entity_confidence
    #    - Sentiment: state.sentiment
    #    - Detected language: state.language
    #    - Number of attempts and corrections made
    # 3. Human agent can:
    #    - View context of conversation
    #    - Make final decision on case
    #    - Manually collect missing information
    #    - Process the complaint directly
    # 4. Case is marked as escalated in system
```

---

## 6. LOCAL CORRECTION FLOW (Correction in Verification Stage)

**Location**: Line 3800+

### Flow Diagram:

```
USER IN VERIFICATION STAGE
│
├─ User sees summary: "Name: John, Email: john@email.com, ..."
│
├─ User responds:
│  ├─ "Yes, all correct" → Proceed to completion
│  ├─ "No, [field] is wrong" → Enter correction mode
│  └─ "I need to change X" → Trigger correction
│
↓
DECISION ENGINE: decide(state, text)
• Analyzes user response
• Determines: Which field needs correction?
• Returns: {action: "correct", target_field: "email", ...}

↓
CORRECTION RESPONSE (Line 3814-3860)
│
├─ Extract new value for field
│  └─ extract(text, mode="field", target_field="email", state=state)
│
├─ Update case with new value
│  └─ update_case(state, extracted, mode="correction")
│     └─ Increments: correction_count += 1
│
├─ Store correction for drift detection
│  └─ state.record_correction(field, new_value)
│
└─ Ask: "Is this correct?" for verification

↓
RE-VERIFY CORRECTION
│
├─ If user confirms → Continue to next field
├─ If user rejects → Ask correction again
└─ If 3+ corrections on same field → Trigger reset

↓
CORRECTION DRIFT DETECTION
│
├─ Same field corrected 3+ times? → Set sentiment="high"
├─ All fields corrected, now correcting again? → Set sentiment="high"
├─ Total corrections > field count? → Set sentiment="high"
│
└─ If any trigger → apply_control() triggers soft reset
```

### Code Block: Field Correction Logic

```python
if action == "fill_field":
    """
    PARAMETERS:
    - action: "fill_field" (from decision engine)
    - state.last_asked_field: Which field user is answering
    - text: User's response
    - target_field: Extracted field name
    
    PROCESS:
    1. Extract value from user response
    2. Validate extracted value
    3. Update case state
    4. Track correction count
    5. Check for drift/loops
    6. Decide next step
    """
    
    target_field = state.last_asked_field
    
    # ========== EXTRACT FIELD VALUE ==========
    extracted = self.u.extract(
        text,
        mode="field",
        target_field=target_field,
        state=state
    )
    
    if not extracted:
        # Extraction failed (unclear value)
        # Ask user again
        return (state, self.i.ask_missing(state))
    
    # ========== UPDATE CASE ==========
    # mode="normal" means: process corrections normally
    state = self.c.update_case(
        state,
        extracted,
        mode="normal"
    )
    # This internally:
    # • Stores entity value
    # • Sets confidence score
    # • Increments correction_count if this is correction
    
    # ========== INCREMENT CONFIDENCE ==========
    # Successful extraction → boost confidence
    state.increase_confidence(0.02)  # +2% confidence
    
    # ========== RESET ATTEMPT COUNTERS ==========
    state.reset_attempts()  # Clear attempts on this field
    state.reset_field_attempt(target_field)
    
    # ========== CHECK FOR MORE FIELDS ==========
    if state.missing_fields:
        # More fields to collect
        return (state, self.i.ask_missing(state))
    
    # All fields collected
    return (state, self.build_verification_response(state))
```

---

## 7. REVERIFICATION AFTER SOFT RESET

**Location**: Line 3653-3734

### Flow:

```
AFTER SOFT RESET:
│
├─ System says: "Let me start fresh. Tell me again..."
├─ User explains issue again
├─ System extracts intent & entities (fresh extraction)
│
└─ Check: if just_reset == True:
   │
   ├─ YES: Find low-confidence fields (< 0.80)
   │  │
   │  ├─ Ask: "You mentioned [field] = [value]. Is that correct?"
   │  │
   │  ├─ User response options:
   │  │  ├─ "Yes" → Set confidence = 0.95, move to next field
   │  │  ├─ "No" → Ask: "What's the correct value?"
   │  │  ├─ "No, it's X" → Apply correction, set confidence = 0.95
   │  │  └─ "Umm... maybe?" → Treat as rejection, ask for value
   │  │
   │  └─ Track: reverify_attempts (max 2 before reset again)
   │
   └─ NO: Continue to missing fields

PARAMETERS:
├─ state.just_reset: Flag indicating fresh extraction
├─ state.entity_confidence[field]: Confidence for each field
├─ state.awaiting_reverify_confirmation: Currently reverifying?
├─ state.reverify_attempts: How many reverify attempts on current field?
└─ state.max_reverify_attempts: Maximum reverify attempts (2)
```

### Code Block: Reverification Logic

```python
if state.last_action == "reverify_low_confidence":
    """
    REVERIFICATION PHASE (after soft reset)
    
    PARAMETERS:
    - state.last_action: "reverify_low_confidence"
    - state.current_field: Which field we're reverifying
    - state.entity_confidence: Confidence score for field
    - state.just_reset: True (in reverification phase)
    - text: User's response to "Is [field] = [value] correct?"
    
    FLOW:
    1. Ask user about low-confidence field
    2. Evaluate user response (yes/no/correction)
    3. Update confidence or ask for correction
    4. Move to next low-confidence field or continue
    """
    
    target_field = state.current_field
    
    # ========== USER CONFIRMS THE VALUE ==========
    if self.d.is_pure_yes(text_normalized):
        # User said "yes" or similar
        state.entity_confidence[target_field] = 0.95  # Boost to high
        state.awaiting_reverify_confirmation = False
        state.reverify_attempts = 0
        state.last_action = None
        # Move to check next low-confidence field
    
    # ========== USER PROVIDES EXPLICIT CORRECTION ==========
    elif self.d.detect_explicit_correction(text_normalized):
        # User said "No, it's X" or "Change it to X"
        extracted = self.u.extract(
            text,
            mode="field",
            target_field=target_field,
            state=state
        )
        
        if extracted:
            # Correction accepted
            self.c.update_case(
                state,
                extracted,
                mode="reverify"  # Don't inflate correction count
            )
            state.entity_confidence[target_field] = 0.95
            state.awaiting_reverify_confirmation = False
            state.reverify_attempts = 0
            state.last_action = None
        else:
            # Extraction failed, ask again
            return (state, self.i.ask_reverify_correction(state))
    
    # ========== USER REJECTS (without correction) ==========
    elif self.d.is_pure_rejection(text_normalized):
        # User said "No" or "That's wrong"
        # Ask: "What's the correct value?"
        return (state, self.i.ask_reverify_correction(state))
    
    # ========== VAGUE RESPONSE ==========
    else:
        # User said "Umm..." or "Maybe?" 
        # Treat as rejection, ask for correction
        return (state, self.i.ask_reverify_correction(state))
    
    # ========== CONTINUE TO NEXT LOW-CONFIDENCE FIELD ==========
    reverify_response = self.i.ask_reverify_low_confidence(state)
    
    if reverify_response:
        # Another low-confidence field found
        return (state, reverify_response)
    
    # No more low-confidence fields
    state.just_reset = False
    
    # Continue with missing fields or verification
    if state.missing_fields:
        return (state, self.i.ask_missing(state))
    
    return (state, self.build_verification_response(state))
```

---

## 8. COMPLETE STATE TRANSITIONS

```
STATE FLOW DIAGRAM:

┌─────────────────────────────────────────────────────────────┐
│                      START                                   │
│                  (New Conversation)                          │
│              intent = None                                   │
│                 stage = collection                           │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
        ┌──────────────────────┐
        │   USER INPUT         │
        │  (First message)     │
        └──────────┬───────────┘
                   │
                   ↓
      ┌────────────────────────────┐
      │  INITIAL CASE EXTRACTION   │
      │  • extract_full()          │
      │  • Intent detection        │
      │  • Language detection      │
      │  • Sentiment analysis      │
      └────────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
   intent = null         intent = found
        │                     │
        ↓                     ↓
    ASK ISSUE             CHECK CONFIDENCE
    "What's wrong?"            │
                       ┌───────┴────────┐
                       │                │
                       ↓                ↓
                  High confidence  Low confidence
                  (>= 0.80)        (< 0.80)
                       │                │
                       └───────┬────────┘
                               │
                               ↓
                   ┌──────────────────────┐
                   │ CHECK MISSING FIELDS │
                   └──────────┬───────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ↓                   ↓
              Missing found        All collected
                    │                   │
                    ↓                   ↓
              ASK MISSING         VERIFICATION
             "What's your        (show summary)
              email?"                   │
                    │                   │
                    └─────────┬─────────┘
                              │
                    ┌─────────↓──────────┐
                    │                    │
                    ↓                    ↓
                Correct            Needs change
                (user says           (user says
                 "yes")           "no, X is wrong")
                    │                    │
                    ↓                    ↓
             COMPLETION            CORRECTION MODE
         (case recorded)              (update field)
                    │                    │
                    └─────────┬─────────┘
                              │
              ┌───────────────┴────────────────┐
              │                                │
              ↓                                ↓
        More corrections              No more corrections
              │                                │
              └─────────┬─────────────────────┘
                        │
              ┌─────────↓──────────┐
              │ CHECK DRIFT        │
              └──────────┬─────────┘
                         │
         ┌───────────────┴────────────────┐
         │                                │
         ↓                                ↓
    Drift detected               No drift
         │                        │
         ↓                        ↓
    SOFT RESET            RE-VERIFY (ask about
    (start fresh)         corrected fields)
         │                        │
         └─────────┬──────────────┘
                   │
                   ↓
         (same cycle repeats
          with fresh perspective)
```

---

## 9. KEY STATE PARAMETERS

```
PARAMETERS USED IN CONTROL & ESCALATION:

State Variables:
├─ state.attempts (int: 0-3)
│  └─ Incremented on each failed field extraction
│  └─ Reset to 0 on soft_reset()
│  └─ Triggers handover if > 3
│
├─ state.correction_count (int: 0-∞)
│  └─ Incremented when user corrects a field
│  └─ Used in escalation score calculation
│  └─ Reset to 0 on soft_reset()
│
├─ state.sentiment (str: None/"low"/"medium"/"medium_high"/"high")
│  └─ Detected via detect_frustration()
│  └─ Drives escalation score
│  └─ "high" sentiment increases escalation by 21% (0.7 * 0.3)
│
├─ state.entity_confidence (dict: field → 0.0-1.0)
│  └─ Tracks reliability of each extracted value
│  └─ Values < 0.80 trigger reverification after reset
│  └─ Boosted to 0.95 after user confirmation
│
├─ state.just_reset (bool: True/False)
│  └─ Set to True after soft_reset()
│  └─ Prevents immediate re-reset
│  └─ Triggers reverification flow
│
├─ state.awaiting_correction (bool: True/False)
│  └─ True when user is correcting a field
│  └─ Used in correction loop detection
│
├─ state.max_attempts (int: 3)
│  └─ Hardcoded threshold
│  └─ Triggers handover if exceeded
│
├─ state.max_correction_count (int: 5)
│  └─ Hardcoded threshold
│  └─ Used in escalation score normalization
│
└─ state.max_field_attempts (int: 3)
   └─ Max times to ask same field
   └─ Prevents infinite loops on single field
```

---

## 10. EXAMPLE SCENARIOS

### Scenario 1: Normal Flow (No Issues)

```
USER: "I want to report a damaged item"
SYSTEM: [Extract intent, entities, sentiment=None]
SYSTEM: "What's your name?"
USER: "John Smith"
SYSTEM: [Extract name, confidence=0.95]
SYSTEM: "What's your email?"
USER: "john@email.com"
SYSTEM: [Extract email, confidence=0.95]
SYSTEM: [All fields collected]
SYSTEM: [Summary] "Is this correct?"
USER: "Yes"
SYSTEM: [Case recorded, completion]

STATE PROGRESSION:
├─ attempts: 0 → 0 → 0 → 0 (no failed extractions)
├─ correction_count: 0 → 0 → 0 → 0 (no corrections)
├─ sentiment: None (no frustration detected)
├─ escalation_score: 0.015 (minimal)
└─ action: No reset/handover needed
```

### Scenario 2: Reset Due to Frustration (Score >= 0.55)

```
USER: "I want to report a billing issue"
SYSTEM: [Extract, sentiment=medium]

USER: [Repeats request, frustrated tone]
SYSTEM: [Asks for name]
USER: "Why are you asking? I don't understand!"
SYSTEM: [detect_frustration() → sentiment="high"]
SYSTEM: [Calculate escalation_score]

CALCULATION:
├─ attempts = 1 → score = 1/3 * 0.4 = 0.133
├─ correction_count = 0 → score = 0/5 * 0.3 = 0.0
├─ sentiment = "high" → score = 0.7 * 0.3 = 0.21
└─ total = 0.133 + 0.0 + 0.21 = 0.343 (no action yet)

[Continue...]
USER: [Tries multiple times to answer, keeps confused]
SYSTEM: [Multiple attempts, sentiment stays "high"]

AFTER 2-3 TURNS:
├─ attempts = 2 → score = 2/3 * 0.4 = 0.267
├─ sentiment = "high" → score = 0.7 * 0.3 = 0.21
└─ total ≈ 0.55 ✓ TRIGGERS SOFT RESET

SYSTEM: [Soft reset triggered]
SYSTEM: "I understand this is frustrating. Let me start fresh."
SYSTEM: [ask_rephrase() called]

STATE AFTER SOFT RESET:
├─ attempts: 2 → 0 (reset)
├─ correction_count: 0 → 0 (unchanged)
├─ just_reset: False → True (flag set)
├─ sentiment: "high" (preserved)
└─ entities: All preserved (keep data)

NEXT TURN:
USER: "Okay, I was charged twice for my subscription"
SYSTEM: [Fresh extraction, new confidence scores]
SYSTEM: [if just_reset] → Reverify low-confidence fields
```

### Scenario 3: Direct Handover (Attempts Exceeded)

```
USER: "I ordered a laptop"
SYSTEM: "What's the order ID?"
USER: "uh... I don't know"
SYSTEM: attempts = 0 → "Can you find it?"

USER: "It's in my email"
SYSTEM: attempts = 1 → "What email?"
USER: "I forgot which email"
SYSTEM: attempts = 2 → "Do you have order number?"

USER: "No I don't"
SYSTEM: attempts = 3 → [THRESHOLD REACHED]

apply_control() check:
if state.attempts > state.max_attempts (3 > 3? NO)
  → Continue

[One more turn...]
USER: "I really can't remember"
SYSTEM: attempts = 4

apply_control() check:
if state.attempts > state.max_attempts (4 > 3? YES) ✓
  → state.sentiment = "high"
  → IMMEDIATE HANDOVER

RETURN: {action: "handover", reason: "max_attempts_exceeded"}

SYSTEM: "Let me transfer you to an agent..."
[User connected to human agent]
```

---

## Summary of Key Concepts

| Concept | Threshold | Action | Parameters |
|---------|-----------|--------|-----------|
| **Direct Attempts** | > 3 | Handover | state.attempts, max_attempts=3 |
| **Escalation Score** | >= 0.55 | Soft Reset | (attempts*0.4) + (corrections*0.3) + (sentiment*0.3) |
| **Critical Score** | >= 0.75 | Handover | Same calculation |
| **Low Confidence** | < 0.80 | Reverify | entity_confidence[field] |
| **Soft Reset** | Various | Reset+Preserve | just_reset=True, preserve entities |
| **Human Request** | Keywords | Handover | "human", "agent", "representative" |

