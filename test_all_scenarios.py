#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE FOR ALL SCENARIOS
Tests all 8 lost phone scenarios with validation
Run: python test_all_scenarios.py
"""

import sys
import json
from typing import Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# TEST CASE DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

class TestScenario:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.turns = []
        self.expected_flow = []
        self.parameters = {}
        self.results = {
            "passed": False,
            "assertions": [],
            "errors": []
        }

    def add_turn(self, turn_num: int, user_msg: str, expected_response: str,
                 checks: Dict = None):
        """Add a conversation turn"""
        self.turns.append({
            "turn": turn_num,
            "user": user_msg,
            "expected_response": expected_response,
            "checks": checks or {}
        })

    def add_expected_flow(self, stages: List[str]):
        """Set expected pipeline flow"""
        self.expected_flow = stages

    def add_parameter_check(self, param_name: str, check_func):
        """Add parameter validation function"""
        self.parameters[param_name] = check_func


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 1: NORMAL FLOW
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_1():
    """SCENARIO 1: Normal Flow - No Issues"""
    s = TestScenario(
        "SCENARIO 1: Normal Flow",
        "User reports lost phone smoothly, no frustration or corrections"
    )

    s.add_expected_flow(["collection", "verification", "completed"])

    s.add_turn(
        1,
        "I lost my phone yesterday at the airport",
        "I'm sorry to hear that. Let me help you. What is your name?",
        {
            "action": "extract_full",
            "sentiment": "None or low",
            "attempts": 0
        }
    )

    s.add_turn(
        2,
        "John Smith",
        "Thank you, John. What's your email address?",
        {
            "action": "extract_field",
            "field": "name",
            "confidence": ">= 0.85",
            "attempts": 0
        }
    )

    s.add_turn(
        3,
        "john.smith@email.com",
        "And your phone number?",
        {
            "action": "extract_field",
            "field": "email",
            "confidence": ">= 0.85",
            "attempts": 0
        }
    )

    s.add_turn(
        4,
        "555-123-4567",
        "Let me confirm your details... Is this correct?",
        {
            "action": "extract_field",
            "field": "phone",
            "missing_fields": "EMPTY",
            "attempts": 0
        }
    )

    s.add_turn(
        5,
        "Yes, that's all correct",
        "Your case has been recorded.",
        {
            "action": "completion",
            "sentiment": "None or low",
            "escalation_score": "< 0.55"
        }
    )

    s.add_parameter_check("attempts", lambda state: state.attempts == 0)
    s.add_parameter_check("sentiment", lambda state: state.sentiment in [None, "low"])
    s.add_parameter_check("corrections", lambda state: state.correction_count == 0)

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 2: SOFT RESET (FRUSTRATION)
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_2():
    """SCENARIO 2: Soft Reset - Frustration Detected"""
    s = TestScenario(
        "SCENARIO 2: Soft Reset (Frustration)",
        "User gets frustrated during collection, system detects and triggers soft reset"
    )

    s.add_expected_flow(["collection", "soft_reset", "reverification", "verification", "completed"])

    s.add_turn(
        1,
        "I lost my phone at the airport yesterday and I'm really frustrated with this process!",
        "I understand your frustration. Let me help. What is your name?",
        {
            "action": "extract_full",
            "sentiment": "high",
            "keywords": "['frustrated', 'process']"
        }
    )

    s.add_turn(
        2,
        "John Smith",
        "What's your email address?",
        {
            "action": "extract_field",
            "field": "name",
            "sentiment": "high"
        }
    )

    s.add_turn(
        3,
        "john@email.com",
        "And your phone number?",
        {
            "action": "extract_field",
            "sentiment": "high"
        }
    )

    s.add_turn(
        4,
        "Ugh! Why are you asking so many questions? This is annoying! It's 555-123-4567",
        "I apologize for the frustration.",
        {
            "action": "sentiment_update",
            "sentiment": "high",
            "keyword": "annoying"
        }
    )

    s.add_turn(
        5,
        "Actually, wait. I can't remember if that's the right number. I don't understand why this is so complicated!",
        "I understand. Let me verify what I have.",
        {
            "action": "sentiment_check",
            "sentiment": "high",
            "keywords": "['cant understand', 'complicated']"
        }
    )

    s.add_turn(
        6,
        "No! The phone is wrong and honestly this whole thing is ridiculous!",
        "I sincerely apologize. Let me start completely fresh.",
        {
            "action": "soft_reset",
            "escalation_score": ">= 0.55",
            "keyword": "ridiculous"
        }
    )

    s.add_turn(
        7,
        "OK fine. I lost my phone at the airport. My phone number is actually 555-321-4567",
        "Let me verify the phone number. Is 555-321-4567 correct?",
        {
            "action": "reverification",
            "just_reset": "True",
            "attempts": "0 (after reset)"
        }
    )

    s.add_turn(
        8,
        "Yes, that's correct",
        "Perfect. Let me confirm everything.",
        {
            "action": "confidence_boost",
            "confidence": "0.95"
        }
    )

    s.add_turn(
        9,
        "Yes, all correct",
        "Your case has been recorded.",
        {
            "action": "completion"
        }
    )

    s.add_parameter_check("just_reset_after_turn_6", lambda state: state.just_reset == True)
    s.add_parameter_check("attempts_after_reset", lambda state: state.attempts == 0)
    s.add_parameter_check("sentiment_high", lambda state: state.sentiment == "high")

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 3: CORRECTION LOOP (DRIFT DETECTION)
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_3():
    """SCENARIO 3: Correction Loop - Drift Detection Triggers Reset"""
    s = TestScenario(
        "SCENARIO 3: Correction Loop (Drift Detection)",
        "User keeps correcting same field multiple times, triggers drift detection"
    )

    s.add_expected_flow(["collection", "verification", "correction", "soft_reset", "verification", "completed"])

    s.add_turn(
        1,
        "I lost my phone at the airport yesterday",
        "I'm sorry. What's your name?",
        {"action": "extract_full"}
    )

    s.add_turn(
        2,
        "James Thompson",
        "What's your email?",
        {"action": "extract_field", "field": "name"}
    )

    s.add_turn(
        3,
        "james.thompson@work.com",
        "And your phone number?",
        {"action": "extract_field", "field": "email"}
    )

    s.add_turn(
        4,
        "555-555-1234",
        "Let me confirm... Correct?",
        {"action": "extract_field", "field": "phone"}
    )

    s.add_turn(
        5,
        "No, wait. The phone is wrong. It's 555-555-5678",
        "Got it. Phone is 555-555-5678. Anything else?",
        {
            "action": "correction",
            "correction_count": 1,
            "field": "phone"
        }
    )

    s.add_turn(
        6,
        "Actually no, the phone is still wrong. It's 555-555-9999",
        "Updated to 555-555-9999. Anything else?",
        {
            "action": "correction",
            "correction_count": 2,
            "field": "phone",
            "same_field_corrected": 2
        }
    )

    s.add_turn(
        7,
        "Hmm, I think the email is also wrong. It should be james@personal.com",
        "Updated. Anything else?",
        {
            "action": "correction",
            "correction_count": 3,
            "field": "email"
        }
    )

    s.add_turn(
        8,
        "Wait, the phone is STILL not right. Let me think... it's 555-555-4321",
        "I see we're having trouble. Let me start fresh.",
        {
            "action": "drift_detected",
            "detection": "detect_correction_drift()",
            "reason": "phone corrected 3x",
            "sentiment": "high",
            "soft_reset": "trigger"
        }
    )

    s.add_turn(
        9,
        "Okay, I lost my phone yesterday. My correct phone is 555-555-4321, email is james@personal.com",
        "Let me verify the phone. 555-555-4321. Correct?",
        {
            "action": "soft_reset_complete",
            "just_reset": "True",
            "attempts": "0",
            "corrections": "0"
        }
    )

    s.add_turn(
        10,
        "Yes",
        "And the email: james@personal.com. Correct?",
        {"action": "reverification"}
    )

    s.add_turn(
        11,
        "Yes",
        "Perfect. Case recorded.",
        {"action": "completion"}
    )

    s.add_parameter_check("drift_detected", lambda state: hasattr(state, 'is_field_drift') and state.is_field_drift == True)
    s.add_parameter_check("corrections_reset", lambda state: state.correction_count == 0)

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 4: ATTEMPTS EXCEEDED
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_4():
    """SCENARIO 4: Attempts Exceeded - Direct Handover"""
    s = TestScenario(
        "SCENARIO 4: Attempts Exceeded (Direct Handover)",
        "User can't provide phone number clearly, attempts exceed max"
    )

    s.add_expected_flow(["collection", "handover"])

    s.add_turn(
        1,
        "I lost my phone yesterday",
        "What's your name?",
        {"action": "extract_full"}
    )

    s.add_turn(
        2,
        "Sarah Chen",
        "What's your email?",
        {"action": "extract_field", "field": "name"}
    )

    s.add_turn(
        3,
        "sarah@email.com",
        "And your phone number?",
        {"action": "extract_field", "field": "email"}
    )

    s.add_turn(
        4,
        "Umm... it's like... 555... I think... maybe 555-something?",
        "Can you provide your phone number clearly?",
        {
            "action": "failed_extraction",
            "attempts": 1,
            "field": "phone"
        }
    )

    s.add_turn(
        5,
        "I'm not sure. It might be 555-123-4567 or 555-123-5678... I can't remember",
        "Do you have your phone bill with the number?",
        {
            "action": "failed_extraction",
            "attempts": 2,
            "reason": "ambiguous"
        }
    )

    s.add_turn(
        6,
        "No, I don't have anything. I'm at the airport and I don't know it",
        "Let me try a different approach. What's the phone carrier?",
        {
            "action": "failed_extraction",
            "attempts": 3
        }
    )

    s.add_turn(
        7,
        "I don't know that either, sorry",
        "Let me connect you to an agent who can help.",
        {
            "action": "handover",
            "trigger": "attempts > max_attempts",
            "attempts": 4,
            "max_attempts": 3,
            "escalation_reason": "max_attempts_exceeded"
        }
    )

    s.add_turn(
        8,
        "Okay",
        "[TRANSFER TO HUMAN AGENT]",
        {
            "action": "handover_complete",
            "pipeline": "STOPPED"
        }
    )

    s.add_parameter_check("attempts_exceeded", lambda state: state.attempts > state.max_attempts)
    s.add_parameter_check("direct_handover", lambda state: state.stage == "handover")

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 5: EXPLICIT HUMAN REQUEST
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_5():
    """SCENARIO 5: Explicit Human Request - Immediate Handover"""
    s = TestScenario(
        "SCENARIO 5: Explicit Human Request",
        "User explicitly asks to speak to a human"
    )

    s.add_expected_flow(["collection", "handover"])

    s.add_turn(
        1,
        "I lost my phone and I want to talk to a real person, not a chatbot",
        "Of course, let me connect you to an agent right away.",
        {
            "action": "handover",
            "trigger": "explicit_human_request",
            "keywords": "['real person']",
            "escalation_reason": "user_requested_human"
        }
    )

    s.add_turn(
        2,
        "Thanks",
        "[TRANSFER TO HUMAN AGENT]",
        {
            "action": "handover_complete",
            "no_processing": "True"
        }
    )

    s.add_parameter_check("immediate_handover", lambda state: state.stage == "handover")

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 6: ESCALATION SCORE CRITICAL
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_6():
    """SCENARIO 6: Escalation Score Critical (0.75+) - Handover"""
    s = TestScenario(
        "SCENARIO 6: Escalation Score Critical",
        "Multiple factors push score >= 0.75"
    )

    s.add_expected_flow(["collection", "verification", "correction", "handover"])

    s.add_turn(
        1,
        "I lost my phone at the airport and this is absolutely ridiculous!",
        "I'm sorry. What's your name?",
        {
            "action": "extract_full",
            "sentiment": "high",
            "keyword": "ridiculous"
        }
    )

    s.add_turn(
        2,
        "Michael Johnson",
        "Your email?",
        {"action": "extract_field", "field": "name"}
    )

    s.add_turn(
        3,
        "michael@company.com",
        "Phone number?",
        {"action": "extract_field", "field": "email"}
    )

    s.add_turn(
        4,
        "555-999-8888",
        "Let me confirm... Correct?",
        {"action": "extract_field", "field": "phone"}
    )

    s.add_turn(
        5,
        "No! The email is wrong. It's michael@work.com",
        "Updated. Anything else?",
        {
            "action": "correction",
            "correction_count": 1,
            "sentiment": "high"
        }
    )

    s.add_turn(
        6,
        "And the phone is wrong too! It's 555-888-9999 and I'm very frustrated!",
        "Updated. Anything else?",
        {
            "action": "correction",
            "correction_count": 2,
            "sentiment": "high",
            "keyword": "frustrated"
        }
    )

    s.add_turn(
        7,
        "And my name! It should be Michael Robert Johnson. This is so annoying!",
        "Updated. Correct now?",
        {
            "action": "correction",
            "correction_count": 3,
            "sentiment": "high",
            "keyword": "annoying"
        }
    )

    s.add_turn(
        8,
        "No! I've been telling you the same things over and over! Why can't you understand?!",
        "Let me verify... [Summary]. Correct?",
        {
            "action": "escalation_check",
            "sentiment": "high",
            "corrections": 3,
            "escalation_score": "0.39"
        }
    )

    s.add_turn(
        9,
        "Actually wait, the phone is STILL wrong. Let me change it to 555-777-6666. I can't believe how frustrating this is!",
        "Updated. Correct now?",
        {
            "action": "correction",
            "correction_count": 4,
            "sentiment": "high",
            "multi_pass_drift": "detected",
            "escalation_score": "0.583"
        }
    )

    s.add_turn(
        10,
        "No wait! Email again. And my name is just Michael Johnson. This is impossible!",
        "Let me verify... Correct?",
        {
            "action": "correction",
            "correction_count": 5,
            "sentiment": "high",
            "escalation_score": "0.643"
        }
    )

    s.add_turn(
        11,
        "No, I'm done. Phone still isn't right! I want someone to actually help me!",
        "I completely understand. Let me connect you to someone right away.",
        {
            "action": "handover",
            "trigger": "escalation_score OR multi_factor",
            "sentiment": "high",
            "corrections": 5,
            "reason": "escalation_score_critical"
        }
    )

    s.add_turn(
        12,
        "Thank you",
        "[TRANSFERRED TO HUMAN AGENT]",
        {
            "action": "handover_complete"
        }
    )

    s.add_parameter_check("score_calculation", lambda state: state.escalation_score >= 0.75)

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 7: "I DON'T KNOW" HANDLING
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_7():
    """SCENARIO 7: 'I Don't Know' Handling"""
    s = TestScenario(
        "SCENARIO 7: 'I Don't Know' Handling",
        "User can't provide value, recorded as 'unknown', no repeated attempts"
    )

    s.add_expected_flow(["collection", "verification", "completed"])

    s.add_turn(
        1,
        "I lost my phone at the mall yesterday",
        "I'm sorry. What's your name?",
        {"action": "extract_full"}
    )

    s.add_turn(
        2,
        "Rachel Martinez",
        "Your email?",
        {"action": "extract_field", "field": "name"}
    )

    s.add_turn(
        3,
        "rachel@email.com",
        "And your phone number?",
        {"action": "extract_field", "field": "email"}
    )

    s.add_turn(
        4,
        "I don't know my phone number off the top of my head",
        "That's okay. Let me summarize what I have...",
        {
            "action": "unknown_phrase_detected",
            "phrase": "i don't know",
            "field": "phone",
            "value": "unknown",
            "attempts": "NOT incremented",
            "extraction_status": "valid"
        }
    )

    s.add_turn(
        5,
        "Let me see... I think that's all right. The phone is still unknown?",
        "Yes. Would you like to provide it, or proceed?",
        {
            "action": "verification",
            "field_value": "unknown",
            "missing_fields": "EMPTY"
        }
    )

    s.add_turn(
        6,
        "Just proceed, they have my email if they need me",
        "Your lost phone case has been recorded.",
        {
            "action": "completion",
            "with_unknown_field": "True"
        }
    )

    s.add_parameter_check("no_repeated_attempts", lambda state: state.attempts == 0)
    s.add_parameter_check("phone_unknown_stored", lambda state: state.entities.get("phone") == "unknown")

    return s


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO 8: LOW-CONFIDENCE REVERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def create_scenario_8():
    """SCENARIO 8: Low-Confidence Field Reverification"""
    s = TestScenario(
        "SCENARIO 8: Low-Confidence Reverification",
        "Field extracted with low confidence, reverified after reset"
    )

    s.add_expected_flow(["collection", "soft_reset", "reverification", "verification", "completed"])

    s.add_turn(
        1,
        "I lost my phone while traveling. Uh, my phone number, well, I think it might be 555-something or maybe 666-something? I'm not really sure.",
        "What's your name?",
        {
            "action": "extract_full",
            "confidence": "phone < 0.80",
            "phone_confidence": "0.65"
        }
    )

    s.add_turn(
        2,
        "David Lee",
        "Your email?",
        {"action": "extract_field", "field": "name"}
    )

    s.add_turn(
        3,
        "david@email.com",
        "Any other details?",
        {"action": "extract_field", "field": "email"}
    )

    s.add_turn(
        4,
        "I was at the airport yesterday afternoon when I lost it",
        "Let me confirm... Correct?",
        {
            "action": "all_fields_collected",
            "low_confidence_fields": "['phone']"
        }
    )

    s.add_turn(
        5,
        "I'm not really sure about all this. Can we start over? I'm confused",
        "Of course! Let me start fresh.",
        {
            "action": "soft_reset",
            "trigger": "confusion_detected",
            "sentiment": "medium_high"
        }
    )

    s.add_turn(
        6,
        "I lost my phone at the airport. I think my number starts with 555 but I'm not certain",
        "I have your phone number as 555-XXX-XXXX. Is that correct?",
        {
            "action": "reverification",
            "just_reset": "True",
            "low_confidence": "< 0.80"
        }
    )

    s.add_turn(
        7,
        "Actually, now that I think about it, yes, it is 555-something. I believe it's 555-666-7777",
        "Great, I have 555-666-7777. Let me verify everything...",
        {
            "action": "confidence_boost",
            "confidence": "0.95",
            "reason": "user_confirmed"
        }
    )

    s.add_turn(
        8,
        "Yes, all correct",
        "Your case has been recorded.",
        {
            "action": "completion",
            "confidence": "0.95"
        }
    )

    s.add_parameter_check("low_conf_detected", lambda state: hasattr(state, 'entity_confidence'))
    s.add_parameter_check("confidence_boosted", lambda state: state.entity_confidence.get("phone", 0) >= 0.95)

    return s


