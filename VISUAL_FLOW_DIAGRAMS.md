
# CLEAN AGENT FLOW DIAGRAMS WITH CODE EXPLANATIONS

---

## DIAGRAM 1: MAIN AGENT PIPELINE FLOW

```
                           ╔═══════════════════════════════════╗
                           ║       USER INPUT                  ║
                           ║   state.last_user_message = text  ║
                           ║   conversation_turns += 1         ║
                           ╚════════════════╤════════════════╝
                                            │
                                            ▼
                    ┌───────────────────────────────────────────┐
                    │   CONTROL LAYER (apply_control)           │
                    │   • Check explicit human request          │
                    │   • Check attempts > 3                    │
                    │   • Calculate escalation score            │
                    │   • Check correction loops                │
                    └───────────┬───────────────────────────────┘
                                │
                ┌───────────────┴────────────────┬──────────────┐
                │                                │              │
              YES                              NO              NULL
                │                                │              │
                ▼                                ▼              ▼
        ╔═════════════════╗           Continue normal flow
        ║ CONTROL ACTION  ║
        ╚════════╤════════╝
                 │
        ┌────────┴────────┐
        │                 │
    HANDOVER          RESET
        │                 │
        ▼                 ▼
   ┌──────────┐    ┌──────────────────┐
   │ HUMAN    │    │ SOFT RESET       │
   │HANDOVER  │    │ ask_rephrase()   │
   │(Line     │    │ (Line 3575-3583) │
   │3560-3569)│    └──────────┬───────┘
   └──────────┘               │
                              ▼
                    ┌─────────────────────────────┐
                    │ state.just_reset = True     │
                    │ state.awaiting_new_issue=True
                    │ Preserve all entities       │
                    │ Clear effort counters       │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │ Check state.intent == None OR    │
                    │ state.awaiting_new_issue == True │
                    │ (Line 3589-3595)                 │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │ INITIAL CASE EXTRACTION          │
                    │ • extract_full() mode            │
                    │ • Detect: intent, entities,      │
                    │   sentiment, language            │
                    │ • update_state()                 │
                    │ • update_case(mode="global")     │
                    │ (Line 3597-3611)                 │
                    └──────────────┬───────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────┐
                    │ Check: just_reset == True?       │
                    │ (Line 3617-3625)                 │
                    └────────┬─────────────┬───────────┘
                             │             │
                            YES            NO
                             │             │
                             ▼             ▼
                    ┌──────────────────┐   │
                    │ REVERIFY LOW     │   │
                    │ CONFIDENCE FIELDS│   │
                    │ (< 0.80)         │   │
                    │ ask_reverify_    │   │
                    │ low_confidence() │   │
                    └────────┬─────────┘   │
                             │             │
                             └──────┬──────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │ Check: missing_fields?           │
                    │ (Line 3631-3636)                 │
                    └────────┬─────────────┬───────────┘
                             │             │
                            YES            NO
                             │             │
                             ▼             ▼
                    ┌──────────────────┐   │
                    │ ASK MISSING      │   │
                    │ ask_missing()    │   │
                    │ (Line 3633-3636) │   │
                    └────────┬─────────┘   │
                             │             │
                             └──────┬──────┘
                                    │
                                    ▼
                    ╔══════════════════════════════════╗
                    ║ build_verification_response()    ║
                    ║ • Create summary                 ║
                    ║ • Ask user: "Is this correct?"   ║
                    ║ (Line 3642-3646)                 ║
                    ╚══════════════════════════════════╝
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │ DECISION ENGINE                  │
                    │ decide(state, text)              │
                    │ (Line 3803-3806)                 │
                    └────────┬─────────────┬───────────┘
                             │             │
                           YES             NO
                    CORRECTIONS        COMPLETION
                             │             │
                             ▼             ▼
                    (See local correction diagram below)
```

---

## DIAGRAM 2: CONTROL LAYER - ESCALATION DECISION

