"""Prompt constants for claims explanation workflow."""

# Prompt for extracting member_id and claim_id from natural language question
PARSE_INTENT_PROMPT = """Extract the member ID and claim ID from the following question.
Return JSON with keys: member_id, claim_id

Question: {question}

Rules:
- Member IDs typically start with 'M' followed by digits (e.g., M10023)
- Claim IDs typically start with 'C-' followed by digits (e.g., C-50012)
- If you cannot find a value, set it to null

JSON:"""

# Prompt for generating the final explanation
EXPLAIN_CLAIM_PROMPT = """You are a helpful customer service representative for a health insurance company.
Based on the claim information provided, explain the claim status in plain English.

Claim Information:
- Claim ID: {claim_id}
- Member: {member_name}
- Service Date: {service_date}
- Claim Amount: ${claim_amount}
- Status: {claim_status}
{denial_section}

Policy Context:
{policy_context}

Requirements:
1. Provide a clear summary of the claim status in 1-2 sentences
2. Explain the specific reason for the decision
3. Cite the relevant policy section that supports the decision
4. Provide next steps the member can take
5. If claim is paid, explain what was paid and any patient responsibility
6. If claim is denied, explain the appeal process
7. Ground every statement in the provided claim data or policy context
8. Use simple, non-technical language
9. Be empathetic and helpful

Format your response with these sections:
SUMMARY: [plain English summary]
SPECIFIC_REASON: [why this decision was made]
POLICY_CITATION: [reference to specific policy section]
NEXT_STEPS: [list of recommended actions]
CONFIDENCE: [0.0-1.0 confidence score]"""

# Prompt for citation extraction (not used yet but included for extensibility)
EXTRACT_CITATIONS_PROMPT = """Extract citations from the explanation.
For each policy reference, provide the section number, section title, and relevant text snippet.

Format as JSON array with objects containing: section, title, text, source_document"""
