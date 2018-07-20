from django.shortcuts import render_to_response


def error403(request):
    return render_to_response('errors/huge_error.html', {'errno': 403})


def error500(request):
    return render_to_response('errors/huge_error.html', {'errno': 500})


def csrf_failure(request, reason=""):
    return render_to_response('errors/csrf.html')
