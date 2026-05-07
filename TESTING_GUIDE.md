# Complete Testing Guide

## Quick Start

### Option 1: Interactive Test Menu (RECOMMENDED)
```bash
python run_interactive_test.py
```
- Browse all 8 scenarios
- See detailed conversation scripts
- Copy-paste messages for manual testing

### Option 2: View All Scenarios
```bash
python test_all_scenarios.py
```
- Shows structured test cases
- Lists all assertions
- Displays parameter checks

### Option 3: Legacy Scenario File
```bash
python TEST_LOST_PHONE_SCENARIO.py
```
- Original comprehensive documentation
- Detailed flow diagrams
- Real-world examples

---

## Testing Workflow

### Step 1: Prepare Your Environment
```bash
# Terminal 1: Start your chatbot
export DEBUG=True
python final_2.py

# Terminal 2: Open testing guide
python run_interactive_test.py
```

### Step 2: Select a Scenario
Pick any of the 8 scenarios from the interactive menu:
- 1: Normal Flow
- 2: Soft Reset (Frustration)
- 3: Correction Loop (Drift)
- 4: Attempts Exceeded
- 5: Explicit Human Request
- 6: Escalation Score Critical
- 7: "I Don't Know" Handling
- 8: Low-Confidence Reverification

### Step 3: Copy-Paste User Messages
For each TURN in the scenario:
1. Copy the USER message from testing guide
2. Paste it into Terminal 1 (your chatbot)
3. Press ENTER

### Step 4: Verify Response
Compare what the bot says with expected response:
- ✅ Exact match = PASS
- ⚠️ Similar but worded differently = PASS
- ❌ Completely different = FAIL

### Step 5: Monitor Debug Output
Watch Terminal 1 for:
```
STATE: attempts=X, sentiment='Y', corrections=Z
DEBUG_SIGNALS: {
  'attempts': ...,
  'correction_count': ...,
  'sentiment': ...,
  'escalation_score': ...,
  'just_reset': ...
}
```

---

## Detailed Scenario Guide

### SCENARIO 1: Normal Flow (No Issues)
**What to Test**: Basic conversation without problems
**Expected**: Smooth progression from collection to completion
**Turns**: 5
**Time**: ~2 minutes

```
Turn 1: "I lost my phone yesterday at the airport"
Turn 2: "John Smith"
Turn 3: "john.smith@email.com"
Turn 4: "555-123-4567"
Turn 5: "Yes, that's all correct"
```

**Verify**:
- ✓ No repeated questions
- ✓ sentiment stays None/low
- ✓ attempts = 0 throughout
- ✓ Direct flow to completion

---

### SCENARIO 2: Soft Reset (Frustration)
**What to Test**: System detects frustration and triggers soft reset
**Expected**: After user gets frustrated, system says "Let me start fresh"
**Turns**: 9
**Time**: ~3 minutes

```
Turn 1: "I lost my phone...and I'm really frustrated with this process!"
Turn 2: "John Smith"
Turn 3: "john@email.com"
Turn 4: "Ugh! Why are you asking so many questions? This is annoying! It's 555-123-4567"
Turn 5: "Actually, wait...I don't understand why this is so complicated!"
Turn 6: "No! The phone is wrong...this whole thing is ridiculous!"
    ↓ SOFT RESET SHOULD TRIGGER HERE
Turn 7: "OK fine. I lost my phone...My phone is 555-321-4567"
Turn 8: "Yes, that's correct"
Turn 9: "Yes, all correct"
```

**Critical Check**:
Turn 6 should trigger soft reset message like:
"I sincerely apologize...Let me start completely fresh"

**Verify**:
- ✓ Frustration keywords detected (frustrated, annoying, ridiculous)
- ✓ sentiment = "high" 
- ✓ After Turn 6: just_reset = True
- ✓ Turn 7: asks "Is 555-321-4567 correct?" (reverification)
- ✓ attempts reset to 0 after soft_reset()

---

### SCENARIO 3: Correction Loop (Drift Detection)
**What to Test**: Same field corrected multiple times triggers reset
**Expected**: After 3 corrections on same field, system says "Let me start fresh"
**Turns**: 11
**Time**: ~3 minutes

```
Turn 1-4: Normal collection with phone=555-555-1234

Turn 5: "No, wait. The phone is wrong. It's 555-555-5678"
        → CORRECTION 1 on phone field

Turn 6: "Actually no, the phone is still wrong. It's 555-555-9999"
        → CORRECTION 2 on phone field (same field)

Turn 7: "Hmm, the email is also wrong. It's james@personal.com"
        → CORRECTION 3 on email field (different field)

Turn 8: "Wait, the phone is STILL not right. It's 555-555-4321"
        → CORRECTION 4 on phone field (3rd correction on phone!)
        ↓ DRIFT DETECTED - SOFT RESET TRIGGERS

Turn 9-11: Fresh extraction + reverification
```

