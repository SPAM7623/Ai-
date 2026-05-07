#!/usr/bin/env python3
"""
INTERACTIVE TEST RUNNER
Allows user to select and run individual scenarios
Run: python run_interactive_test.py
"""

import json
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════════════════
# ALL TEST SCENARIOS DATA
# ═══════════════════════════════════════════════════════════════════════════

SCENARIOS = {
    "1": {
        "name": "Normal Flow (No Issues)",
        "description": "User reports lost phone smoothly",
        "expected_flow": ["collection", "verification", "completed"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone yesterday at the airport",
                "system_action": "Extract intent, sentiment, entities",
                "checks": "sentiment=None/low, attempts=0"
            },
            {
                "turn": 2,
                "user": "John Smith",
                "system_action": "Extract name field",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 3,
                "user": "john.smith@email.com",
                "system_action": "Extract email field",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 4,
                "user": "555-123-4567",
                "system_action": "Extract phone field",
                "checks": "All fields collected"
            },
            {
                "turn": 5,
                "user": "Yes, that's all correct",
                "system_action": "Completion",
                "checks": "sentiment < 0.55, corrections=0"
            }
        ]
    },

    "2": {
        "name": "Soft Reset (Frustration)",
        "description": "User gets frustrated, system detects and resets",
        "expected_flow": ["collection", "soft_reset", "reverification", "verification", "completed"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport yesterday and I'm really frustrated with this process!",
                "system_action": "Extract, detect frustration",
                "checks": "sentiment=high"
            },
            {
                "turn": 2,
                "user": "John Smith",
                "system_action": "Extract name",
                "checks": "sentiment stays high"
            },
            {
                "turn": 3,
                "user": "john@email.com",
                "system_action": "Extract email",
                "checks": "No reset yet"
            },
            {
                "turn": 4,
                "user": "Ugh! Why are you asking so many questions? This is annoying! It's 555-123-4567",
                "system_action": "Detect 'annoying', check escalation",
                "checks": "sentiment=high"
            },
            {
                "turn": 5,
                "user": "Actually, wait. I can't remember if that's the right number. I don't understand why this is so complicated!",
                "system_action": "Check escalation_score",
                "checks": "sentiment=high, building score"
            },
            {
                "turn": 6,
                "user": "No! The phone is wrong and honestly this whole thing is ridiculous!",
                "system_action": "TRIGGER SOFT RESET",
                "checks": "escalation_score >= 0.55, soft_reset() called"
            },
            {
                "turn": 7,
                "user": "OK fine. I lost my phone at the airport. My phone number is actually 555-321-4567",
                "system_action": "Fresh extraction after reset",
                "checks": "just_reset=True, attempts=0"
            },
            {
                "turn": 8,
                "user": "Yes, that's correct",
                "system_action": "Reverification confirmation",
                "checks": "confidence=0.95"
            },
            {
                "turn": 9,
                "user": "Yes, all correct",
                "system_action": "Completion",
                "checks": "Case recorded"
            }
        ]
    },

    "3": {
        "name": "Correction Loop (Drift Detection)",
        "description": "User corrects same field multiple times",
        "expected_flow": ["collection", "soft_reset", "verification", "completed"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport yesterday",
                "system_action": "Extract intent",
                "checks": "sentiment=None"
            },
            {
                "turn": 2,
                "user": "James Thompson",
                "system_action": "Extract name",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 3,
                "user": "james.thompson@work.com",
                "system_action": "Extract email",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 4,
                "user": "555-555-1234",
                "system_action": "Extract phone",
                "checks": "All fields collected"
            },
            {
                "turn": 5,
                "user": "No, wait. The phone is wrong. It's 555-555-5678",
                "system_action": "CORRECTION 1: phone",
                "checks": "correction_count=1"
            },
            {
                "turn": 6,
                "user": "Actually no, the phone is still wrong. It's 555-555-9999",
                "system_action": "CORRECTION 2: phone (same field)",
                "checks": "correction_count=2, same_field_count=2"
            },
            {
                "turn": 7,
                "user": "Hmm, I think the email is also wrong. It should be james@personal.com",
                "system_action": "CORRECTION 3: email",
                "checks": "correction_count=3"
            },
            {
                "turn": 8,
                "user": "Wait, the phone is STILL not right. Let me think... it's 555-555-4321",
                "system_action": "DRIFT DETECTED: phone corrected 3x",
                "checks": "sentiment=high, soft_reset triggered"
            },
            {
                "turn": 9,
                "user": "Okay, I lost my phone yesterday. My phone is 555-555-4321, email is james@personal.com",
                "system_action": "Fresh extraction",
                "checks": "just_reset=True, attempts=0, corrections=0"
            },
            {
                "turn": 10,
                "user": "Yes",
                "system_action": "Verify phone",
                "checks": "confidence=0.95"
            },
            {
                "turn": 11,
                "user": "Yes",
                "system_action": "Verify email",
                "checks": "confidence=0.95"
            }
        ]
    },

    "4": {
        "name": "Attempts Exceeded",
        "description": "Failed extraction attempts exceed max (3)",
        "expected_flow": ["collection", "handover"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone yesterday",
                "system_action": "Extract intent",
                "checks": "Intent detected"
            },
            {
                "turn": 2,
                "user": "Sarah Chen",
                "system_action": "Extract name",
                "checks": "Name extracted"
            },
            {
                "turn": 3,
                "user": "sarah@email.com",
                "system_action": "Extract email",
                "checks": "Email extracted"
            },
            {
                "turn": 4,
                "user": "Umm... it's like... 555... I think... maybe 555-something?",
                "system_action": "ATTEMPT 1: phone extraction fails",
                "checks": "attempts=1"
            },
            {
                "turn": 5,
                "user": "I'm not sure. It might be 555-123-4567 or 555-123-5678",
                "system_action": "ATTEMPT 2: phone extraction fails",
                "checks": "attempts=2"
            },
            {
                "turn": 6,
                "user": "No, I don't have anything. I'm at the airport and I don't know it",
                "system_action": "ATTEMPT 3: phone extraction fails",
                "checks": "attempts=3, max_attempts=3"
            },
            {
                "turn": 7,
                "user": "I don't know that either",
                "system_action": "ATTEMPT 4: HANDOVER",
                "checks": "attempts > max_attempts (4 > 3), HANDOVER"
            }
        ]
    },

    "5": {
        "name": "Explicit Human Request",
        "description": "User explicitly asks for human agent",
        "expected_flow": ["handover"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone and I want to talk to a real person, not a chatbot",
                "system_action": "Detect human request keywords",
                "checks": "Keywords: 'real person' detected, IMMEDIATE HANDOVER"
            },
            {
                "turn": 2,
                "user": "Thanks",
                "system_action": "HANDOVER",
                "checks": "Pipeline stopped"
            }
        ]
    },

    "6": {
        "name": "Escalation Score Critical (0.75+)",
        "description": "Multiple factors push score >= 0.75",
        "expected_flow": ["collection", "verification", "handover"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone at the airport and this is absolutely ridiculous!",
                "system_action": "Extract, sentiment=high",
                "checks": "Keyword: 'ridiculous'"
            },
            {
                "turn": 2,
                "user": "Michael Johnson",
                "system_action": "Extract name",
                "checks": "sentiment=high"
            },
            {
                "turn": 3,
                "user": "michael@company.com",
                "system_action": "Extract email",
                "checks": "sentiment=high"
            },
            {
                "turn": 4,
                "user": "555-999-8888",
                "system_action": "Extract phone",
                "checks": "All fields collected"
            },
            {
                "turn": 5,
                "user": "No! The email is wrong. It's michael@work.com",
                "system_action": "CORRECTION 1",
                "checks": "correction_count=1, sentiment=high"
            },
            {
                "turn": 6,
                "user": "And the phone is wrong too! It's 555-888-9999",
                "system_action": "CORRECTION 2",
                "checks": "correction_count=2"
            },
            {
                "turn": 7,
                "user": "And my name! It should be Michael Robert Johnson. This is so annoying!",
                "system_action": "CORRECTION 3",
                "checks": "correction_count=3, keyword: 'annoying'"
            },
            {
                "turn": 8,
                "user": "Actually wait, the phone is STILL wrong. Let me change it to 555-777-6666",
                "system_action": "CORRECTION 4",
                "checks": "correction_count=4, multi_pass_drift detected"
            },
            {
                "turn": 9,
                "user": "No wait! Email again. And my name is just Michael Johnson. This is impossible!",
                "system_action": "CORRECTION 5",
                "checks": "correction_count=5, escalation_score building"
            },
            {
                "turn": 10,
                "user": "No, I'm done. Phone still isn't right! I want someone to actually help me!",
                "system_action": "CHECK SCORE >= 0.75",
                "checks": "HANDOVER triggered"
            }
        ]
    },

    "7": {
        "name": "'I Don't Know' Handling",
        "description": "User can't provide value, recorded as 'unknown'",
        "expected_flow": ["collection", "verification", "completed"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone at the mall yesterday",
                "system_action": "Extract intent",
                "checks": "Intent detected"
            },
            {
                "turn": 2,
                "user": "Rachel Martinez",
                "system_action": "Extract name",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 3,
                "user": "rachel@email.com",
                "system_action": "Extract email",
                "checks": "confidence >= 0.85"
            },
            {
                "turn": 4,
                "user": "I don't know my phone number off the top of my head",
                "system_action": "DETECT 'I don't know'",
                "checks": "field=unknown, attempts NOT incremented"
            },
            {
                "turn": 5,
                "user": "Just proceed, they have my email if they need me",
                "system_action": "Verification with unknown field",
                "checks": "phone='unknown' in summary"
            }
        ]
    },

    "8": {
        "name": "Low-Confidence Reverification",
        "description": "Field with low confidence reverified after reset",
        "expected_flow": ["collection", "soft_reset", "reverification", "verification", "completed"],
        "turns": [
            {
                "turn": 1,
                "user": "I lost my phone. My number is 555 or maybe 666? I'm not sure.",
                "system_action": "Extract with LOW confidence",
                "checks": "phone_confidence < 0.80"
            },
            {
                "turn": 2,
                "user": "David Lee",
                "system_action": "Extract name",
                "checks": "Name extracted"
            },
            {
                "turn": 3,
                "user": "david@email.com",
                "system_action": "Extract email",
                "checks": "Email extracted"
            },
            {
                "turn": 4,
                "user": "I'm confused. Can we start over?",
                "system_action": "TRIGGER SOFT RESET",
                "checks": "Low confidence detected, soft_reset triggered"
            },
            {
                "turn": 5,
                "user": "I lost my phone at the airport. I think my number starts with 555",
                "system_action": "Fresh extraction",
                "checks": "just_reset=True"
            },
            {
                "turn": 6,
                "user": "I believe it's 555-666-7777",
                "system_action": "REVERIFICATION with correction",
                "checks": "confidence boosted to 0.95"
            },
            {
                "turn": 7,
                "user": "Yes, all correct",
                "system_action": "Completion",
                "checks": "Case recorded"
            }
        ]
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════════════════

def print_header():
    """Print test suite header"""
    print("\n" + "="*80)
    print("LOST PHONE SCENARIO - INTERACTIVE TEST RUNNER")
    print("="*80 + "\n")


def print_menu():
    """Print scenario menu"""
    print("Select a scenario to test:\n")
    for num, (key, scenario) in enumerate(SCENARIOS.items(), 1):
        print(f"  {key}. {scenario['name']}")
        print(f"     └─ {scenario['description']}")
    print(f"\n  0. Run All Scenarios")
    print(f"  9. Exit\n")


def print_scenario_details(scenario_num: str):
    """Print detailed scenario information"""
    if scenario_num not in SCENARIOS:
        print(f"Invalid scenario number: {scenario_num}")
        return

    scenario = SCENARIOS[scenario_num]

    print("\n" + "="*80)
    print(f"SCENARIO {scenario_num}: {scenario['name']}")
    print("="*80)
    print(f"\nDescription: {scenario['description']}")
    print(f"\nExpected Flow: {' → '.join(scenario['expected_flow'])}\n")

    print("CONVERSATION SCRIPT:")
    print("─" * 80)

    for turn in scenario['turns']:
        print(f"\nTURN {turn['turn']}:")
        print(f"  📱 USER INPUT:")
        print(f"     \"{turn['user']}\"")
        print(f"\n  🤖 SYSTEM ACTION:")
        print(f"     {turn['system_action']}")
        print(f"\n  ✅ CHECKS:")
        print(f"     {turn['checks']}")

    print("\n" + "─"*80)
    print("\n⚙️  HOW TO TEST THIS SCENARIO:\n")
    print("""
1. Open TWO terminal windows:

   Terminal 1:
   $ python final_2.py

   Terminal 2:
   $ Keep this script open for reference

2. For each TURN in the scenario:

   a) Copy the USER INPUT from above
   b) Paste it into Terminal 1 (where your chatbot is running)
   c) Press ENTER

3. Compare SYSTEM RESPONSE:

   a) Read what your bot says
   b) Compare with EXPECTED in this scenario
   c) Check if similar (exact wording may vary)

4. Verify CHECKS:

   a) Look for expected debug output
   b) Monitor state variables:
      - attempts
      - sentiment
      - correction_count
      - escalation_score
      - just_reset
      - entity_confidence

5. If anything unexpected:

   a) Note the difference
   b) Check code logic
   c) Verify parameters

═════════════════════════════════════════════════════════════════════════════
    """)


def run_all_scenarios():
    """Display all scenarios"""
    print("\n" + "="*80)
    print("ALL SCENARIOS")
    print("="*80 + "\n")

    for scenario_num in sorted(SCENARIOS.keys()):
        print_scenario_details(scenario_num)
        input("\n[Press ENTER to continue to next scenario...]")


def main():
    """Main interactive menu"""
    print_header()

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            run_all_scenarios()
        elif choice in SCENARIOS:
            print_scenario_details(choice)
            input("\n[Press ENTER to return to menu...]")
        elif choice == "9":
            print("\n👋 Goodbye!\n")
            break
        else:
            print(f"\n❌ Invalid choice. Please try again.\n")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT SCENARIOS AS JSON
# ═══════════════════════════════════════════════════════════════════════════

def export_scenarios_to_json(filename: str = "test_scenarios.json"):
    """Export all scenarios to JSON for other tools"""
    with open(filename, 'w') as f:
        json.dump(SCENARIOS, f, indent=2)
    print(f"✅ Scenarios exported to {filename}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!\n")