```
                    ╔════════════════════════════════════════╗
                    ║   apply_control(state, text)           ║
                    ║   (Line 3289-3365)                     ║
                    ╚════════════════╤═══════════════════════╝
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
    ╔═════════════╗            ┌──────────────┐          ┌──────────────┐
    ║ CHECK 1:    ║            │ CHECK 2-6:   │          │ CHECK 7:     │
    ║ EXPLICIT    ║            │ PATTERN      │          │ ESCALATION   │
    ║ HUMAN       ║            │ DETECTION    │          │ SCORE        │
    ║ REQUEST     ║            │ (Line        │          │ (Line 3341)  │
    ║ (Line       ║            │ 3320-3339)   │          │              │
    ║ 3301-3305)  ║            │              │          │              │
    ╚══════╤══════╝            └──────┬───────┘          └──────┬───────┘
           │                          │                         │
         YES                        TRIGGER                   CALCULATE
           │                      sentiment=                  FORMULA:
           │                       "high"                     (A*0.4) +
           ▼                          │                       (C*0.3) +
    ┌─────────────────┐              │                       (S*0.3)
    │ KEYWORDS:       │              ▼                         │
    │ • "human"       │         SET sentiment                 │
    │ • "agent"       │         to "high"                     │
    │ • "real person" │              │                        │
    │                 │              └────────┬───────────────┘
    │ ACTION:         │                       │
    │ IMMEDIATE       │                       ▼
    │ HANDOVER        │              Score >= 0.75?
    │ (no questions)  │                       │
    └─────────────────┘           ┌───────────┴───────────┐
                                  │                       │
                                YES                       NO
                                 │                        │
                                 ▼                        ▼
                          ╔─────────────╗      Score >= 0.55?
                          ║  HANDOVER   ║              │
                          ║ (reason:    ║   ┌──────────┴──────────┐
                          ║"escalation_ ║   │                     │
                          ║score_       │  YES                    NO
                          ║critical")   ║   │                      │
                          ╚─────────────╝   ▼                      ▼
                                   ╔─────────────╗      ┌──────────────┐
                                   ║ SOFT RESET  ║      │ NO ACTION    │
                                   ║ (if not     ║      │ CONTINUE     │
                                   ║just_reset)  ║      │ NORMAL FLOW  │
                                   ╚─────────────╝      └──────────────┘

    ═══════════════════════════════════════════════════════════════════════════

    ADDITIONAL CHECK: CORRECTION LOOP (Line 3355-3363)
    
    if (awaiting_correction AND attempts >= 2 AND NOT just_reset):
        ▼
    ┌─────────────────────┐
    │ SOFT RESET          │
    │ (reason:            │
    │ "correction_loop")  │
    └─────────────────────┘
```

---

## DIAGRAM 3: HUMAN HANDOVER FLOW

```
                    ┌───────────────────────────────────────┐
                    │ HUMAN HANDOVER TRIGGERED              │
                    │ (Line 3560-3569)                      │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ╔═══════════════════════════════════════╗
                    ║ state.escalate(reason)                ║
                    ║ • Log escalation reason               ║
                    ║ • Mark case as escalated              ║
                    ║ (Line 3562-3564)                      ║
                    ╚═══════════════╤═════════════════════╝
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ COLLECT DATA TO SEND TO HUMAN AGENT                       │
    │                                                            │
    │ • state.entities: All extracted fields                    │
    │ • state.entity_confidence: Reliability scores             │
    │ • state.sentiment: User's emotional state                 │
    │ • state.language: Detected language                       │
    │ • state.conversation_turns: Number of exchanges           │
    │ • state.attempts: Failed field extractions                │
    │ • state.correction_count: User corrections made           │
    │ • state.last_user_message: Latest input                   │
    │                                                            │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ╔════════════════════════════════════════════════════════════╗
    ║ SEND HANDOVER MESSAGE TO USER                              ║
    ║                                                             ║
    ║ "I understand you're having difficulty with this process. ║
    ║  I'm connecting you to a human agent who has full access  ║
    ║  to your account and can provide personalized assistance. ║
    ║                                                             ║
    ║  Please hold while I transfer you..."                     ║
    ║                                                             ║
    ║ action: "handover"                                        ║
    ╚═══════════════╤════════════════════════════════════════════╝
                    │
                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ AGENT PIPELINE STOPS                                       │
    │ • No more automated responses                              │
    │ • Human agent takes over                                   │
    │ • Case marked as: ESCALATED / IN_PROGRESS                  │
    └────────────────────────────────────────────────────────────┘
                    │
                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ HUMAN AGENT RECEIVES:                                      │
    │                                                             │
    │ ✓ Full conversation history                                │
    │ ✓ All extracted data (name, email, issue, etc.)            │
    │ ✓ Confidence scores for each field                         │
    │ ✓ Sentiment analysis (high frustration?)                   │
    │ ✓ Number of attempts made by user                          │
    │ ✓ Why escalation was triggered                             │
    │ ✓ User's preferred language                                │
    │                                                             │
    │ Human can then:                                            │
    │ • Verify information directly with user                    │
    │ • Make final decision on case                              │
    │ • Process complaint immediately                            │
    │ • Provide personalized resolution                          │
    │ • Update case status                                       │
    └────────────────────────────────────────────────────────────┘

    ═══════════════════════════════════════════════════════════════

    TRIGGERS FOR HANDOVER (All lead here):
    
    1. Explicit request: "I want to talk to a human"
    2. Attempts exceeded: attempts > 3
    3. Escalation critical: score >= 0.75
    4. Risk keywords: "assault", "abuse", "threat", etc.
```