**Critical Check**:
Turn 8 should trigger: "I see we're having trouble. Let me start fresh."

**Verify**:
- ✓ correction_count increments: 1 → 2 → 3 → 4
- ✓ detect_correction_drift() returns True at Turn 8
- ✓ sentiment = "high" is set
- ✓ soft_reset() is called
- ✓ After reset: attempts = 0, corrections = 0

---

### SCENARIO 4: Attempts Exceeded
**What to Test**: Failed extraction attempts trigger direct handover
**Expected**: After 4 failed phone entries, system transfers to human
**Turns**: 8
**Time**: ~2 minutes

```
Turn 1-3: Name and email collected successfully

Turn 4: "Umm... it's like... 555... maybe 555-something?"
        → ATTEMPT 1 FAILED (unclear)

Turn 5: "I'm not sure. It might be 555-123-4567 or 555-123-5678"
        → ATTEMPT 2 FAILED (ambiguous)

Turn 6: "No, I don't have anything. I don't know it"
        → ATTEMPT 3 FAILED (no data)

Turn 7: "I don't know that either"
        → ATTEMPT 4 FAILED
        ↓ CHECK: attempts > 3 (4 > 3) = TRUE
        ↓ IMMEDIATE HANDOVER
```

**Critical Check**:
Turn 7 should trigger: "Let me connect you to an agent right away"

**Verify**:
- ✓ attempts increments each failed turn: 1 → 2 → 3 → 4
- ✓ At Turn 7: apply_control() returns handover immediately
- ✓ NO escalation score calculation needed
- ✓ Pipeline stops (no more collection questions)

---

### SCENARIO 5: Explicit Human Request
**What to Test**: Keywords like "real person" trigger immediate handover
**Expected**: Handover WITHOUT further processing
**Turns**: 2
**Time**: ~30 seconds

```
Turn 1: "I lost my phone and I want to talk to a real person, not a chatbot"
        → KEYWORDS: "real person" detected
        ↓ IMMEDIATE HANDOVER

Turn 2: "Thanks"
        → [TRANSFERRED TO HUMAN AGENT]
```

**Critical Check**:
Turn 1 should trigger: "Of course, let me connect you..."

**Verify**:
- ✓ apply_control() checks human keywords FIRST
- ✓ NO other processing happens
- ✓ Handover happens before Turn 2
- ✓ reason = "user_requested_human"

---

### SCENARIO 6: Escalation Score Critical (0.75+)
**What to Test**: Multiple factors combine to push score >= 0.75
**Expected**: After many corrections + high sentiment, system transfers
**Turns**: 12
**Time**: ~4 minutes

```
Turn 1: "I lost my phone...this is absolutely ridiculous!"
        → sentiment = "high"

Turn 2-4: Collect name, email, phone

Turn 5-10: Multiple corrections on different fields
        → correction_count increases: 1 → 2 → 3 → 4 → 5
        → sentiment stays "high"
        → escalation_score keeps building

Turn 11-12: Score reaches 0.75, HANDOVER triggered
```

**Score Calculation**:
```
Score = (attempts/3 * 0.4) + (corrections/5 * 0.3) + (sentiment * 0.3)

Example at Turn 10:
- attempts = 0 (no failed extractions)
- corrections = 5
- sentiment = "high"

score = (0/3*0.4) + (5/5*0.3) + (0.7*0.3)
      = 0 + 0.3 + 0.21
      = 0.51 (not yet critical)

But with multi_pass_drift or other factors detected,
sentiment might be weighted differently or additional
checks trigger handover.
```

**Verify**:
- ✓ Debug output shows escalation_score calculation
- ✓ sentiment = "high" throughout
- ✓ corrections increment with each correction
- ✓ At some point, score >= 0.75 triggers handover

---

### SCENARIO 7: "I Don't Know" Handling
**What to Test**: User can't provide value, recorded as "unknown"
**Expected**: Field set to "unknown", case proceeds
**Turns**: 6
**Time**: ~2 minutes

```
Turn 1: "I lost my phone at the mall yesterday"
        → Extract intent

Turn 2: "Rachel Martinez"
        → Extract name

Turn 3: "rachel@email.com"
        → Extract email

Turn 4: "I don't know my phone number off the top of my head"
        → DETECT: "I don't know" phrase
        → RESULT: phone = "unknown" (VALID extraction)
        → NOTE: attempts NOT incremented

Turn 5-6: Verification with unknown field
```

**Critical Check**:
Turn 4 should NOT ask "Can you provide your phone number?" again
Instead, should move to verification with phone = "unknown"

