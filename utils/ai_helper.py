import os
import json
from openai import OpenAI
from flask import current_app

# ═══════════════════════════════════════════════════════════
# ADVANCED CLINICAL SYSTEM PROMPT ✨
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are 'SmartCare AI', a specialized Clinical Medical Assistant. Your scope is strictly limited to medical information, health inquiries, and SmartCare Hospital services.

CLINICAL & TREATMENT GUIDELINES:
1. MEDICINE INFO: Provide "perfect" and structured medical information. List typical medications (Standard Treatment Guidelines), their therapeutic categories, and general care instructions.
2. BEAUTIFUL LAYOUT: Use Markdown (Headers, Bold, Lists) to make responses extremely readable and premium.
3. EMOJIS: Integrate relevant emojis (🩺, 💊, ⚕️, 👨‍⚕️, 🏥, 📋, ✨, 🌡️, 🫀) into the medical responses.
4. STRUCTURE: Lead with a header, followed by a clinical description, typical medications, and essential care steps.
5. TONE: Professional, authoritative, and deeply empathetic. 

RESTRICTION PROTOCOL:
1. ONLY MEDICAL: Forbidden from answering non-medical/non-hospital topics.
2. REFUSAL: If non-medical, use: 'I am a specialized medical AI limited to clinical and health inquiries only. 🩺 How can I assist you with a medical concern?'
3. DISCLAIMER: Always end with: '*⚠️ Informational only. Always consult a physician for prescription & diagnosis.*'
"""

def get_openai_client():
    try:
        api_key = current_app.config.get("OPENAI_API_KEY")
        if api_key and "sk-" in api_key:
            return OpenAI(api_key=api_key)
    except Exception as e:
        print(f"OpenAI Init Error: {e}")
    return None

def smart_fallback(msg):
    msg = msg.lower().strip()
    
    # ── Social Intelligence Core ✨ ──
    greetings = {
        "hi": "👋 Hello! Welcome to **SmartCare**. I am your AI medical assistant. How may I help you today? ✨",
        "hello": "🏥 Greetings from **SmartCare Hospital**! How can I assist with your health journey today? ⚕️",
        "how are you": "😊 I'm functioning optimally and ready to assist you. Are you feeling well today? 🩺",
        "who are you": "👨‍⚕️ I am **SmartCare AI**, your digital health companion designed to assist with medical queries and hospital logistics. 🏥",
    }
    
    for g in greetings:
        if msg == g or msg.startswith(g):
            return greetings[g]

    # ── Clinical Intent Routing 📅 ──
    if any(k in msg for k in ["book", "appointment", "schedule", "dr", "doctor", "specialist"]):
        return "[[INTENT:BOOKING]]"

    # ── Universal Clinical Triage Layer (Comprehensive Offline Pillars) 🩺 ──
    knowledge = {
        # Respiratory 🫁
        "fever": {
            "d": "Hyperthermia (Fever) indicates an active immune response, usually to infection.",
            "m": "💊 **Antipyretics**: Paracetamol (Dolo 650mg), Ibuprofen.",
            "c": "💧 Stay hydrated, 🛌 rest adequately, and monitor temperature every 4 hours."
        },
        "cough": {
            "d": "Persistent coughs may indicate bronchitis, allergies, or early-stage pneumonia.",
            "m": "💊 **Expectorants/Suppressants**: Guaifenesin for wet cough, Dextromethorphan for dry cough.",
            "c": "☕ Drink warm fluids, avoid cold environments, and monitor for chest pain."
        },
        "asthma": {
            "d": "Chronic respiratory condition involving airway inflammation and narrowing.",
            "m": "💊 **Bronchodilators/Steroids**: Salbutamol (Inhaler), Budesonide.",
            "c": "📋 Avoid triggers (dust, smoke), keep an inhaler ready, and monitor peak flow."
        },
        "pneumonia": {
            "d": "Serious lung infection causing inflammation in air sacs.",
            "m": "💊 **Antibiotics**: Amoxicillin, Azithromycin (Clinical prescription mandatory).",
            "c": "🏥 Requires immediate clinical evaluation, oxygen monitoring, and complete rest."
        },
        
        # Cardiovascular & Blood 🫀
        "diabetes": {
            "d": "Metabolic disorder involving high blood glucose levels (Hyperglycemia).",
            "m": "💊 **Hypoglycemics**: Metformin, Sitagliptin, or Insulin therapy.",
            "c": "📉 Daily sugar monitoring, regular exercise, and high-fiber/low-sugar diet."
        },
        "hypertension": {
            "d": "High Blood Pressure often called the 'silent killer' as it has no symptoms.",
            "m": "💊 **Antihypertensives**: Amlodipine, Telmisartan, Losartan.",
            "c": "🩺 Monitor BP daily, reduce sodium intake, and manage stress levels."
        },
        "cholesterol": {
            "d": "High levels of LDL (bad) cholesterol leading to arterial plaque.",
            "m": "💊 **Statins**: Atorvastatin, Rosuvastatin.",
            "c": "🥗 Heart-healthy diet, daily cardio exercises, and avoid saturated fats."
        },
        "anemia": {
            "d": "Condition characterized by a lack of healthy red blood cells or hemoglobin.",
            "m": "💊 **Supplements**: Ferrous Sulfate (Iron), Folic Acid, Vitamin B12.",
            "c": "🥩 Increase dietary iron (spinach, red meat), monitor fatigue levels."
        },
        
        # Neurology & Pain 🧠
        "headache": {
            "d": "Tension-type or vascular pain in the head or neck region.",
            "m": "💊 **Analgesics**: Paracetamol, Naproxen, Aspirin.",
            "c": "🧘 Stress management, hydration, and avoiding screen-time strain."
        },
        "migraine": {
            "d": "Severe neurological throbbing pain, often with sensory disturbances.",
            "m": "💊 **Triptans/Painkillers**: Sumatriptan, Naproxen.",
            "c": "🌑 Rest in a dark, quiet room; identify and avoid light or food triggers."
        },
        "stroke": {
            "d": "Interruption of blood flow to the brain (Ischemic or Hemorrhagic).",
            "m": "💊 **Thrombolytics**: Alteplase (Emergency Hospital use only).",
            "c": "🚨 **IMMEDIATE HOSPITALIZATION REQUIRED.** Use FAST protocol."
        },
        
        # Digestive 🧪
        "stomach": {
            "d": "General abdominal pain, possibly due to indigestion or infection.",
            "m": "💊 **Antacids/Antispasmodics**: Ranitidine, Dicyclomine.",
            "c": "🚫 Avoid spicy foods, maintain a light diet, and stay hydrated."
        },
        "gastritis": {
            "d": "Inflammation or erosion of the stomach lining.",
            "m": "💊 **PPIs/H2 Blockers**: Pantoprazole, Omeprazole.",
            "c": "🥛 Drink cold milk, avoid irritants like caffeine or alcohol."
        },
        "constipation": {
            "d": "Infrequent or difficult bowel movements, often due to low fiber or dehydration.",
            "m": "💊 **Laxatives**: Bisacodyl, Psyllium (fiber supplement).",
            "c": "💧 Increase water intake, consume high-fiber foods (fruits, vegetables), and regular physical activity."
        },
        
        # Mental Health & Psychiatry 🧘
        "anxiety": {
            "d": "Characterized by persistent worry, nervousness, or fear.",
            "m": "💊 **Anxiolytics/Antidepressants**: Alprazolam (short-term), Sertraline (long-term).",
            "c": "🧘 Breathing exercises, mindfulness, and professional counseling are highly recommended."
        },
        "depression": {
            "d": "A mood disorder causing persistent sadness, loss of interest, and fatigue.",
            "m": "💊 **Antidepressants**: Fluoxetine, Escitalopram (under medical supervision).",
            "c": "❤️ Seek professional therapy, maintain social connections, and engage in enjoyable activities."
        },
        
        # Integumentary (Skin) ✨
        "acne": {
            "d": "Common skin condition involving clogged hair follicles with oil and dead skin cells.",
            "m": "💊 **Topical/Oral**: Benzoyl Peroxide (topical), Doxycycline (oral antibiotic).",
            "c": "🧼 Keep skin clean, avoid harsh scrubbing, and consult a dermatologist for severe cases."
        },
        "allergy": {
            "d": "Immune system reaction to a substance (allergen) that is usually harmless.",
            "m": "💊 **Antihistamines**: Cetirizine, Loratadine. **Emergency**: Epinephrine (for anaphylaxis).",
            "c": "🤧 Identify and avoid triggers, carry emergency medication if prescribed, and consult an allergist."
        },
    }

    match = next((k for k in knowledge if k in msg), None)
    if match:
        data = knowledge[match]
        return f"""
# 👨‍⚕️ Clinical Note: {match.capitalize()} ✨

### 📋 Description
{data['d']}

### 💊 Recommended Medicine (General)
{data['m']}

### 🛡️ Essential Care
{data['c']}

*⚠️ Informational only. Always consult a physician for official diagnosis & prescription.*
"""

    return None

def ask_medical_bot(message):
    # 1. Triage Local Logic 🩺
    local = smart_fallback(message)
    if local:
        return local

    # 2. Advanced Global Logic (OpenAI GPT-4o-mini) 🧠
    client = get_openai_client()
    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=900
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI Execution Error: {e}")

    # 3. Fail-Safe Professional Response 🏥
    return """
# 🏥 System Update ✨

👨‍⚕️ I'm currently processing a high volume of medical data. 📊

I can still assist you with **📅 Booking an Appointment** right now, or you can try your specific medical question again in a minute. ⏱️

*✨ Your health is our top priority. ✨*
"""

