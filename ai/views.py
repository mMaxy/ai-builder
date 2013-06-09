# Create your views here.
import multiprocessing

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import Context, RequestContext

from ai.forms import UploadFileForm
from ai.models import Network, SingleRun


def index(request):
    context = Context()
    return render(request, 'ai/index.html', context)


def details(request, nw_id):
    nw = get_object_or_404(Network, pk=nw_id)
    if nw.done:
        top3 = nw.getTop3()
        sr1 = get_object_or_404(SingleRun, pk=top3[0])
        sr2 = get_object_or_404(SingleRun, pk=top3[1])
        sr3 = get_object_or_404(SingleRun, pk=top3[2])
        return render(request, 'ai/details.html', {'network': nw, 'sr1': sr1, 'sr2': sr2, 'sr3': sr3})
    else:
        return render(request, 'ai/details.html', {'network': nw})


def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            network = Network(name=request.POST['title'], date=timezone.now(), inputs=request.FILES['file'])
            network.save()
            p = multiprocessing.Process(target=network.run, args=())
            p.start()
            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('ai.views.details', args=(network.id,)))
    else:
        form = UploadFileForm() # A empty, unbound form
        # Render list page with the documents and the form
    return render_to_response(
        'ai/upload.html',
        {'form': form},
        context_instance=RequestContext(request)
    )