---

## DIAGRAM 4: SOFT RESET FLOW

```
                    ╔═══════════════════════════════════════╗
                    ║ SOFT RESET TRIGGERED                  ║
                    ║ (Line 3575-3583)                      ║
                    ╚═══════════════╤═════════════════════╝
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
              Trigger 1:                      Trigger 2:
           Score >= 0.55                   Correction Loop
              (User                       (awaiting_correction
              frustrated)                  + attempts >= 2)
                   │                                 │
                   └────────────────┬────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ state.soft_reset()                    │
                    │ (Line 313-325)                        │
                    └───────────────┬───────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
    ╔═════════════════╗      ╔═════════════════╗      ╔═════════════════╗
    ║ CLEARED         ║      ║ PRESERVED       ║      ║ FLAGS SET       ║
    ║ (Reset)         ║      ║ (Keep Data)     ║      ║                 ║
    ╚═════════════════╝      ╚═════════════════╝      ╚═════════════════╝
    │                         │                       │
    ├─ attempts = 0           ├─ entities            ├─ just_reset=True
    ├─ field_attempts={}      ├─ entity_confidence   ├─ awaiting_new=True
    ├─ correction_count=0     ├─ sentiment           └─ awaiting_verify=False
    ├─ correction_passes=0    ├─ language
    └─ fields_corrected={}    ├─ department
                              └─ intent

        EFFECT: User gets fresh start with cleared effort,
               but system remembers extracted data & context

                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ ask_rephrase() called                 │
                    │ (Line 3580-3582)                      │
                    │                                       │
                    │ SYSTEM MESSAGE:                       │
                    │ "Let me start fresh. Can you tell me  │
                    │  about your issue again from the      │
                    │  beginning? I have your information   │
                    │  saved (name, email, etc.)"           │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ USER RESPONDS WITH NEW EXPLANATION    │
                    │                                       │
                    │ Example:                              │
                    │ "I ordered a laptop 2 weeks ago and   │
                    │  it arrived with broken screen"       │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ FRESH EXTRACTION                      │
                    │ • extract_full() - new parsing        │
                    │ • Re-detect intent, sentiment         │
                    │ • Generate new confidence scores      │
                    │ • May get different results!          │
                    │ (Line 3597-3611)                      │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ CHECK: just_reset == True?            │
                    │ (Line 3617)                           │
                    │                                       │
                    │ YES → Reverify low-confidence fields  │
                    │ (< 0.80 confidence)                   │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ REVERIFICATION                        │
                    │                                       │
                    │ "You mentioned 'laptop'. Is that      │
                    │  the correct product?"                │
                    │                                       │
                    │ User can:                             │
                    │ • Confirm: "Yes" → confidence=0.95    │
                    │ • Correct: "No, it's a phone"         │
                    │ • Reject: "No" → ask for correct value│
                    │                                       │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ CONTINUE NORMAL FLOW                  │
                    │                                       │
                    │ • Check missing fields                │
                    │ • Ask for any remaining data          │
                    │ • Build verification summary          │
                    │                                       │
                    │ With FRESH PERSPECTIVE from soft reset
                    └───────────────────────────────────────┘
```

---

## DIAGRAM 5: LOCAL CORRECTION FLOW (During Verification)

