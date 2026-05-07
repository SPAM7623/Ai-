# BUG REPORT - System Test Analysis

## Test Run Findings:
- **Attempts**: 22 (Very High)
- **Confidence**: 0.7999... (Stuck at threshold)
- **Sentiment**: "medium" (Should be "high")
- **Correction Count**: 1 (Too low for 22 attempts)
- **Requires Human**: False ❌ (Should be True)
- **Conversation Turns**: 46 (Excessive)

---

## BUG #1: ESCALATION SCORE NOT TRIGGERING (CRITICAL)

**Problem**: With 22 attempts, escalation should fire but doesn't

**Root Cause**: 
```python
# In _calculate_escalation_score():
attempt_score = min(1.0, 22 / 3) = 1.0
sentiment_score = 0.05  # "medium" = 0.05, not "high" = 0.7

# Calculation:
total = (1.0 * 0.4) + (1/4 * 0.3) + (0.05 * 0.3)
      = 0.4 + 0.075 + 0.015
      = 0.49  ← Below 0.55 threshold!
```

**Impact**: User needs 0.75 escalation OR high sentiment to trigger handover
- With 22 attempts + low sentiment = NO ESCALATION

**Fix Needed**: Escalation should trigger automatically when attempts > max_attempts, regardless of sentiment

---

## BUG #2: SENTIMENT NOT DETECTED (CRITICAL)

**Problem**: Text "its annoying u are not able to understand" stays as "medium" sentiment

**Root Cause**: 
- Keywords "annoying", "frustrated" aren't detected as frustration
- System only has basic frustration phrase list
- Text needs explicit phrase match (case sensitive or exact match)

**Impact**: 
- Escalation score stuck at 0.49
- User frustration invisible to system
- No handover triggered

**Fix Needed**: Improve frustration keyword detection to catch "annoying", "frustrated", etc.

---

## BUG #3: CONFIDENCE NOT INCREASING (CRITICAL)

**Problem**: Confidence stuck at 0.7999... despite successful field inputs

**Root Cause**:
- `increase_confidence()` IS called in normal update mode (line 1831)
- But confidence stays same
- Possible issues:
  1. `increase_confidence()` not working correctly
  2. Confidence being reset/overwritten after increase
  3. Updates going through "reverify" mode (which doesn't increase confidence)
  4. Logic issue in confidence calculation

**Check needed**: 
```python
def increase_confidence(self, amount=0.05):
    self.confidence = min(1.0, self.confidence + amount)
    # If confidence starts at 0.85 and adds 0.05, should be 0.90
    # But it's staying at 0.80 - means increase_confidence NOT being called
    # OR confidence is being reset somewhere
```

**Fix Needed**: Trace where confidence is being reset/overwritten

---

## BUG #4: DOUBLE "EXPLAIN FROM BEGINNING" (MEDIUM)

**Problem**: After soft reset, system asks user to explain twice

**Root Cause**: 
- `ask_rephrase()` called → sets stage="restart" and asks to explain
- User responds → system processes input
- Flow is unclear what happens next - might call ask_rephrase again OR ask_missing

**Flow Issue**:
```
User clarifies issue
       ↓
Should go to: Low-confidence reverification
But might go to: ask_rephrase() again (duplicate)
       ↓
Result: User asked twice
```

**Fix Needed**: Check if `just_reset` flag is being cleared properly after first reverification pass

---

## BUG #5: FIELD CORRECTION NOT DETECTING "ITS HOUSE" (MEDIUM)

**Problem**: User says "it's house" but system doesn't apply correction

**Root Cause**: 
- Field correction detection uses pattern matching or exact value matching
- Text "it's house" might not be extracted properly
- System might be looking for field hints like "the [field_name] is wrong"
- Simple statement "it's house" doesn't match correction patterns

**Example**:
```
User says: "its house its annoying u are not able to understand"
System should detect: "it's house" = field correction
But current detection needs explicit pattern like:
  - "house is wrong"
  - "change to house"
  - "the [field] should be house"

Simple "it's house" falls into "vague response" category
```

**Fix Needed**: Improve context-aware field value detection

---

## BUG #6: ATTEMPTS INCREMENTING BUT NOT TRIGGERING THRESHOLD (MAJOR)

**Problem**: 22 attempts logged but no automatic escalation

**Root Cause**: 
- Attempts increment on field failures ✓
- But escalation check only happens in `apply_control()`
- `apply_control()` only checks:
  1. Explicit human requests
  2. Repetition fatigue
  3. Correction drift
  4. Escalation score
  5. Correction loop (only if awaiting_correction)

**Missing Check**:
```python
# Should have:
if state.attempts > state.max_attempts:
    return {
        "action": "handover",
        "reason": "max_attempts_exceeded"
    }

# Currently missing - no direct check!
```

**Impact**: Users can get stuck asking same field 22+ times without escalation

**Fix Needed**: Add explicit max_attempts check in apply_control()

---

## Summary Table

| Bug # | Issue | Severity | Root Cause | Impact |
|-------|-------|----------|-----------|--------|
| 1 | Escalation score math | 🔴 Critical | Sentiment requirement too high | No handover at 22 attempts |
| 2 | Sentiment detection | 🔴 Critical | Missing keyword patterns | Can't detect user frustration |
| 3 | Confidence stuck | 🔴 Critical | Unknown overwrite/reset | Can't track field reliability |
| 4 | Double explain | 🟡 Major | Flow confusion after reset | Poor UX, repetitive |
| 5 | Field correction | 🟡 Major | Pattern matching too strict | Can't detect simple corrections |
| 6 | No attempts threshold | 🟡 Major | Missing explicit check | Infinite loop risk |

---

## Recommended Fixes (in order of priority):

1. **Add explicit attempts check in apply_control()**
   ```python
   if state.attempts > state.max_attempts:
       state.sentiment = "high"
       return {"action": "handover", "reason": "max_attempts"}
   ```

2. **Improve sentiment detection for "annoying", "frustrated"**
   - Add to frustration_phrases in UnderstandingAgent
   - Make pattern matching case-insensitive

3. **Trace confidence reset issue**
   - Check if update_case() is being called with wrong mode
   - Verify increase_confidence() is actually being invoked

4. **Fix double explain issue**
   - Ensure just_reset is cleared after first reverification
   - Clear stage="restart" when moving to normal collection flow

5. **Improve field correction detection**
   - Add context-aware extraction
   - Detect simple value statements like "it's [value]"

6. **Add safety limit checks**
   - Prevent same field being asked > 5 times
   - Auto-escalate if pattern detected

