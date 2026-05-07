# Advanced Conversation Scenarios

## Scenario 5: Low-Confidence Reverification → User Rejects → Correction

```
USER: I want to report a billing issue with my subscription

SYSTEM: I'll help you resolve that. What's your name?

USER: Amanda

SYSTEM: Nice to meet you, Amanda. What's your last name?

USER: Rodriguez... well, actually that's my maiden name.
      I got married last year. It's now Garcia.

SYSTEM: [Extraction confidence: 0.62 - LOW]
        Let me note your last name as Garcia.
        
        What email address is associated with your account?

USER: amanda.garcia@email.com

SYSTEM: And your phone number?

USER: 555-555-1234

SYSTEM: [All fields collected - Moving to verification]
        
        Let me confirm:
        Name: Amanda Garcia
        Email: amanda.garcia@email.com
        Phone: 555-555-1234
        Issue: Billing issue with subscription
        
        Is this correct?

USER: Actually, I should probably go with my maiden name.
      My account is registered under Rodriguez.

SYSTEM: [Soft Reset Triggered]
        [Correction pattern detected - updating names]
        [Escalation Score: 0.35 - LOW]
        
        Let me start fresh to make sure we have the right information.
        
        I remember:
        Email: amanda.garcia@email.com
        Phone: 555-555-1234
        
        Can you tell me which name your account uses?

USER: Rodriguez. That's the original registration name.

SYSTEM: [Low-confidence field detected: last_name (confidence: 0.62)]
        
        Before we continue, I want to double-check this detail.
        
        You mentioned your name as: Amanda Rodriguez
        Is that the correct account name?

USER: No, wait. My account is under the married name - Garcia.
      But I also use Rodriguez sometimes.

SYSTEM: [User rejecting the reverification and providing correction]
        
        What name would you like me to use for this case?
        Please let me know if it's Garcia or Rodriguez.

USER: Use Garcia. That's the current name.

SYSTEM: [Confidence updated to 0.95]
        [Moving on]
        
        Perfect. So your account is under:
        Name: Amanda Garcia
        Email: amanda.garcia@email.com
        Phone: 555-555-1234
        Issue: Billing issue with subscription
        
        Is everything correct now?

USER: Yes, all correct.

SYSTEM: Thank you! Your billing issue case has been escalated to 
        our Finance team. They will investigate your subscription 
        charges and contact you within 24 hours.
        
        Case Reference: BL-2024-0892
```

---

## Scenario 6: Multiple Reversifications + Failed Extraction → Escalation

```
USER: I need to report a product quality issue

SYSTEM: I'm here to help. What is your name?

USER: David Chen

SYSTEM: Thank you David. What's your email?

USER: d-chen-1995@gmail.com

SYSTEM: And your phone?

USER: It's uh... 555... hmm, let me think.
      Is it 555-312-4567? Or 555-312-5678?
      Actually I think it might be 555-321-4567

SYSTEM: [Low confidence: 0.58]
        Let me note that as 555-312-4567
        
        What was the product you ordered?

USER: A coffee maker

SYSTEM: [All fields collected]
        
        Here's what I have:
        Name: David Chen
        Email: d-chen-1995@gmail.com
        Phone: 555-312-4567
        Product: Coffee maker
        Issue: Quality issue
        
        Is this correct?

USER: No, my phone is wrong. It's definitely 555-321-4567

SYSTEM: [Soft Reset Triggered]
        [Preserves: Name, Email, Low-conf Phone, Product]
        
        Let me start fresh with the correct information.
        
        I have your name and email saved. Let me verify the phone.
        
        You mentioned phone as: 555-321-4567
        Is that correct?

USER: Actually, no. It's 555-321-5678

SYSTEM: [Reverify attempt 1 - User rejects and provides correction]
        
        So your phone number is: 555-321-5678
        Is that correct?

USER: No wait, I need to check my phone. 
      Umm... I think it's 555-312-7654?

SYSTEM: [Reverify attempt 2 - User unsure/vague]
        
        What is the correct phone number?
        Please provide it clearly so we can move forward.

USER: Ugh, I don't remember! This is frustrating!

SYSTEM: [Reverify attempt 2 - Exceeds max attempts (2)]
        [Sentiment: FRUSTRATION DETECTED]
        [Escalation Score: 0.65 - MEDIUM-HIGH]
        
        I understand this is frustrating. Let's take a different approach.
        
        Could you provide:
        1. Your complete name
        2. Email address
        3. Order number (if you have it)
        4. Phone number
        
        Just state it all clearly and we'll get this resolved.

USER: Okay fine. It's David Chen, d-chen-1995@gmail.com,
      Order12345, and the phone is 555-321-5678

SYSTEM: [New extraction from comprehensive input]
        [High confidence reestablished]
        
        Perfect! Here's the complete summary:
        
        Name: David Chen
        Email: d-chen-1995@gmail.com
        Phone: 555-321-5678
        Order: Order12345
        Product: Coffee maker
        Issue: Quality issue
        
        Is this correct?

USER: Yes!

SYSTEM: Excellent! Your product quality case has been recorded.
        
        Case Number: PQ-2024-4521
        Our Quality Assurance team will review your coffee maker 
        and contact you at 555-321-5678 within 48 hours with options
        for replacement or refund.
```

