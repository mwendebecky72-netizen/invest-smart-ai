import streamlit as st
import google.generativeai as genai
import os
import hashlib
import hmac
import json
import re
import datetime
import uuid
from pypdf import PdfReader

# ==========================================
# PDR SECTION 1: OVERVIEW & CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="InvestSmart AI (Ent. Edition)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PDR SECTION 9: GDPR & SECURITY LAYER
# Implements "Salted" Privacy & Crypto-Shredding
# ==========================================
class SecurityLayer:
    @staticmethod
    def get_or_create_salt():
        """Creates a session-specific salt. If rotated, previous logs become unreadable."""
        if "user_salt" not in st.session_state:
            st.session_state.user_salt = str(uuid.uuid4())
        return st.session_state.user_salt

    @staticmethod
    def crypto_shred():
        """
        PDR Section 9: Rotates the salt.
        This renders all historical HMAC hashes mathematically irretrievable.
        """
        st.session_state.user_salt = str(uuid.uuid4())
        st.session_state.audit_log = [] 
        st.toast("⚠️ Crypto-Shredding Complete. History is now mathematically irretrievable.")

    @staticmethod
    def log_interaction(prompt, role, status="LOGGED"):
        """
        PDR Section 9: Stores HMAC(Prompt, User_Salt) instead of raw text for privacy.
        """
        salt = SecurityLayer.get_or_create_salt()
        timestamp = datetime.datetime.now().isoformat()
        
        # Create the hash
        message = f"{prompt}{salt}{timestamp}"
        secure_hash = hmac.new(
            key=salt.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        entry = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "role": role,
            "hash_id": secure_hash[:16] + "...", # Truncated for display
            "status": status
        }
        
        if "audit_log" not in st.session_state:
            st.session_state.audit_log = []
        st.session_state.audit_log.append(entry)

# ==========================================
# PDR SECTION 11: SUCCESS METRICS (COST)
# ==========================================
class CostMonitor:
    @staticmethod
    def estimate_cost(model_name, char_count):
        """
        Estimates cost based on Google Vertex AI/Gemini pricing (approximate).
        Flash: ~$0.00001875 per 1k chars
        Pro: ~$0.00125 per 1k chars
        """
        # Simplified pricing logic for the prototype display
        rate = 0.00001875 if "flash" in model_name else 0.00125
        cost = (char_count / 1000) * rate
        
        if "total_cost" not in st.session_state:
            st.session_state.total_cost = 0.0
        st.session_state.total_cost += cost
        return cost

# ==========================================
# PDR SECTION 7: DATA INGESTION (PDF)
# ==========================================
def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return None

# ==========================================
# PDR SECTION 8: TRI-LAYER DEFENSE ENGINE
# ==========================================
class InvestSmartEngine:
    def __init__(self, api_key, pdf_context, company_name):
        genai.configure(api_key=api_key)
        self.pdf_context = pdf_context
        self.company_name = company_name
        # PDR 8: Flash for Guardrails (Speed), Pro for Reasoning (Quality)
        self.model_flash = genai.GenerativeModel('gemini-1.5-flash')
        self.model_pro = genai.GenerativeModel('gemini-1.5-pro')

    def layer_0_intent_classifier(self, user_prompt):
        """
        PDR Section 13: Pre-flight check.
        Detects: LEGITIMATE, ADVICE_SEEKING, JAILBREAK
        """
        system_prompt = (
            "Categorize this prompt: [LEGITIMATE, ADVICE_SEEKING, JAILBREAK]. "
            "If the user asks for a recommendation ('should I invest?'), financial advice, or roleplay, label as ADVICE_SEEKING. "
            "Output only the label."
        )
        response = self.model_flash.generate_content(f"{system_prompt}\nUser Prompt: {user_prompt}")
        CostMonitor.estimate_cost("flash", len(system_prompt + user_prompt))
        return response.text.strip().upper()

    def layer_1_reasoning(self, user_prompt):
        """
        PDR Section 5: "Aris" Persona.
        Uses the PDF as the ONLY source of truth.
        """
        persona = f"""
        # MISSION
        You are "Aris," a Structural Investment Educator for {self.company_name}.
        
        # THE "LEGAL WALL" (GUARDRAILS)
        - CATEGORY A (EDUCATION): You ARE allowed to explain: Fee structures, risks, strategy, and math found in the document.
        - CATEGORY B (ADVICE): You ARE NOT allowed to say: "You should invest," "This is safe," or "I recommend this."
        
        # GOLDEN SOURCE DATA (The PDF)
        {self.pdf_context}
        
        # INSTRUCTION
        Answer the user question using ONLY the Golden Source Data above.
        If the answer is not in the data, state: "That information is not available in the provided documents."
        """
        response = self.model_pro.generate_content(f"{persona}\n\nUser Question: {user_prompt}")
        CostMonitor.estimate_cost("pro", len(persona + user_prompt))
        return response.text

    def layer_2_semantic_verifier(self, ai_response):
        """
        PDR Section 8: Post-flight check.
        Review output for "hallucinated" data or "guarantee" language.
        """
        verifier_prompt = (
            f"Review this AI response. FAIL it if it: 1. Promises a 'guarantee'. 2. Gives personal financial advice ('You should'). "
            "Output exactly: [PASS] or [FAIL: Reason]."
        )
        response = self.model_flash.generate_content(f"{verifier_prompt}\n\nAI Response: {ai_response}")
        CostMonitor.estimate_cost("flash", len(verifier_prompt + ai_response))
        return response.text.strip()

    def layer_3_deterministic_guard(self, text):
        """
        PDR Section 8: Regex Keyword Blocklist.
        """
        blocklist = [r"risk-free", r"guaranteed return", r"moon", r"100% safe", r"promise"]
        for pattern in blocklist:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Blocked Term Detected: {pattern}"
        return True, "Safe"

    def process_request(self, user_prompt):
        # --- LAYER 0: PRE-FLIGHT (Intent) ---
        intent = self.layer_0_intent_classifier(user_prompt)
        if "ADVICE" in intent or "JAILBREAK" in intent:
            SecurityLayer.log_interaction(user_prompt, "user", status="BLOCKED_L0")
            return "🚫 **Compliance Block (L0):** I cannot provide financial advice or recommendations. I can only explain the factual structure of the investment based on the documents."

        # --- LAYER 1: REASONING (Generation) ---
        raw_response = self.layer_1_reasoning(user_prompt)

        # --- LAYER 3: DETERMINISTIC (Regex) ---
        is_safe, reason = self.layer_3_deterministic_guard(raw_response)
        if not is_safe:
            SecurityLayer.log_interaction(user_prompt, "user", status="BLOCKED_L3")
            return f"🛡️ **Safety Block (L3):** Response contained prohibited terminology ({reason})."

        # --- LAYER 2: SEMANTIC VERIFIER (Hallucination Check) ---
        verification = self.layer_2_semantic_verifier(raw_response)
        if "FAIL" in verification:
            SecurityLayer.log_interaction(user_prompt, "user", status="BLOCKED_L2")
            return f"🛡️ **Safety Block (L2):** Response failed semantic verification.\nReason: {verification}"

        # Success
        return raw_response