```
                    ╔═══════════════════════════════════════╗
                    ║ VERIFICATION STAGE                    ║
                    ║ System shows summary                  ║
                    ║                                       ║
                    ║ Name: John Smith                      ║
                    ║ Email: john@email.com                 ║
                    ║ Phone: 555-123-4567                   ║
                    ║ Issue: Laptop arrived broken          ║
                    ║                                       ║
                    ║ "Is this correct?"                    ║
                    ╚═══════════════╤═════════════════════╝
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                │
                  YES              NO             PARTIAL
                   │           (correction       (some fields
                   │            needed)          need change)
                   │                │                │
                   ▼                ▼                ▼
            ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
            │ COMPLETION  │  │ IDENTIFY     │  │ IDENTIFY     │
            │ Process     │  │ WHICH FIELD  │  │ WHICH FIELDS │
            │ case        │  │ needs        │  │ need change  │
            └─────────────┘  │ correction   │  └──────────────┘
                             └──────┬───────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ DECISION ENGINE: decide(state, text)  │
                    │ (Line 3803-3806)                      │
                    │                                       │
                    │ Analyzes user response:               │
                    │ • "No, my email is john@work.com"     │
                    │ • Identifies field: "email"           │
                    │ • Returns: action="correct",          │
                    │   target_field="email"                │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────────┐
                    │ FIELD CORRECTION HANDLER              │
                    │ (Line 3814-3860)                      │
                    │                                       │
                    │ action == "correct"                   │
                    └───────────────┬───────────────────────┘
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ Step 1: EXTRACT NEW VALUE                                 │
    │ (Line 3825-3828)                                          │
    │                                                            │
    │ extracted = extract(                                      │
    │     text,                                                 │
    │     mode="field",                      ◄─ Extract specific field
    │     target_field="email",              ◄─ Know which field
    │     state=state                        ◄─ Full context
    │ )                                                          │
    │                                                            │
    │ RESULT: {email: "john@work.com"}                          │
    └───────────────┬───────────────────────────────────────────┘
                    │
    ┌───────────────┴───────────────────────────┐
    │                                           │
   YES                                         NO
 Value                                   Extraction
 found                                    failed
    │                                           │
    ▼                                           ▼
    ┌─────────────────────────────┐   ┌─────────────────────────┐
    │ Continue                    │   │ Ask again               │
    └─────────────────────────────┘   │                         │
             │                        │ "What's your email?"    │
             ▼                        └─────────────────────────┘
    ┌───────────────────────────────────────────────────────────┐
    │ Step 2: UPDATE CASE STATE                                 │
    │ (Line 3833-3837)                                          │
    │                                                            │
    │ state = update_case(                                      │
    │     state,                                                │
    │     extracted,                                            │
    │     mode="normal"              ◄─ Normal correction mode  │
    │ )                                                          │
    │                                                            │
    │ This will:                                                │
    │ • Update entity: entities["email"] = "john@work.com"      │
    │ • Increment correction_count += 1                         │
    │ • Set confidence for email field                          │
    │ • Check for correction drift                              │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ Step 3: BOOST CONFIDENCE                                  │
    │ (Line 3847)                                               │
    │                                                            │
    │ state.increase_confidence(0.02)                           │
    │ • Confidence += 0.02                                      │
    │ • Shows system trusts the correction                      │
    │ • Caps at 1.0 (100%)                                      │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ Step 4: RESET ATTEMPT COUNTERS                            │
    │ (Line 3849-3852)                                          │
    │                                                            │
    │ state.reset_attempts()                                    │
    │ • Clear attempts counter for this field                   │
    │ • Allows clean re-extraction if needed                    │
    │ • Prevents artificial "stuck" state                       │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ Step 5: CHECK FOR MORE CORRECTIONS                        │
    │ (Line 3859-3860)                                          │
    │                                                            │
    │ if state.missing_fields:                                  │
    │     return ask_missing()                                  │
    │ else:                                                      │
    │     return build_verification_response()  ◄─ Show summary │
    │                                                            │
    │ OPTIONS:                                                   │
    │ • More fields to collect → ask_missing()                  │
    │ • All done → build summary (goto verification)            │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ Step 6: CHECK CORRECTION DRIFT                            │
    │ (Automatic in apply_control)                              │
    │                                                            │
    │ During this flow, apply_control() checks:                 │
    │ • Same field corrected 3+ times?                          │
    │   → sentiment = "high"                                    │
    │ • Corrections > field count?                              │
    │   → sentiment = "high"                                    │
    │ • Multi-pass drift?                                       │
    │   → sentiment = "high"                                    │
    │                                                            │
    │ If triggered:                                              │
    │ → escalation_score >= 0.55                                │
    │ → SOFT RESET triggered again                              │
    └───────────────┬───────────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │ SHOW UPDATED SUMMARY (if no drift)                        │
    │                                                            │
    │ Name: John Smith                                          │
    │ Email: john@work.com        ◄─ CORRECTED                 │
    │ Phone: 555-123-4567                                       │
    │ Issue: Laptop arrived broken                              │
    │                                                            │
    │ "Is this correct now?"                                    │
    │                                                            │
    │ User can:                                                  │
    │ • "Yes" → COMPLETION                                      │
    │ • "No, X is still wrong" → Another correction             │
    └───────────────────────────────────────────────────────────┘
```

---

## CODE BLOCKS EXPLAINED

### Block 1: apply_control() - Main Decision Point