---

## Scenario 7: Explicit Correction During Reverification

```
USER: I have a shipping issue

SYSTEM: I'd like to help. What's your name?

USER: Patricia Lee

SYSTEM: Patricia, what's your email address?

USER: pat.lee@domain.org

SYSTEM: And your phone?

USER: The person who answered said "five five five dash 
      two two eight dash eight nine nine nine" so I think 
      that's 555-228-8999

SYSTEM: [Low confidence: 0.64 - Spoken number, not verified]
        
        When was your package supposed to arrive?

USER: March 15th

SYSTEM: [All fields collected]
        
        Let me confirm:
        Name: Patricia Lee
        Email: pat.lee@domain.org
        Phone: 555-228-8999
        Expected Delivery: March 15th
        Issue: Shipping issue
        
        Is this correct?

USER: The phone number is definitely wrong. It should be 
      555-228-8989. I have one extra 9 that shouldn't be there.

SYSTEM: [Soft Reset Triggered]
        [Low-confidence field: phone (0.64)]
        
        Let me verify the phone number.
        
        You mentioned: 555-228-8999
        Is that correct?

USER: No, it needs to be changed to 555-228-8989 - 
      remove one 9 from the end

SYSTEM: [Explicit correction detected and applied]
        [Confidence updated to 0.95]
        [Moving forward]
        
        Got it. Your phone is: 555-228-8989
        
        Here's the updated summary:
        Name: Patricia Lee
        Email: pat.lee@domain.org
        Phone: 555-228-8989
        Expected Delivery: March 15th
        Issue: Shipping issue
        
        Is everything correct now?

USER: Perfect!

SYSTEM: Thank you! Your shipping case has been filed.
        
        Case ID: SH-2024-7834
        Status: ACTIVE - Tracking investigation
        
        Our Logistics team will locate your package and provide 
        you with an update by tomorrow morning. We'll reach you at 
        555-228-8989 or pat.lee@domain.org.
```

---

## Scenario 8: Vague Responses During Reverification

```
USER: I want to report a damaged item

SYSTEM: I'll help you with that. What is your name?

USER: Thomas Wilson

SYSTEM: What's your email address?

USER: thomas@emailprovider.net

SYSTEM: And your phone number?

USER: 555... 666... I dunno, somewhere around there

SYSTEM: [Very low confidence: 0.42]
        Let me note that as 555-666-0000
        
        What item arrived damaged?

USER: It was... like... some kind of electronics thing

SYSTEM: [All fields collected with low confidence overall]
        
        Here's what I have:
        Name: Thomas Wilson
        Email: thomas@emailprovider.net
        Phone: 555-666-0000
        Item: Electronics
        Issue: Damaged
        
        Is this correct?

USER: Um... kind of? But not really...

SYSTEM: [Soft Reset]
        
        Let me start fresh. I have your name and email.
        
        I noted your phone as: 555-666-0000
        Is that correct?

USER: Not really sure. Maybe?

SYSTEM: [Vague response detected - treating as rejection]
        
        What is your actual phone number? 
        It will help us contact you about this case.

USER: 555-777-8888

SYSTEM: [Correction applied - Confidence updated to 0.95]
        [Continuing with clearer information]
        
        And what specifically was the electronics item that arrived damaged?
        For example: laptop, phone, headphones, etc.

USER: A laptop

SYSTEM: Perfect! Here's the complete summary:
        
        Name: Thomas Wilson
        Email: thomas@emailprovider.net
        Phone: 555-777-8888
        Item: Laptop
        Issue: Arrived damaged
        
        Is this correct?

USER: Yes, that's right!

SYSTEM: Thank you Thomas! Your damaged laptop case has been recorded.
        
        Case Number: DM-2024-5431
        Priority: HIGH - Electronics damage claim
        
        We will arrange a replacement laptop and coordinate 
        pickup of the damaged unit. You'll hear from us at 
        555-777-8888 within 12 hours.
```

