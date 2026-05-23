def unread_messages_count(request):
    if request.user.is_authenticated:
        from books.models import Message
        count = Message.objects.filter(seller=request.user, is_read=False).count()
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}
