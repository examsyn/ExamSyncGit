# context_processors.py
def user_info(request):
    return {
        'user': request.user
    }
