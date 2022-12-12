from django.http import HttpResponse


# Главная страница
def index(request):    
    return HttpResponse('ГЛАВНАЯ СТРАНИЦА')


def group_posts(request, slug):
    return HttpResponse('СТРАНИЦА GROUP_POSTS')
