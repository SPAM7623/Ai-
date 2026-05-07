# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an AI-powered case management system that processes user complaints/issues through an intelligent multi-agent pipeline. The system guides users through collecting, verifying, and escalating cases with natural language understanding and conversational flow control.

## Running the System

### Basic Execution
```bash
python final_2.py
```

This starts an interactive loop that:
1. Accepts user input (type `exit` or `quit` to stop)
2. Runs the multi-agent pipeline
3. Prints the bot response and current state

### API Key Setup

The system requires an OpenAI/Claude API key. Currently, it's hardcoded at line 3359:
```python
API_KEY = "sk-proj-..."
```

Before running, ensure this key is valid and has appropriate quota.

## Architecture

### Core State Management
**CaseState** (lines 15-343) - Dataclass that maintains the conversation state:
- **Case Information**: intent, department, current_issue
- **Entity Storage**: Stores extracted entities with confidence scores and sources
- **NLP Signals**: sentiment, confidence, language detection
- **Field Management**: Tracks required fields, missing fields, and validation attempts
- **Flow Control**: Manages pipeline stages (collection → verification → correction → completed)
- **Correction Tracking**: Tracks user corrections and repeated fields

Key methods:
- `update_entity()` / `remove_entity()` - Safely manage extracted data
- `increment_field_attempt()` - Track field extraction attempts
- `soft_reset()` / `full_reset()` - Reset conversation state while preserving/clearing data
- `set_stage()` - Transition between pipeline stages

### Agent Architecture
The Pipeline (lines 2804+) orchestrates six specialized agents:

1. **InputAgent** (lines 344-365) - Processes raw user input
2. **UnderstandingAgent** (lines 366-936) - Determines user intent, extracts entities, detects sentiment/language
3. **CaseBuilderAgent** (lines 937-1571) - Manages case/complaint structure, field schemas, department logic
4. **InteractionAgent** (lines 1572-2047) - Generates conversational prompts (asking for fields, clarifications, corrections)
5. **VerificationAgent** (lines 2048-2377) - Creates summaries and verification messages
6. **DecisionAgent** (lines 2378-2803) - Determines next action in the conversation flow

Each agent accepts the CaseState and produces outputs like text responses or structured decisions.

### Pipeline Execution (lines 2951+)
The main `run()` method:
1. **Control checks** (lines 2830-2907) - Evaluates if conditions warrant handover/reset (excessive attempts, high distress, too many corrections)
2. **Routing based on stage**:
   - **collection**: Gather missing fields until all required fields are collected
   - **verification**: Summarize and ask user to confirm
   - **correction**: Handle user-requested field changes
   - **completed**: Final confirmation and case closure
3. **Escalation logic**: Routes to human agents on failure thresholds

### Flow Control States
The pipeline manages these states (defined in CaseState.stage):
- `collection` - Initial data gathering
- `verification` - Confirm collected information
- `correction` - Fix incorrect fields
- `completed` - Case successfully recorded
- `restart` - User requested restart
- `handover` - Escalation to human agent

### Escalation Triggers (lines 2830-2907)
The system escalates to human agents when:
- User explicitly requests human/agent/representative
- Maximum attempts exceeded (3+)
- High sentiment distress with 2+ failed attempts
- 4+ corrections on same field
- Correction loop detected (2+ attempts while awaiting correction)

## Development Notes

### Adding New Fields/Departments
Field schemas are defined in the CaseBuilderAgent. When modifying case requirements:
1. Update field definitions in the CaseBuilderAgent constructor
2. Add extraction logic in UnderstandingAgent
3. Add validation in CaseBuilderAgent if needed
4. Update department mappings if field applies to specific departments only

### Understanding Conversation Flow
The system uses a state machine approach:
- Each turn, `Pipeline.run()` evaluates current state and returns (updated_state, response)
- The response includes `text` (for user) and `action` (internal routing: ask_field, verify, correct, complete, handover, reset, clarify)
- State preserves context across turns for coherent multi-turn conversations

### Debugging
The main loop (lines 3365+) prints detailed state information:
- Full CaseState object
- Key debug signals: attempts, correction_count, sentiment, flow flags
- This output is essential for understanding why certain decisions are made

### Key Design Decisions
- **Confidence tracking** (0.0-1.0): Indicates extraction quality; affects retry logic
- **Field attempt limits**: Prevents infinite loops on problematic fields
- **Soft vs full reset**: Soft reset preserves entities for context; full reset clears everything
- **Sentiment-based escalation**: Combines distress detection with failure thresholds for empathetic escalation

## Dependencies

The code imports:
- `dataclasses` - For state management (Python 3.7+)
- `typing` - For type hints
- Implicit: API client library for LLM (inferred from API_KEY pattern and agent implementations)

Install if needed:
```bash
pip install anthropic
# or
pip install openai
```

## Testing and Validation

Currently, no automated tests are configured. To test:
1. Run `python final_2.py`
2. Test each pipeline stage by providing different inputs
3. Monitor console output and state transitions
4. Verify escalation triggers by forcing specific conditions (e.g., exceeding max_attempts)
