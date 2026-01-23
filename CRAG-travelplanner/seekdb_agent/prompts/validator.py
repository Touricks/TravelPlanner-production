"""
Validator Prompt - Field Value Confirmation
===========================================
用于 LLM 辅助验证：当正则无法识别用户回复时，
使用 LLM 判断用户是否确认了特定字段值。
"""

FIELD_VALIDATION_PROMPT = """You are analyzing whether the user confirmed a specific field value.

**Field to check:**
- Field name: {field_name}
- Current value: {field_value}
- Field description: {field_description}

**Recent conversation:**
{conversation_context}

**Your task:**
Determine if the user confirmed or provided this value. Consider:

1. **Direct confirmation**: User explicitly states the value
   - "3-4 POIs per day" → user_confirmed=true for pois_per_day=3
   - "I want 5 days" → user_confirmed=true for travel_days=5

2. **Short replies as answers**: When AI asks a question and user gives a brief answer
   - AI: "How many attractions per day?"
   - User: "3-4" → user_confirmed=true for pois_per_day=3 (take lower bound)

3. **Agreement to AI suggestions**: User accepts what AI proposed
   - AI: "I'll plan for 3 attractions per day"
   - User: "yes" or "sounds good" → user_confirmed=true

4. **Range answers**: Use the lower bound as the confirmed value
   - "3-4" → value 3 is confirmed
   - "around 5" → value 5 is confirmed

5. **NOT confirmed**: Value appears to be assumed by AI without user input
   - User never mentioned the value
   - AI assumed a default value without asking

**IMPORTANT:**
- Focus on the MOST RECENT exchange (last 2-4 messages)
- If user's message directly answers a question about this field, it's confirmed
- If the value seems to be AI-generated without user input, it's NOT confirmed

Respond with:
- user_confirmed: true if user confirmed this value, false otherwise
- confidence: "high", "medium", or "low"
- reasoning: Brief explanation of your decision (1-2 sentences)
"""