---

## Scenario 9: Risk Indicators Detected → Immediate Escalation

```
USER: I was assaulted by one of your employees at the store!

SYSTEM: [CRITICAL ALERT - Risk indicator detected: "assaulted"]
        [Sentiment: HIGH - Distress & Trauma]
        [Escalation Score: 0.89 - CRITICAL]
        
        I'm very sorry to hear that. This is a serious matter that 
        requires immediate attention from our management team.
        
        I'm connecting you to a supervisor right now who can 
        help you and take an incident report.
        
        Can you provide your name while I transfer you?

USER: Yes, it's Lisa Martinez

SYSTEM: Thank you Lisa. You're being connected to our Store Manager 
        immediately. They have full authority to address this situation.
        
        This is not being handled by an automated system. A real person 
        will be with you in seconds.

---

[HUMAN MANAGER CONNECTS IMMEDIATELY]

MANAGER: Lisa, this is Store Manager Robert Chen. I've been alerted 
         to your situation. I sincerely apologize. I'm going to personally 
         ensure this is investigated immediately.
         
         Where are you calling from?
```

---

## Scenario 10: Handover After Collection Complete

```
USER: I'm having ongoing technical support issues 
      and I've already contacted you three times this week

SYSTEM: I understand your frustration. Let me help document this.
        What is your name?

USER: Can I just talk to someone? Like a real human?

SYSTEM: [Explicit human request detected]
        [Escalation Policy: Immediate handover on explicit request]
        
        Absolutely, I understand. I'm connecting you to a 
        senior support agent right now who has full access 
        to your account history.
        
        Please hold...

---

[SENIOR SUPPORT AGENT CONNECTS]

AGENT: Hello, this is Jennifer from our Senior Support Team. 
       I can see that you've contacted us three times this week 
       about technical issues. I sincerely apologize for the 
       inconvenience.
       
       Let me pull up your full history and we'll get this resolved 
       permanently today. 
       
       What's your name?

USER: Tom Bradley

AGENT: Hi Tom! I have your account open. I can see the previous tickets.
       Let me review what happened and work on a permanent fix for you...
```

---

## Key Flow Indicators in Conversations

### ✅ **System Successfully Detects:**
- ✓ Low-confidence field extractions
- ✓ User frustration/distress
- ✓ Soft reset triggers
- ✓ Escalation signals
- ✓ Risk indicators (assault, threats, violence)
- ✓ Explicit correction patterns
- ✓ Vague/uncertain responses
- ✓ Human agent requests
- ✓ Correction loops
- ✓ Maximum attempt limits

### 🔄 **Reverification Flow:**
1. System detects low-confidence field (< 0.80)
2. After soft reset, asks: "Is [field] = [value] correct?"
3. User response options:
   - ✓ **"Yes"** → Confidence boosted to 0.95, move to next
   - ✗ **"No" alone** → Ask "What is the correct value?"
   - ⚠️ **"No, it's X"** → Apply correction, boost to 0.95
   - ❓ **Vague** → Treat as rejection, ask for value

### 🚨 **Escalation Triggers:**
- Explicit requests: "Can I talk to a human?"
- High distress + sentiment
- Correction count exceeds field count
- Risk keywords detected
- Reverification attempts exceed 2
- Escalation score ≥ 0.75

### 🔄 **Soft Reset Behavior:**
- **Preserves:** All entity values, language, sentiment
- **Clears:** Attempt counts, correction tracking, field attempts
- **Effect:** User retells issue, system doesn't re-ask already-extracted data
- **Special:** Re-verifies only low-confidence fields