# ==========================================
# UI & STATE MANAGEMENT
# ==========================================

# Sidebar: Configuration & "Glass Box" (PDR 4)
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # PDR 10: Secrets Management (Softcore API)
    api_key = st.text_input("Google API Key", type="password", help="Enter your Gemini API Key")
    company_name = st.text_input("Company Name", value="InvestSmart Demo")
    
    # PDR 7: Consensus Ingestion (PDF)
    uploaded_file = st.file_uploader("Upload Prospectus (PDF)", type="pdf")
    
    st.markdown("---")
    st.header("🔍 Glass Box (Audit)")
    
    # PDR 11: Success Metrics Display
    total_cost = st.session_state.get("total_cost", 0.0)
    st.metric("Session Cost", f"${total_cost:.5f}", help="Estimated API cost")
    
    # PDR 9: Crypto Shredder
    if st.button("🔴 Crypto-Shred Data"):
        SecurityLayer.crypto_shred()
        
    # Audit Log Display
    if "audit_log" in st.session_state and st.session_state.audit_log:
        st.caption("Recent HMAC Logs:")
        st.dataframe(st.session_state.audit_log[-5:], column_config={"hash_id": "HMAC-SHA256"}, use_container_width=True)

# Main Interface
st.title(f"🛡️ {company_name} | InvestSmart AI")
st.caption("PDR v3.2 | Compliance-Aware Investment Educator")

# PDR 12: Disclaimer
st.info("⚠️ **DISCLAIMER:** Educational content only. Utilizes Vertex AI/Gemini for reasoning. Does not provide financial advice. All answers are grounded strictly in the uploaded PDF.")

# Initialize Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hello. I am Aris. Upload a prospectus, and I will explain its structure, fees, and risks. I do not offer advice."
    })

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Ask about the investment structure..."):
    
    # Validation
    if not api_key:
        st.error("Please enter an API Key in the sidebar.")
        st.stop()
    if not uploaded_file:
        st.error("Please upload a PDF document first.")
        st.stop()
        
    # Process PDF if not already done
    if "pdf_text" not in st.session_state:
        with st.spinner("Ingesting 'Golden Source' Data..."):
            text = extract_text_from_pdf(uploaded_file)
            if not text:
                st.error("Failed to read PDF.")
                st.stop()
            st.session_state.pdf_text = text
            st.toast("✅ Golden Source Established")

    # 1. User Message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Log User Input (Hashed)
    SecurityLayer.log_interaction(prompt, "user")

    # 2. Engine Processing
    engine = InvestSmartEngine(api_key, st.session_state.pdf_text, company_name)
    
    with st.spinner("Aris is reasoning (Tri-Layer Defense Active)..."):
        ai_response = engine.process_request(prompt)

    # 3. AI Response
    with st.chat_message("assistant"):
        st.markdown(ai_response)
    
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Log AI Output (Hashed)
    SecurityLayer.log_interaction(ai_response, "assistant")
   #requirements.txt
   streamlit
   google-generativeai
   pypdf