```python
def apply_control(self, state, text):
    """
    ═══════════════════════════════════════════════════════════
    PURPOSE: Decide if case needs CONTROL ACTION
    
    PARAMETERS:
    • state: CaseState (all conversation data)
    • text: str (user's latest message)
    
    RETURNS:
    • None (if no action needed)
    • {action: "handover"|"reset", reason: str}
    ═══════════════════════════════════════════════════════════
    """
    
    t = str(text or "").lower().strip()
    
    # ════════════════════════════════════════════════════════
    # CHECK 1: Explicit Human Request
    # ════════════════════════════════════════════════════════
    human_keywords = ["human", "agent", "representative", "real person"]
    if any(word in t for word in human_keywords):
        # User explicitly wants a human
        # No more automated responses
        return {"action": "handover", "reason": "user_requested_human"}
    
    # ════════════════════════════════════════════════════════
    # CHECK 2: Direct Attempts Threshold
    # ════════════════════════════════════════════════════════
    # CRITICAL: Prevents infinite loops on stuck fields
    if state.attempts > state.max_attempts:  # max_attempts = 3
        state.sentiment = "high"
        # Immediate transfer, don't calculate score
        return {"action": "handover", "reason": "max_attempts_exceeded"}
    
    # ════════════════════════════════════════════════════════
    # CHECKS 3-6: Detect Problem Patterns
    # ════════════════════════════════════════════════════════
    # All these set sentiment="high" which increases escalation score
    
    if self.u.detect_repetition_fatigue(state):
        state.sentiment = "high"  # User asked same field too many times
    
    is_field_drift, _ = state.detect_correction_drift()
    if is_field_drift:
        state.sentiment = "high"  # Same field corrected 3+ times
    
    is_multi_pass, _ = state.detect_multi_pass_drift()
    if is_multi_pass:
        state.sentiment = "high"  # All fields corrected, now correcting again
    
    exceeds_fields, _ = state.check_total_corrections_exceed_fields()
    if exceeds_fields:
        state.sentiment = "high"  # Corrections > field count
    
    # ════════════════════════════════════════════════════════
    # CHECK 7: Calculate Escalation Score
    # ════════════════════════════════════════════════════════
    escalation_score = self._calculate_escalation_score(state)
    
    # FORMULA: (attempts/3 * 0.4) + (corrections/5 * 0.3) + (sentiment * 0.3)
    # Returns: 0.0 to 1.0
    
    if escalation_score >= 0.75:
        # Critical: User very frustrated or many attempts
        return {"action": "handover", "reason": "escalation_score_critical"}
    
    if escalation_score >= 0.55 and not state.just_reset:
        # High: Not critical yet, but needs reset
        # just_reset check prevents immediate re-reset
        return {"action": "reset", "reason": "escalation_score_high"}
    
    # ════════════════════════════════════════════════════════
    # CHECK 8: Correction Loop Detection
    # ════════════════════════════════════════════════════════
    if (state.awaiting_correction and 
        state.attempts >= 2 and 
        not state.just_reset):
        # User stuck in correction loop
        # Tried 2+ times to correct something
        return {"action": "reset", "reason": "correction_loop"}
    
    # No action needed - continue normal flow
    return None
```

### Block 2: Escalation Score Calculation

```python
def _calculate_escalation_score(self, state):
    """
    ═══════════════════════════════════════════════════════════
    FORMULA: (A * 0.4) + (C * 0.3) + (S * 0.3)
    
    Where:
    A = attempts/max_attempts (normalized 0-1)
    C = corrections/max_corrections (normalized 0-1)
    S = sentiment_score (mapped 0.05-0.7)
    
    Result: 0.0 to 1.0
    ═══════════════════════════════════════════════════════════
    """
    
    # ────────────────────────────────────────────────────────
    # COMPONENT A: Attempt Effort (Weight: 40%)
    # ────────────────────────────────────────────────────────
    # How many times has system tried to extract field?
    attempt_score = min(1.0, state.attempts / state.max_attempts)
    #
    # Examples:
    # 0 attempts → 0.0 score
    # 1 attempt  → 0.33 score (1/3)
    # 2 attempts → 0.67 score (2/3)
    # 3+ attempts → 1.0 score (capped)
    #
    # Impact: Up to +0.4 on final score (1.0 * 0.4)
    
    # ────────────────────────────────────────────────────────
    # COMPONENT C: Correction Burden (Weight: 30%)
    # ────────────────────────────────────────────────────────
    # How many fields has user corrected?
    correction_score = min(
        1.0,
        state.correction_count / float(state.max_correction_count)
    )
    #
    # Examples (max=5):
    # 0 corrections → 0.0 score
    # 2 corrections → 0.4 score (2/5)
    # 5+ corrections → 1.0 score (capped)
    #
    # Impact: Up to +0.3 on final score (1.0 * 0.3)
    
    # ────────────────────────────────────────────────────────
    # COMPONENT S: Emotional State (Weight: 30%)
    # ────────────────────────────────────────────────────────
    # Is user frustrated, angry, confused?
    if state.sentiment == "high":
        sentiment_score = 0.7  # Clearly frustrated
    elif state.sentiment == "medium_high":
        sentiment_score = 0.4  # Somewhat frustrated
    elif state.sentiment is not None:
        sentiment_score = 0.1  # Neutral
    else:
        sentiment_score = 0.05  # No emotion detected
    #
    # Impact: Up to +0.21 on final score (0.7 * 0.3)
    
    # ────────────────────────────────────────────────────────
    # CALCULATE TOTAL SCORE
    # ────────────────────────────────────────────────────────
    total_score = (
        attempt_score * 0.4 +      # 40% weight on attempts
        correction_score * 0.3 +   # 30% weight on corrections
        sentiment_score * 0.3      # 30% weight on sentiment
    )
    
    return total_score
    #
    # EXAMPLES:
    #
    # Normal user, no problems:
    # • 0 attempts, 0 corrections, sentiment=None
    # • (0*0.4) + (0*0.3) + (0.05*0.3) = 0.015 ✓ NO ACTION
    #
    # Frustrated but low attempts:
    # • 1 attempt, 0 corrections, sentiment="high"
    # • (0.33*0.4) + (0*0.3) + (0.7*0.3) = 0.345 ✓ NO ACTION
    #
    # Multiple problems (SOFT RESET):
    # • 2 attempts, 2 corrections, sentiment="high"
    # • (0.67*0.4) + (0.4*0.3) + (0.7*0.3) = 0.57 ⚠️ RESET
    #
    # Critical (HANDOVER):
    # • 3 attempts, 5 corrections, sentiment="high"
    # • (1.0*0.4) + (1.0*0.3) + (0.7*0.3) = 1.0 🚨 HANDOVER
```

