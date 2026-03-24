​🛡️ InvestSmart AI (Enterprise Edition)


​Compliance-Aware Investment Educator & RAG Engine


​InvestSmart AI is a high-fidelity Retrieval-Augmented Generation (RAG) platform designed for the financial and real estate sectors. It transforms complex investment prospectuses into clear, educational insights while maintaining a "Hard Wall" against providing unauthorized financial advice.


​🚀 Core Architecture: The Tri-Layer Defense


​To ensure institutional-grade safety, InvestSmart utilizes a multi-model approach powered by Google Gemini 1.5:




​Layer 0 (Intent Classifier): Uses Gemini 1.5 Flash to instantly detect and block prompts seeking financial advice, recommendations, or "jailbreak" attempts.


​Layer 1 (Contextual Reasoning): Uses Gemini 1.5 Pro to analyze the "Golden Source" (uploaded PDF) and provide factual, document-grounded answers.


​Layer 2 (Semantic Verifier): A final post-generation check to ensure the AI hasn't "hallucinated" guarantees or strayed into advisory territory.




​🌍 Glocalization: Market-Aware Personas


​InvestSmart features a "Market Context" toggle, allowing the AI to switch between:




​International Standard: Neutral, concise, and formal business English.


​Kenyan Localized: Professional English with local nuances (e.g., "Kindly note," "Tuko pamoja?") to build trust with local investors and SACCO members.




​🔐 Security & Privacy (Section 9 Compliance)




​Salted HMAC Logging: User interactions are hashed using session-specific salts. We store the "proof" of the interaction without storing raw, sensitive text.


​Crypto-Shredding: Users can instantly rotate session salts, rendering all historical audit logs mathematically irretrievable.


​Deterministic Guardrails: Hard-coded regex blocks for high-risk terms like "risk-free" or "guaranteed returns."




​🛠️ Technical Stack




​Frontend: Streamlit


​LLM Orchestration: Google Generative AI (Gemini 1.5 Pro/Flash)


​PDF Processing: PyPDF


​Security: HMAC-SHA256 & UUID Salt Rotation



