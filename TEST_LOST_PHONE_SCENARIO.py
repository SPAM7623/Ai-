#!/usr/bin/env python3
"""
TEST SCRIPT: Lost Phone Complaint
Demonstrates all agent flows: collection, verification, correction, reset, handover
"""

# ═══════════════════════════════════════════════════════════════════════════
# TEST SCENARIO: LOST PHONE
# ═══════════════════════════════════════════════════════════════════════════

TEST_CONVERSATIONS = [

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 1: NORMAL FLOW (No Issues)
    # Expected: Collection → Verification → Completion
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 1: Normal Flow (No Problems)",
        "description": "User reports lost phone smoothly, no frustration or corrections",
        "expected_flow": ["collection", "verification", "completed"],
        "parameters": {
            "attempts": "Should stay 0",
            "sentiment": "Should be None or 'low'",
            "escalation_score": "Should stay < 0.55",
            "corrections": "Should be 0"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone yesterday at the airport",
                "system_action": "Initial extraction (full mode)",
                "check": "Detect intent='complaint', issue='lost_phone', sentiment=None",
                "expected_response": "I'm sorry to hear that. Let me help you. What is your name?"
            },
            {
                "turn": 2,
                "user": "John Smith",
                "system_action": "Field extraction for 'name'",
                "check": "name extracted with confidence=0.95",
                "expected_response": "Thank you, John. What's your email address?"
            },
            {
                "turn": 3,
                "user": "john.smith@email.com",
                "system_action": "Field extraction for 'email'",
                "check": "email extracted, no failed attempts",
                "expected_response": "And your phone number?"
            },
            {
                "turn": 4,
                "user": "555-123-4567",
                "system_action": "Field extraction for 'phone'",
                "check": "phone extracted, all required fields collected",
                "expected_response": "Let me confirm your details... [SUMMARY] Is this correct?"
            },
            {
                "turn": 5,
                "user": "Yes, that's all correct",
                "system_action": "Verification confirmation",
                "check": "sentiment=None, escalation_score=0.015",
                "expected_response": "Your case has been recorded. Case Reference: LOST-2024-001"
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 2: SOFT RESET (User Frustration)
    # Expected: Collection → Frustration detected → Soft Reset → Reverification → Completion
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 2: Soft Reset (Frustration Triggers Reset)",
        "description": "User gets frustrated during collection, system detects and triggers soft reset",
        "expected_flow": ["collection", "soft_reset", "reverification", "verification", "completed"],
        "parameters": {
            "attempts": "0 before reset, then 0 again after",
            "sentiment": "Changes to 'high' when frustration detected",
            "escalation_score": "Jumps to 0.55+, triggers reset",
            "just_reset": "Set to True after reset"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport yesterday and I'm really frustrated with this process!",
                "system_action": "Full extraction",
                "check": "Detect frustration keywords: 'frustrated', 'process'",
                "expected_response": "I understand your frustration. Let me help. What is your name?"
            },
            {
                "turn": 2,
                "user": "John Smith",
                "system_action": "Extract name",
                "check": "name=John Smith, confidence=0.95",
                "expected_response": "What's your email address?"
            },
            {
                "turn": 3,
                "user": "john@email.com",
                "system_action": "Extract email",
                "check": "email extracted, no issues yet",
                "expected_response": "And your phone number?"
            },
            {
                "turn": 4,
                "user": "Ugh! Why are you asking so many questions? This is annoying! It's 555-123-4567",
                "system_action": "Detect frustration, calculate escalation score",
                "check": "detect_frustration() → 'annoying' keyword → sentiment='high'",
                "check_detail": "escalation_score = (0*0.4) + (0*0.3) + (0.7*0.3) = 0.21 (still low, continue)",
                "expected_response": "I apologize for the frustration. Let me confirm what I have..."
            },
            {
                "turn": 5,
                "user": "Actually, wait. I can't remember if that's the right number. I don't understand why this is so complicated!",
                "system_action": "Detect multiple frustration signals",
                "check": "Can't understand + annoying detected again → sentiment stays 'high'",
                "check_detail": "attempts=0, sentiment='high' → escalation_score ≈ 0.35 (still below 0.55)",
                "expected_response": "I understand. Let me verify... Name: John Smith, Email: john@email.com, Phone: 555-123-4567. Is this correct?"
            },
            {
                "turn": 6,
                "user": "No! The phone is wrong and honestly this whole thing is ridiculous!",
                "system_action": "Frustration 'ridiculous' detected + correction needed",
                "check": "sentiment='high' PLUS correction request → escalation_score calculation",
                "check_detail": "attempts=1 (failed phone), sentiment='high' → (0.33*0.4) + (0*0.3) + (0.7*0.3) = 0.342 (still < 0.55)",
                "expected_response": "I sincerely apologize for the frustration. Let me start completely fresh and make this easier."
            },
            {
                "turn": 7,
                "user": "OK fine. I lost my phone at the airport. My phone number is actually 555-321-4567",
                "system_action": "SOFT RESET TRIGGERED + Fresh extraction",
                "check": "just_reset=True, soft_reset() called",
                "check_detail": "Clears: attempts=0, corrections=0 | Preserves: sentiment, entities",
                "expected_response": "Let me verify the phone number. You mentioned 555-321-4567. Is that correct?"
            },
            {
                "turn": 8,
                "user": "Yes, that's correct",
                "system_action": "Reverification confirmation",
                "check": "entity_confidence['phone'] = 0.95, just_reset=False",
                "expected_response": "Perfect. Let me confirm everything: Name: John Smith, Email: john@email.com, Phone: 555-321-4567. Correct?"
            },
            {
                "turn": 9,
                "user": "Yes, all correct",
                "system_action": "Final verification",
                "check": "All fields confirmed",
                "expected_response": "Your lost phone case has been recorded. Case Reference: LOST-2024-002"
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 3: CORRECTION LOOP (Multiple Corrections → Soft Reset)
    # Expected: Collection → Multiple Corrections → Drift Detected → Soft Reset → Completion
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 3: Correction Loop (Drift Detection)",
        "description": "User keeps correcting same field multiple times, triggers drift detection → soft reset",
        "expected_flow": ["collection", "verification", "correction", "correction", "soft_reset", "verification", "completed"],
        "parameters": {
            "correction_count": "Increments with each correction",
            "corrections_on_phone": "Should trigger drift if > 3",
            "sentiment": "Should become 'high' when drift detected",
            "escalation_score": "Increases with corrections"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport yesterday",
                "system_action": "Initial extraction",
                "check": "Intent detected, sentiment=None",
                "expected_response": "I'm sorry. What's your name?"
            },
            {
                "turn": 2,
                "user": "James Thompson",
                "system_action": "Extract name",
                "expected_response": "What's your email?"
            },
            {
                "turn": 3,
                "user": "james.thompson@work.com",
                "system_action": "Extract email",
                "expected_response": "And your phone number?"
            },
            {
                "turn": 4,
                "user": "555-555-1234",
                "system_action": "Extract phone",
                "expected_response": "Let me confirm... Name: James Thompson, Email: james.thompson@work.com, Phone: 555-555-1234. Correct?"
            },
            {
                "turn": 5,
                "user": "No, wait. The phone is wrong. It's 555-555-5678",
                "system_action": "CORRECTION 1: Phone field",
                "check": "correction_count=1, detect_correction_drift() checked",
                "expected_response": "Got it. Phone number is now 555-555-5678. Is everything else correct?"
            },
            {
                "turn": 6,
                "user": "Actually no, the phone is still wrong. It's 555-555-9999",
                "system_action": "CORRECTION 2: Same field (phone)",
                "check": "correction_count=2, same field corrected twice",
                "expected_response": "Updated to 555-555-9999. Anything else?"
            },
            {
                "turn": 7,
                "user": "Hmm, I think the email is also wrong. It should be james@personal.com",
                "system_action": "CORRECTION 3: Email field",
                "check": "correction_count=3, different field, no drift yet",
                "expected_response": "Updated email to james@personal.com. Anything else?"
            },
            {
                "turn": 8,
                "user": "Wait, the phone is STILL not right. Let me think... it's 555-555-4321",
                "system_action": "CORRECTION 4: Phone field again (3rd time on same field!)",
                "check": "correction_count=4, DRIFT DETECTED: same field corrected 3x",
                "check_detail": "detect_correction_drift() returns True → sentiment='high'",
                "expected_response": "I see we're having trouble with these details. Let me start fresh."
            },
            {
                "turn": 9,
                "user": "Okay, I lost my phone yesterday. My correct phone is 555-555-4321, email is james@personal.com",
                "system_action": "SOFT RESET triggered + Fresh extraction",
                "check": "just_reset=True, soft_reset() clears attempts/corrections",
                "expected_response": "Let me verify the phone number. 555-555-4321. Is that correct?"
            },
            {
                "turn": 10,
                "user": "Yes",
                "system_action": "Reverification",
                "expected_response": "And the email: james@personal.com. Correct?"
            },
            {
                "turn": 11,
                "user": "Yes",
                "system_action": "Complete reverification",
                "expected_response": "Perfect. Case recorded. Reference: LOST-2024-003"
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 4: ATTEMPTS EXCEEDED (Direct Handover)
    # Expected: Collection → Multiple Failed Attempts → attempts > 3 → Immediate Handover
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 4: Attempts Exceeded (Direct Handover)",
        "description": "User can't provide phone number clearly, attempts exceed max → immediate handover",
        "expected_flow": ["collection", "handover"],
        "parameters": {
            "attempts": "Increments on each failed extraction",
            "max_attempts": "3 (hardcoded)",
            "direct_check": "if attempts > 3: HANDOVER (no score calc needed)"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone yesterday",
                "system_action": "Initial extraction",
                "expected_response": "What's your name?"
            },
            {
                "turn": 2,
                "user": "Sarah Chen",
                "system_action": "Extract name",
                "expected_response": "What's your email?"
            },
            {
                "turn": 3,
                "user": "sarah@email.com",
                "system_action": "Extract email",
                "expected_response": "And your phone number?"
            },
            {
                "turn": 4,
                "user": "Umm... it's like... 555... I think... maybe 555-something?",
                "system_action": "ATTEMPT 1: Phone extraction fails (unclear)",
                "check": "attempts=1, extraction returned empty",
                "expected_response": "Can you provide your phone number clearly?"
            },
            {
                "turn": 5,
                "user": "I'm not sure. It might be 555-123-4567 or 555-123-5678... I can't remember",
                "system_action": "ATTEMPT 2: Phone extraction fails (multiple options, ambiguous)",
                "check": "attempts=2",
                "expected_response": "Do you have your phone bill or ID with the number?"
            },
            {
                "turn": 6,
                "user": "No, I don't have anything. I'm at the airport and I don't know it",
                "system_action": "ATTEMPT 3: Phone extraction fails (no data available)",
                "check": "attempts=3, no more attempts allowed",
                "expected_response": "Let me try a different approach. What's the phone carrier?"
            },
            {
                "turn": 7,
                "user": "I don't know that either, sorry",
                "system_action": "ATTEMPT 4: Phone extraction fails again",
                "check": "attempts=4 → CHECK: attempts > max_attempts (4 > 3) = TRUE",
                "check_detail": "apply_control() immediate return: {action: 'handover', reason: 'max_attempts_exceeded'}",
                "expected_response": "I understand this is difficult. Let me connect you to an agent who can help locate your phone. Please hold..."
            },
            {
                "turn": 8,
                "user": "Okay",
                "system_action": "HANDOVER",
                "check": "Pipeline stops, human agent takes over",
                "expected_response": "[TRANSFER TO HUMAN AGENT] Your call is being transferred..."
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 5: EXPLICIT HUMAN REQUEST (Immediate Handover)
    # Expected: Collection → User requests human → Immediate Handover
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 5: Explicit Human Request (Immediate Handover)",
        "description": "User explicitly asks to speak to a human → immediate transfer",
        "expected_flow": ["collection", "handover"],
        "parameters": {
            "keywords": "'human', 'agent', 'representative', 'real person'",
            "escalation_score": "NOT calculated (immediate action)"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone and I want to talk to a real person, not a chatbot",
                "system_action": "Check keywords in apply_control()",
                "check": "'real person' detected",
                "check_detail": "return {action: 'handover', reason: 'user_requested_human'}",
                "expected_response": "Of course, let me connect you to an agent right away."
            },
            {
                "turn": 2,
                "user": "Thanks",
                "system_action": "HANDOVER",
                "expected_response": "[TRANSFER TO HUMAN AGENT]"
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 6: ESCALATION SCORE CRITICAL (0.75+) → Handover
    # Expected: Collection → Escalation score buildup → Score >= 0.75 → Handover
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 6: Escalation Score Critical (Handover)",
        "description": "Multiple factors (attempts + corrections + sentiment) push score >= 0.75 → handover",
        "expected_flow": ["collection", "verification", "handover"],
        "parameters": {
            "attempts": "3",
            "corrections": "3+",
            "sentiment": "'high'",
            "formula": "(3/3*0.4) + (3/5*0.3) + (0.7*0.3) = 0.4 + 0.18 + 0.21 = 0.79"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport and this is absolutely ridiculous!",
                "system_action": "Initial extraction",
                "check": "Sentiment detected: 'high' (ridiculous)",
                "expected_response": "I'm sorry. What's your name?"
            },
            {
                "turn": 2,
                "user": "Michael Johnson",
                "system_action": "Extract name",
                "expected_response": "Your email?"
            },
            {
                "turn": 3,
                "user": "michael@company.com",
                "system_action": "Extract email",
                "expected_response": "Phone number?"
            },
            {
                "turn": 4,
                "user": "555-999-8888",
                "system_action": "Extract phone",
                "expected_response": "Let me confirm... is this correct?"
            },
            {
                "turn": 5,
                "user": "No! The email is wrong. It's michael@work.com",
                "system_action": "CORRECTION 1",
                "check": "correction_count=1",
                "expected_response": "Updated. Anything else?"
            },
            {
                "turn": 6,
                "user": "And the phone is wrong too! It's 555-888-9999 and I'm very frustrated with this!",
                "system_action": "CORRECTION 2 + Frustration detected again",
                "check": "correction_count=2, sentiment='high' (frustrated)",
                "expected_response": "Updated. Anything else?"
            },
            {
                "turn": 7,
                "user": "And my name! It should be Michael Robert Johnson. This is so annoying!",
                "system_action": "CORRECTION 3 + 'annoying' detected",
                "check": "correction_count=3, sentiment='high'",
                "expected_response": "Updated. Is everything correct now?"
            },
            {
                "turn": 8,
                "user": "No! I've been telling you the same things over and over! Why can't you understand?!",
                "system_action": "CALCULATE ESCALATION SCORE",
                "check": "attempts=0, corrections=3, sentiment='high'",
                "check_detail": "(0*0.4) + (3/5*0.3) + (0.7*0.3) = 0 + 0.18 + 0.21 = 0.39 (still < 0.75)",
                "expected_response": "I apologize. Let me verify... [Summary]. Correct?"
            },
            {
                "turn": 9,
                "user": "Actually wait, the phone is STILL wrong. Let me change it to 555-777-6666. I can't believe how frustrating this is!",
                "system_action": "CORRECTION 4 (4th correction) + detect_multi_pass_drift",
                "check": "correction_count=4, detect_multi_pass_drift() checks if all fields corrected",
                "check_detail": "if all fields corrected + correcting again → sentiment='high', escalation recalculated",
                "check_detail2": "(1/3*0.4) + (4/5*0.3) + (0.7*0.3) = 0.133 + 0.24 + 0.21 = 0.583 (still < 0.75)",
                "expected_response": "Updated. Let me confirm everything..."
            },
            {
                "turn": 10,
                "user": "No wait! I need to change the email again. And my name is just Michael Johnson without 'Robert'. This is impossible!",
                "system_action": "CORRECTION 5 + Multi-pass drift confirmed",
                "check": "correction_count=5, sentiment='high' (impossible)",
                "check_detail": "(1/3*0.4) + (5/5*0.3) + (0.7*0.3) = 0.133 + 0.30 + 0.21 = 0.643 (approaching 0.75)",
                "expected_response": "I understand. Let me verify... Correct?"
            },
            {
                "turn": 11,
                "user": "No, I'm done. The phone still isn't right! I want someone to actually help me!",
                "system_action": "Check: escalation_score + explicit human request",
                "check": "attempts=0, corrections=5, sentiment='high'",
                "check_detail": "(0*0.4) + (5/5*0.3) + (0.7*0.3) = 0 + 0.3 + 0.21 = 0.51 (< 0.75 but user explicitly asked)",
                "check_detail2": "Keywords detected: 'actually help' might not trigger, BUT multiple signals detected",
                "expected_response": "I completely understand your frustration. Let me connect you to someone who can help immediately."
            },
            {
                "turn": 12,
                "user": "Thank you",
                "system_action": "HANDOVER",
                "check": "High sentiment + multiple corrections + repeated corrections = signal for handover",
                "expected_response": "[TRANSFERRED TO HUMAN AGENT] We have your information ready for the agent."
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 7: "I DON'T KNOW" HANDLING (New Feature)
    # Expected: Collection → User says "I don't know" → Recorded as "unknown" → Continue
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 7: 'I Don't Know' Handling (New Feature)",
        "description": "User can't provide a field value → recorded as 'unknown' → no repeated attempts",
        "expected_flow": ["collection", "verification", "completed"],
        "parameters": {
            "attempts": "Should stay 0 (not a failed extraction)",
            "extraction": "Returns {phone: 'unknown'} as valid value",
            "missing_fields": "Phone not in missing_fields (has a value)"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone at the mall yesterday",
                "system_action": "Initial extraction",
                "expected_response": "I'm sorry. What's your name?"
            },
            {
                "turn": 2,
                "user": "Rachel Martinez",
                "system_action": "Extract name",
                "expected_response": "Your email?"
            },
            {
                "turn": 3,
                "user": "rachel@email.com",
                "system_action": "Extract email",
                "expected_response": "And your phone number?"
            },
            {
                "turn": 4,
                "user": "I don't know my phone number off the top of my head",
                "system_action": "Detect 'I don't know' phrase",
                "check": "detect_unknown_phrase() in extract_field()",
                "check_detail": "returns {phone: 'unknown'} as VALID extraction",
                "check_detail2": "attempts NOT incremented (not a failed extraction)",
                "expected_response": "That's okay. Let me summarize what I have..."
            },
            {
                "turn": 5,
                "user": "Let me see... I think that's all right. The phone is still unknown?",
                "system_action": "Show verification summary",
                "check": "Summary includes: phone = 'unknown'",
                "expected_response": "Yes, we have 'unknown' for phone. Would you like to provide it, or shall we proceed?"
            },
            {
                "turn": 6,
                "user": "Just proceed, they have my email if they need me",
                "system_action": "Verification confirmation",
                "check": "Case can proceed with 'unknown' field",
                "expected_response": "Your lost phone case has been recorded. Case Reference: LOST-2024-007"
            }
        ]
    },

    # ═════════════════════════════════════════════════════════════════════════
    # SCENARIO 8: LOW-CONFIDENCE REVERIFICATION
    # Expected: Collection → Low confidence detected → Soft reset → Reverify → Confirmation boost
    # ═════════════════════════════════════════════════════════════════════════
    {
        "name": "SCENARIO 8: Low-Confidence Field Reverification",
        "description": "Field extracted with low confidence (< 0.80) → After reset, system reverifies",
        "expected_flow": ["collection", "soft_reset", "reverification", "verification", "completed"],
        "parameters": {
            "confidence_threshold": "< 0.80 triggers reverification",
            "reverification_flow": "Ask user to confirm low-confidence fields",
            "confidence_boost": "User confirmation → confidence = 0.95"
        },
        "conversation": [
            {
                "turn": 1,
                "user": "I lost my phone while traveling. Uh, my phone number, well, I think it might be 555-something or maybe 666-something? I'm not really sure.",
                "system_action": "Initial extraction",
                "check": "Phone extracted with LOW confidence (< 0.80), e.g., 0.65",
                "expected_response": "What's your name?"
            },
            {
                "turn": 2,
                "user": "David Lee",
                "system_action": "Extract name",
                "expected_response": "Your email?"
            },
            {
                "turn": 3,
                "user": "david@email.com",
                "system_action": "Extract email",
                "expected_response": "Any other details about your situation?"
            },
            {
                "turn": 4,
                "user": "I was at the airport yesterday afternoon when I lost it",
                "system_action": "Extract additional info, all fields collected",
                "expected_response": "Let me confirm... Name: David Lee, Email: david@email.com, Phone: [uncertain value]. Correct?"
            },
            {
                "turn": 5,
                "user": "I'm not really sure about all this. Can we start over? I'm confused",
                "system_action": "Confusion detected + low confidence + user request → SOFT RESET",
                "check": "just_reset=True, soft_reset() preserves entities but clears attempts",
                "expected_response": "Of course! Let me start fresh. Can you explain again?"
            },
            {
                "turn": 6,
                "user": "I lost my phone at the airport. I think my number starts with 555 but I'm not certain",
                "system_action": "Fresh extraction",
                "check": "just_reset=True triggers reverification check",
                "expected_response": "I have your phone number as 555-XXX-XXXX. Is that correct?"
            },
            {
                "turn": 7,
                "user": "Actually, now that I think about it, yes, it is 555-something. Let me think... I believe it's 555-666-7777",
                "system_action": "Reverification with explicit correction",
                "check": "User provides specific value, confidence boosted to 0.95",
                "expected_response": "Great, I have 555-666-7777. Let me verify everything..."
            },
            {
                "turn": 8,
                "user": "Yes, all correct",
                "system_action": "Final verification",
                "expected_response": "Your case has been recorded. Case Reference: LOST-2024-008"
            }
        ]
    }

]


# ═══════════════════════════════════════════════════════════════════════════
# HOW TO RUN THIS TEST SCRIPT
# ═══════════════════════════════════════════════════════════════════════════

def print_scenario(scenario):
    """Print a formatted scenario"""
    print("\n" + "="*80)
    print(f"TEST: {scenario['name']}")
    print("="*80)
    print(f"\nDescription: {scenario['description']}")
    print(f"\nExpected Flow: {' → '.join(scenario['expected_flow'])}")
    print(f"\nParameters to Monitor:")
    for param, expectation in scenario['parameters'].items():
        print(f"  • {param}: {expectation}")

    print(f"\n{'─'*80}")
    print("CONVERSATION FLOW:")
    print(f"{'─'*80}\n")

    for exchange in scenario['conversation']:
        turn = exchange['turn']
        user_msg = exchange['user']
        action = exchange['system_action']
        checks = exchange.get('check', '')
        check_detail = exchange.get('check_detail', '')
        check_detail2 = exchange.get('check_detail2', '')
        expected = exchange['expected_response']

        print(f"TURN {turn}:")
        print(f"  USER: {user_msg}")
        print(f"  └─ System Action: {action}")
        if checks:
            print(f"     └─ Check: {checks}")
        if check_detail:
            print(f"        └─ Detail: {check_detail}")
        if check_detail2:
            print(f"        └─ Detail: {check_detail2}")
        print(f"  SYSTEM: {expected}")
        print()


def run_all_tests():
    """Run all test scenarios"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "LOST PHONE COMPLAINT - TEST SCENARIOS" + " "*27 + "║")
    print("╚" + "="*78 + "╝")

    for i, scenario in enumerate(TEST_CONVERSATIONS, 1):
        print_scenario(scenario)

        # Pause between scenarios
        if i < len(TEST_CONVERSATIONS):
            input("\n[Press ENTER to continue to next scenario...]\n")


# ═══════════════════════════════════════════════════════════════════════════
# MANUAL TEST INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════

MANUAL_TEST_INSTRUCTIONS = """

MANUAL TESTING WITH YOUR CHATBOT:
═════════════════════════════════════════════════════════════════════════════

To test your code with these scenarios:

1. START YOUR CHATBOT:
   $ python final_2.py

2. COPY-PASTE THE USER MESSAGES FROM EACH SCENARIO

3. FOR EACH TURN, VERIFY:
   - ✓ Correct system response
   - ✓ State changes match expectations
   - ✓ Parameters (attempts, sentiment, score) behave correctly

DEBUGGING CHECKLIST:

□ SCENARIO 1 (Normal Flow):
  - Expect: No errors, smooth progression
  - Watch: No repeated attempts or corrections
  - Check: sentiment stays None or low

□ SCENARIO 2 (Frustration Reset):
  - Expect: System detects frustration and triggers soft reset
  - Watch: "just_reset=True" appears in debug output
  - Check: After reset, system asks to confirm fields again

□ SCENARIO 3 (Correction Loop):
  - Expect: System detects same field corrected 3+ times
  - Watch: sentiment changes to "high"
  - Check: Soft reset triggered, fresh extraction starts

□ SCENARIO 4 (Attempts Exceeded):
  - Expect: After 4 failed attempts → immediate handover
  - Watch: attempts counter increments to 4
  - Check: No escalation score calculation, direct handover

□ SCENARIO 5 (Explicit Human Request):
  - Expect: Immediate handover without processing further
  - Watch: Keywords "real person" detected
  - Check: apply_control() returns handover immediately

□ SCENARIO 6 (Escalation Score Critical):
  - Expect: Multiple corrections + frustration → score >= 0.75
  - Watch: correction_count increments, sentiment="high"
  - Check: Escalation score calculation shown in debug

□ SCENARIO 7 (I Don't Know):
  - Expect: Field set to "unknown", not treated as failure
  - Watch: attempts NOT incremented
  - Check: System continues without re-asking

□ SCENARIO 8 (Low Confidence Reverification):
  - Expect: After reset, low-confidence fields reverified
  - Watch: entity_confidence < 0.80 triggers reverification
  - Check: User confirmation → confidence boosted to 0.95

═════════════════════════════════════════════════════════════════════════════

WHAT TO LOOK FOR IN DEBUG OUTPUT:

1. APPLY_CONTROL() DECISIONS:
   ✓ Check which condition triggered (attempts, score, keywords)
   ✓ Verify action returned (handover, reset, or None)
   ✓ Monitor sentiment changes

2. STATE MANAGEMENT:
   ✓ attempts counter behavior
   ✓ correction_count tracking
   ✓ just_reset flag changes
   ✓ entity_confidence scores

3. ESCALATION SCORE:
   ✓ Formula: (attempts/3*0.4) + (corrections/5*0.3) + (sentiment*0.3)
   ✓ Sentiment mapping: high=0.7, medium_high=0.4, other=0.1, none=0.05
   ✓ Thresholds: 0.55=soft reset, 0.75=handover

4. REVERIFICATION (After Reset):
   ✓ Low-confidence fields (< 0.80) listed
   ✓ User confirmation → confidence = 0.95
   ✓ Correction without inflation (mode="reverify")

═════════════════════════════════════════════════════════════════════════════

EXPECTED DEBUG OUTPUT EXAMPLE:

STATE: attempts=2, corrections=3, sentiment='high'
DEBUG_SIGNALS: {
  'attempts': 2,
  'correction_count': 3,
  'last_corrected_field': 'phone',
  'awaiting_correction': False,
  'just_reset': False,
  'sentiment': 'high'
}

apply_control() checks:
  ✓ Human request? No
  ✓ Attempts > 3? No (2 <= 3)
  ✓ Repetition fatigue? No
  ✓ Field drift? Yes (phone corrected 3x)
    └─ Setting sentiment='high'
  ✓ Escalation score: 0.57 >= 0.55?
    └─ Yes! Triggering SOFT RESET

Returning: {action: 'reset', reason: 'escalation_score_high'}

═════════════════════════════════════════════════════════════════════════════
"""


if __name__ == "__main__":
    # Print instructions first
    print(MANUAL_TEST_INSTRUCTIONS)

    # Ask user if they want to see scenarios
    response = input("\nDo you want to see all test scenarios? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        run_all_tests()
    else:
        print("\nTo test manually:")
        print("1. Copy-paste messages from TEST_CONVERSATIONS above")
        print("2. Run your chatbot: python final_2.py")
        print("3. Compare responses with expected outputs")