### Block 3: Soft Reset Implementation

```python
def soft_reset(self):
    """
    ═══════════════════════════════════════════════════════════
    NON-DESTRUCTIVE RESET
    
    Purpose: Give user fresh start without losing context
    
    CLEARS:
    • attempts counter (fresh field extraction)
    • correction counters (no penalty for previous corrections)
    • field attempt tracking (can ask fields again)
    
    PRESERVES:
    • all extracted entities (keep data collected so far)
    • confidence scores (know which fields were uncertain)
    • sentiment (keep emotional context)
    • language (keep detected language)
    ═══════════════════════════════════════════════════════════
    """
    
    # ────────────────────────────────────────────────────────
    # CLEAR EFFORT COUNTERS
    # ────────────────────────────────────────────────────────
    self.attempts = 0
    # Reset how many times system tried to extract fields
    # Allows fresh extractions without penalty
    
    self.field_attempts = {}
    # Clear per-field attempt tracking
    # Each field can be asked again fresh
    
    # ────────────────────────────────────────────────────────
    # CLEAR CORRECTION TRACKING
    # ────────────────────────────────────────────────────────
    self.correction_count = 0
    # Reset count of how many corrections user made
    # Doesn't penalize user for previous corrections
    
    self.correction_passes = 0
    # Reset number of correction passes
    # Tracks if all fields corrected + more corrections
    
    self.fields_corrected_in_pass = set()
    # Clear which fields corrected in current pass
    # Used for multi-pass drift detection
    
    # ────────────────────────────────────────────────────────
    # PRESERVE EXTRACTED DATA
    # ────────────────────────────────────────────────────────
    # DO NOT clear these - keep all user data!
    # self.entities (e.g., {"name": "John", "email": "..."})
    # self.entity_confidence (e.g., {"name": 0.95, "email": 0.8})
    # self.sentiment (e.g., "high")
    # self.language (e.g., "hindi")
    
    # ────────────────────────────────────────────────────────
    # SET FLAGS FOR REVERIFICATION
    # ────────────────────────────────────────────────────────
    self.just_reset = True
    # Flag: System just did soft reset
    # Triggers: Reverify low-confidence fields
    # Prevents: Immediate re-reset
    
    self.awaiting_new_issue = True
    # Flag: Ready to collect issue again
    # Triggers: Fresh extraction on next input
    
    self.awaiting_reverify_confirmation = False
    # Flag: Clear verification state
    # Ensures fresh reverification flow
    
    self.last_corrected_field = None
    # Clear which field was last corrected
    
    self.reverify_attempts = 0
    # Clear reverification attempts
    # Allows fresh reverification
    
    return
    
    # ════════════════════════════════════════════════════════
    # WHAT HAPPENS NEXT (in main flow):
    # ════════════════════════════════════════════════════════
    # 1. System: "Let me start fresh. Can you explain again?"
    # 2. User: Re-explains issue
    # 3. System: extract_full() - fresh extraction
    # 4. Check: if just_reset == True:
    #    → Reverify low-confidence fields (< 0.80)
    #    → Ask: "You mentioned X, is that correct?"
    # 5. Continue: normal flow (missing fields, verification)
```

### Block 4: Field Correction Logic

