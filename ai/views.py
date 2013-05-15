# Create your views here.
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import loader, Context, RequestContext
from ai.forms import UploadFileForm
from ai.models import Network


def index(request):
    context = Context()
    return render(request, 'ai/index.html', context)


def details(request, nw_id):
    nw = get_object_or_404(Network, pk=nw_id)
    return render(request, 'ai/details.html', {'network': nw})


def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            network = Network(name=request.POST['title'], date=timezone.now(), inputs=request.FILES['file'])
            network.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('ai.views.upload'))
    else:
        form = UploadFileForm() # A empty, unbound form

    # Load documents for the list page
    networks = Network.objects.all()

    # Render list page with the documents and the form
    return render_to_response(
        'ai/upload.html',
        {'networks': networks, 'form': form},
        context_instance=RequestContext(request)
    )