**Verify**:
- ✓ Phrase detected: "I don't know"
- ✓ Field value: phone = "unknown"
- ✓ attempts = 0 (not a failure)
- ✓ missing_fields doesn't include phone (has a value)
- ✓ Summary shows phone: "unknown"

---

### SCENARIO 8: Low-Confidence Reverification
**What to Test**: Fields with confidence < 0.80 are reverified after reset
**Expected**: After reset, system asks to confirm uncertain fields
**Turns**: 8
**Time**: ~3 minutes

```
Turn 1: "I lost my phone...555 or maybe 666? I'm not sure"
        → Extract phone with LOW confidence (< 0.80)
        → Confidence: ~0.65

Turn 2: "David Lee"
        → Extract name

Turn 3: "david@email.com"
        → Extract email

Turn 4: "I'm confused. Can we start over?"
        → Trigger soft reset
        → Reason: Low confidence + confusion

Turn 5: "I lost my phone...My number starts with 555"
        → Fresh extraction
        → just_reset = True
        ↓ REVERIFICATION OF LOW-CONFIDENCE FIELDS

Turn 6: "I believe it's 555-666-7777"
        → User provides explicit value during reverification
        → Confidence boosted to 0.95

Turn 7-8: Confirmation
```

**Critical Check**:
Turn 5 should ask: "Is 555-XXX-XXXX correct?" (reverifying low-conf phone)

**Verify**:
- ✓ Initial confidence < 0.80
- ✓ Soft reset triggered
- ✓ After reset: ask_reverify_low_confidence() called
- ✓ User confirmation → confidence = 0.95
- ✓ just_reset cleared after reverification done

---

## Debugging Checklist

### For Each Scenario, Verify:

#### ✅ Response Content
- [ ] Bot response matches expected (exact or similar)
- [ ] No unexpected error messages
- [ ] Proper punctuation and formatting

#### ✅ State Variables
- [ ] attempts: Correct value for scenario
- [ ] correction_count: Tracks user corrections
- [ ] sentiment: Matches detected emotion
- [ ] escalation_score: Proper calculation
- [ ] just_reset: Set/cleared at right times
- [ ] entity_confidence: Tracks field reliability

#### ✅ Control Flow
- [ ] apply_control() checks happen in order
- [ ] Correct action returned (handover, reset, None)
- [ ] soft_reset() clears right fields
- [ ] Reverification happens when needed
- [ ] Pipeline stage progression correct

#### ✅ Edge Cases
- [ ] "Unknown" values handled correctly
- [ ] Low-confidence reverification works
- [ ] Drift detection triggers properly
- [ ] Score calculation accurate
- [ ] Keywords detected correctly

---

## Expected Debug Output Format

```
STATE: attempts=2, sentiment='high', corrections=3
DEBUG_SIGNALS: {
  'attempts': 2,
  'correction_count': 3,
  'last_corrected_field': 'phone',
  'awaiting_correction': False,
  'just_reset': False,
  'sentiment': 'high',
  'escalation_score': 0.57
}

apply_control() analysis:
  ✓ Check 1: Human request? No
  ✓ Check 2: Attempts > 3? No
  ✓ Check 3: Repetition fatigue? No
  ✓ Check 4: Field drift? Yes → sentiment='high'
  ✓ Check 5: Multi-pass drift? No
  ✓ Check 6: Corrections > fields? No
  ✓ Check 7: Score >= 0.75? No
           Score >= 0.55? Yes!
  └─ Action: SOFT RESET

Returning: {action: 'reset', reason: 'escalation_score_high'}
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Soft reset doesn't trigger" | Check sentiment detection - must be "high" |
| "Attempts not incrementing" | Verify extraction is actually failing |
| "Drift not detected" | Check if same field corrected 3+ times |
| "Score not calculating" | Verify all components (A, C, S) in formula |
| "Reverification not asked" | Check if just_reset=True and confidence < 0.80 |
| "Handover doesn't happen" | Check if score >= 0.75 or attempts > 3 |

---

## Quick Test Summary

| Scenario | Expected Outcome | Key Parameters |
|----------|------------------|-----------------|
| 1. Normal | Completion | attempts=0, corrections=0 |
| 2. Frustration | Soft reset | sentiment="high", score>=0.55 |
| 3. Drift | Soft reset | same field 3x corrected |
| 4. Attempts | Handover | attempts > 3 |
| 5. Human Request | Handover | keywords detected |
| 6. Score Critical | Handover | score >= 0.75 |
| 7. Don't Know | Completion | field="unknown" |
| 8. Low Confidence | Reverification | confidence < 0.80 |

---

## Questions?

See:
- `AGENT_FLOW_DIAGRAM.md` - Complete architecture
- `VISUAL_FLOW_DIAGRAMS.md` - Flow diagrams & code
- `TEST_LOST_PHONE_SCENARIO.py` - Original test data
