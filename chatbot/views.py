from django.shortcuts import render, redirect
from .models import ChatSession, Message

def home(request):
    # 1. Find the active session (or make one if the database is totally empty)
    session = ChatSession.objects.first()
    if not session:
        session = ChatSession.objects.create()

    # 2. If the user clicked "Send" (a POST request)
    from django.shortcuts import render, redirect
from .models import ChatSession, Message

def home(request):
    session = ChatSession.objects.first()
    if not session:
        session = ChatSession.objects.create()

    if request.method == 'POST':
        user_text = request.POST.get('user_input')
        
        if user_text:
            # 1. Save the user's message
            Message.objects.create(session=session, sender='user', text=user_text)
            
            # 2. Generate a fake AI response (for now!)
            ai_reply = f"I heard you say: '{user_text}'. I am getting ready to process your documents soon!"
            
            # 3. Save the AI's message
            Message.objects.create(session=session, sender='ai', text=ai_reply)
            
            return redirect('home')

    chat_messages = session.messages.all()
    context = {
        'chat_messages': chat_messages
    }
    return render(request, 'index.html', context)

    # 3. Load the page normally (Displaying the history)
    chat_messages = session.messages.all()
    context = {
        'chat_messages': chat_messages
    }
    return render(request, 'index.html', context)