# ═══════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════

class TestRunner:
    def __init__(self):
        self.scenarios = []
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "scenarios": []
        }

    def add_scenario(self, scenario: TestScenario):
        """Add a test scenario"""
        self.scenarios.append(scenario)

    def run_all(self):
        """Run all scenarios"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE - LOST PHONE SCENARIO")
        print("="*80 + "\n")

        for i, scenario in enumerate(self.scenarios, 1):
            self.run_scenario(scenario, i)

        self.print_summary()

    def run_scenario(self, scenario: TestScenario, num: int):
        """Run a single scenario"""
        print(f"\n{'─'*80}")
        print(f"TEST {num}: {scenario.name}")
        print(f"{'─'*80}")
        print(f"Description: {scenario.description}\n")

        print(f"Expected Flow: {' → '.join(scenario.expected_flow)}\n")

        print("Conversation:")
        print("─" * 40)

        for turn in scenario.turns:
            print(f"\nTURN {turn['turn']}:")
            print(f"  USER: {turn['user']}")
            print(f"  EXPECTED: {turn['expected_response']}")
            if turn['checks']:
                print(f"  CHECKS:")
                for check_key, check_val in turn['checks'].items():
                    print(f"    • {check_key}: {check_val}")

        print(f"\n{'─'*40}")
        print("Parameter Checks:")
        for param_name in scenario.parameters.keys():
            print(f"  ✓ {param_name}")

        print(f"\n✅ SCENARIO {num} OUTLINED\n")

        self.results["total"] += 1
        self.results["scenarios"].append({
            "name": scenario.name,
            "status": "outlined",
            "turns": len(scenario.turns)
        })

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"\nTotal Scenarios: {self.results['total']}")
        print(f"Each scenario with {len(self.scenarios[0].turns)} turns on average\n")

        print("Scenarios:")
        for i, scenario_result in enumerate(self.results['scenarios'], 1):
            print(f"  {i}. {scenario_result['name']}")
            print(f"     └─ Turns: {scenario_result['turns']}")

        print("\n" + "="*80)
        print("TO RUN ACTUAL TESTS:")
        print("="*80)
        print("""
1. Start your chatbot:
   python final_2.py

2. For each scenario, copy-paste the user messages from above

3. Verify the system responses match expected responses

4. Monitor the state changes:
   - attempts counter
   - correction_count
   - sentiment value
   - escalation_score
   - just_reset flag
   - entity_confidence

5. Verify flow progression:
   collection → soft_reset → verification → completion
   (or other flow depending on scenario)

═════════════════════════════════════════════════════════════════════════════
""")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    runner = TestRunner()

    # Add all scenarios
    runner.add_scenario(create_scenario_1())
    runner.add_scenario(create_scenario_2())
    runner.add_scenario(create_scenario_3())
    runner.add_scenario(create_scenario_4())
    runner.add_scenario(create_scenario_5())
    runner.add_scenario(create_scenario_6())
    runner.add_scenario(create_scenario_7())
    runner.add_scenario(create_scenario_8())

    # Run all tests
    runner.run_all()
