from django.shortcuts import render


def index(request):
    """Simple view rendering the simulator index page."""
    return render(request, "simulator/index.html")
