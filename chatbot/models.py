from django.db import models
import uuid

# Create your models here.



class ChatSession(models.Model):
    # This creates a unique, unguessable ID for every new chat window
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

class Message(models.Model):
    # This links the message to a specific ChatSession
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # This keeps track of who is talking
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    
    # This stores the actual chat text
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"