```python
if action == "fill_field":
    """
    ═══════════════════════════════════════════════════════════
    CORRECTION DURING VERIFICATION
    
    PARAMETERS:
    • action: "fill_field" from decision engine
    • target_field: Which field needs correction
    • text: User's response with new value
    • state.last_asked_field: Which field we're working on
    
    PROCESS:
    1. Extract new value from user input
    2. Validate extracted value
    3. Update case with new value
    4. Track correction count
    5. Check for correction drift
    6. Decide next step
    ═══════════════════════════════════════════════════════════
    """
    
    target_field = state.last_asked_field
    # Which field user is correcting (e.g., "email")
    
    # ────────────────────────────────────────────────────────
    # STEP 1: EXTRACT NEW FIELD VALUE
    # ────────────────────────────────────────────────────────
    extracted = self.u.extract(
        text,                           # User said "john@work.com"
        mode="field",                   # Field-specific extraction
        target_field=target_field,      # We know it's "email"
        state=state                     # Full conversation context
    )
    #
    # Returns: {email: "john@work.com"} or {} if failed
    
    if not extracted:
        # Extraction failed (unclear input)
        return (state, self.i.ask_missing(state))
        # Ask field again or ask for clarification
    
    # ────────────────────────────────────────────────────────
    # STEP 2: RESET ATTEMPT COUNTERS
    # ────────────────────────────────────────────────────────
    state.reset_attempts()
    # Clear attempts on this field
    # Successful extraction = fresh start for this field
    
    state.reset_field_attempt(target_field)
    # Remove this field from field_attempts tracking
    # Prevents "stuck field" logic from triggering
    
    # ────────────────────────────────────────────────────────
    # STEP 3: UPDATE CASE WITH NEW VALUE
    # ────────────────────────────────────────────────────────
    state = self.c.update_case(
        state,
        extracted,
        mode="normal"                   # Normal correction mode
    )
    #
    # This will:
    # • Update: entities["email"] = "john@work.com"
    # • Increment: correction_count += 1
    # • Set: entity_confidence["email"] = (some score)
    # • Check: Correction drift detection
    #
    # mode="normal" means:
    # • Process corrections normally
    # • Count towards correction_count
    # • May trigger drift detection
    
    # ────────────────────────────────────────────────────────
    # STEP 4: BOOST CONFIDENCE ON SUCCESS
    # ────────────────────────────────────────────────────────
    state.increase_confidence(0.02)
    # Confidence += 0.02 (capped at 1.0)
    # Shows: System trusts this successful extraction
    
    # ────────────────────────────────────────────────────────
    # STEP 5: CHECK FOR MORE FIELDS
    # ────────────────────────────────────────────────────────
    if state.missing_fields:
        # More fields to collect
        return (state, self.i.ask_missing(state))
        # Ask for next missing field
    
    # All fields collected
    return (state, self.build_verification_response(state))
    # Build and show updated summary
    # User can confirm or make more corrections
    
    # ════════════════════════════════════════════════════════
    # AUTOMATIC DRIFT DETECTION (in apply_control)
    # ════════════════════════════════════════════════════════
    # During this flow, apply_control() will check:
    # • Same field corrected 3+ times? → sentiment="high"
    # • All fields corrected, more corrections? → sentiment="high"
    # • Corrections > field count? → sentiment="high"
    #
    # If any detected:
    # • escalation_score increases
    # • If score >= 0.55 → SOFT RESET
    # • If score >= 0.75 → HANDOVER
```

### Block 5: Reverification After Reset

