from .models import Category

def default(request):
    categories = Category.objects.all()

    return dict(categories=categories)