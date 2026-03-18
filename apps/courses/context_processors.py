def document_counts(request):
    """
    Provide Normal Staff sidebar counts globally.
    Avoids having to pass saved_documents in every view.
    """
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return {}
    if not getattr(user, 'is_normal_staff', False):
        return {}
    try:
        from .models import SavedDocument
        return {'saved_documents': SavedDocument.objects.filter(user=user).count()}
    except Exception:
        return {}