```python
if state.last_action == "reverify_low_confidence":
    """
    ═══════════════════════════════════════════════════════════
    REVERIFY LOW-CONFIDENCE FIELDS AFTER SOFT RESET
    
    PARAMETERS:
    • state.last_action: "reverify_low_confidence"
    • state.current_field: Which field we're reverifying
    • state.entity_confidence[field]: Confidence score (< 0.80)
    • text: User's response to "Is [field] = [value] correct?"
    • state.just_reset: True (we're in reverification phase)
    
    FLOW:
    User responses:
    1. "Yes" → Accept value, move to next field
    2. "No" → Ask for correct value
    3. "No, it's X" → Apply correction, move on
    4. "Umm..." → Treat as rejection, ask for value
    ═══════════════════════════════════════════════════════════
    """
    
    target_field = state.current_field
    # Which field we're verifying (e.g., "product")
    
    t_norm = self.d.normalize(text)
    # Normalize user response for comparison
    
    # ────────────────────────────────────────────────────────
    # CASE 1: USER CONFIRMS THE VALUE
    # ────────────────────────────────────────────────────────
    if self.d.is_pure_yes(t_norm):
        # User said "yes" or "correct" or "uh-huh"
        state.entity_confidence[target_field] = 0.95
        # Boost confidence to high (0.95)
        # User confirmed = reliable field
        
        state.awaiting_reverify_confirmation = False
        state.reverify_attempts = 0
        state.last_action = None
        # Clear reverification state, move on
    
    # ────────────────────────────────────────────────────────
    # CASE 2: USER PROVIDES EXPLICIT CORRECTION
    # ────────────────────────────────────────────────────────
    elif self.d.detect_explicit_correction(t_norm):
        # User said "No, it's X" or "Change to X"
        # System can extract correct value from response
        
        extracted = self.u.extract(
            text,
            mode="field",
            target_field=target_field,
            state=state
        )
        
        if extracted:
            # Correction value extracted successfully
            self.c.update_case(
                state,
                extracted,
                mode="reverify"             # Don't inflate correction count
            )
            # mode="reverify" means:
            # • Update entity value
            # • Don't count towards correction_count
            # • Avoids penalizing for reverification corrections
            
            state.entity_confidence[target_field] = 0.95
            # Boost confidence to high
            # User explicitly provided = very reliable
            
            state.awaiting_reverify_confirmation = False
            state.reverify_attempts = 0
            state.last_action = None
            # Clear state, move on
        else:
            # Extraction failed (unclear correction value)
            return (state, self.i.ask_reverify_correction(state))
            # Ask: "What's the correct value?"
    
    # ────────────────────────────────────────────────────────
    # CASE 3: USER REJECTS (without providing correction)
    # ────────────────────────────────────────────────────────
    elif self.d.is_pure_rejection(t_norm):
        # User said "No" or "That's wrong"
        # But didn't provide correct value
        return (state, self.i.ask_reverify_correction(state))
        # Ask: "What's the correct value?"
    
    # ────────────────────────────────────────────────────────
    # CASE 4: VAGUE/UNCERTAIN RESPONSE
    # ────────────────────────────────────────────────────────
    else:
        # User said "Umm..." or "Maybe?" or "Not sure"
        # Treat as rejection
        return (state, self.i.ask_reverify_correction(state))
        # Ask for clarification/correct value
    
    # ────────────────────────────────────────────────────────
    # CONTINUE TO NEXT LOW-CONFIDENCE FIELD
    # ────────────────────────────────────────────────────────
    reverify_response = self.i.ask_reverify_low_confidence(state)
    # Check if there are more low-confidence fields
    # (confidence < 0.80)
    
    if reverify_response:
        # Another low-confidence field found
        return (state, reverify_response)
        # Ask: "Is [next_field] = [value] correct?"
    
    # ────────────────────────────────────────────────────────
    # NO MORE LOW-CONFIDENCE FIELDS
    # ────────────────────────────────────────────────────────
    state.just_reset = False
    # Clear the reset flag, reverification done
    
    # Continue with normal collection flow
    if state.missing_fields:
        return (state, self.i.ask_missing(state))
        # Ask for any remaining missing fields
    
    return (state, self.build_verification_response(state))
    # All fields done, show final summary
```

---

## PARAMETER REFERENCE TABLE

```
╔════════════════════════════════════════════════════════════════════════════╗
║ PARAMETER                    │ TYPE      │ DEFAULT │ USED IN              ║
╠════════════════════════════════════════════════════════════════════════════╣
║ state.attempts               │ int       │ 0       │ Escalation score     ║
║ state.max_attempts           │ int       │ 3       │ Direct check, scaling║
║ state.correction_count       │ int       │ 0       │ Escalation score     ║
║ state.max_correction_count   │ int       │ 5       │ Scaling              ║
║ state.sentiment              │ str/None  │ None    │ Escalation score     ║
║ state.entity_confidence      │ dict      │ {}      │ Reverification       ║
║ state.just_reset             │ bool      │ False   │ Reset/reverify flag  ║
║ state.awaiting_correction    │ bool      │ False   │ Correction loop      ║
║ state.awaiting_new_issue     │ bool      │ False   │ Reset flow           ║
║ state.last_action            │ str/None  │ None    │ Flow control         ║
║ state.current_field          │ str/None  │ None    │ Field tracking       ║
║ state.entities               │ dict      │ {}      │ Data storage         ║
║ state.missing_fields         │ list      │ []      │ Collection logic     ║
║ state.language               │ str/None  │ None    │ Response generation  ║
║ state.sentiment              │ str/None  │ None    │ Escalation           ║
║ state.field_attempts         │ dict      │ {}      │ Per-field tracking   ║
║ state.max_field_attempts     │ int       │ 3       │ Field limit          ║
║ state.reverify_attempts      │ int       │ 0       │ Reverif limit        ║
║ state.max_reverify_attempts  │ int       │ 2       │ Reverif limit        ║
╚════════════════════════════════════════════════════════════════════════════╝

THRESHOLDS:
• Attempts threshold: > 3 = HANDOVER
• Escalation score soft reset: >= 0.55
• Escalation score handover: >= 0.75
• Confidence reverify: < 0.80
• Confidence boost on success: += 0.02
• Confidence boost on confirm: = 0.95
• Field correction limit: 3 times = increment drift
```

