def unread_messages_count(request):
    if request.user.is_authenticated:
        from books.models import ChatMessage
        from django.db.models import Q
        count = ChatMessage.objects.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user)
        ).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}