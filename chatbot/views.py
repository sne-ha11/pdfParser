import os
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from .models import ChatSession, Message, Document

# Import the AI libraries
import google.generativeai as genai
from openai import OpenAI
from groq import Groq
import cohere
from huggingface_hub import InferenceClient

load_dotenv()

# --- INITIALIZE ALL CLIENTS ---
# 1. Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# 2. OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

# 3. Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

# 4. Cohere
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY")) if os.getenv("COHERE_API_KEY") else None

# 5. Mistral (Using the OpenAI Client as a secret tunnel!)
mistral_client = OpenAI(
    api_key=os.getenv("MISTRAL_API_KEY"),
    base_url="https://api.mistral.ai/v1"
) if os.getenv("MISTRAL_API_KEY") else None

# 6. Hugging Face
hf_client = InferenceClient(token=os.getenv("HUGGINGFACE_API_KEY")) if os.getenv("HUGGINGFACE_API_KEY") else None

from pypdf import PdfReader # <-- Add this import at the very top of your views.py file!

def home(request):
    # Get or create the active chat session
    session = ChatSession.objects.first()
    if not session:
        session = ChatSession.objects.create()

    if request.method == 'POST':
        # 1. Handle Model Switching
        new_model = request.POST.get('ai_model')
        if new_model:
            request.session['selected_model'] = new_model
            return redirect('home')

        # 2. HANDLE NEW PDF UPLOADS
        if request.FILES.get('pdf_file'):
            uploaded_file = request.FILES['pdf_file']
            
            # Save to database
            doc = Document.objects.create(session=session, file=uploaded_file)
            
            try:
                # Open and read the PDF text
                reader = PdfReader(doc.file.path)
                extracted_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
                
                # Create a system message informing the chat about the file
                short_name = uploaded_file.name
                alert_text = f"[System: Uploaded and read file '{short_name}'. Context updated with {len(extracted_text)} characters of text. You can now ask questions about this document!]"
                Message.objects.create(session=session, sender='user', text=alert_text)
                
                # Optional: Have the AI automatically acknowledge the upload
                active_brain = request.session.get('selected_model', 'gemini')
                ai_ack = f"I have successfully scanned and indexed '{short_name}'! What specific information, definitions, or code snippets would you like me to look up from it?"
                Message.objects.create(session=session, sender='ai', text=ai_ack)
                
            except Exception as e:
                Message.objects.create(session=session, sender='ai', text=f"System Error reading PDF: {str(e)}")
                
            return redirect('home')

        # 3. Handle Regular Chat Messages
        user_text = request.POST.get('user_input')
        if user_text:
            # Look up if this session has any uploaded document texts to inject as reference
            context_payload = ""
            associated_docs = session.documents.all()
            if associated_docs.exists():
                context_payload = "--- REFERENCE DOCUMENT DATA ---\n"
                for doc in associated_docs:
                    try:
                        reader = PdfReader(doc.file.path)
                        for page in reader.pages:
                            t = page.extract_text()
                            if t: context_payload += t + "\n"
                    except:
                        pass
                context_payload += "--- END OF REFERENCE DATA ---\n\n"

            # Save user message to database
            Message.objects.create(session=session, sender='user', text=user_text)
            
            # Build final prompt combining the file data (if any) and the user question
            final_prompt = user_text
            if context_payload:
                final_prompt = f"{context_payload}Using the reference documents provided above, please answer this question: {user_text}"

            active_brain = request.session.get('selected_model', 'gemini')
            ai_reply = "System Error: Brain disconnected."
            
            try:
                # --- THE 6-WAY SWITCHBOARD ---
                if active_brain == 'gemini' and gemini_model:
                    response = gemini_model.generate_content(final_prompt)
                    ai_reply = response.text
                    
                elif active_brain == 'openai' and openai_client:
                    response = openai_client.chat.completions.create(
                        model="gpt-4o", messages=[{"role": "user", "content": final_prompt}]
                    )
                    ai_reply = response.choices[0].message.content
                    
                elif active_brain == 'groq' and groq_client:
                    response = groq_client.chat.completions.create(
                        model="llama3-8b-8192", messages=[{"role": "user", "content": final_prompt}]
                    )
                    ai_reply = response.choices[0].message.content
                    
                elif active_brain == 'cohere' and cohere_client:
                    response = cohere_client.chat(message=final_prompt, model="command-r-plus")
                    ai_reply = response.text
                    
                elif active_brain == 'mistral' and mistral_client:
                    response = mistral_client.chat.completions.create(
                        model="mistral-large-latest", messages=[{"role": "user", "content": final_prompt}]
                    )
                    ai_reply = response.choices[0].message.content
                    
                elif active_brain == 'huggingface' and hf_client:
                    response = hf_client.chat_completion(
                        messages=[{"role": "user", "content": final_prompt}], model="HuggingFaceH4/zephyr-7b-beta"
                    )
                    ai_reply = response.choices[0].message.content
                    
            except Exception as e:
                ai_reply = f"Error with {active_brain.upper()}: {str(e)}"
            
            Message.objects.create(session=session, sender='ai', text=ai_reply)
            return redirect('home')

    chat_messages = session.messages.all()
    return render(request, 'index.html', {'chat_messages': chat_messages})

    chat_messages = session.messages.all()
    return render(request, 'index.html', {'chat_messages': chat_messages})