# -*- coding: utf-8 -*-
import os
import logging

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.http import Http404
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic.edit import FormView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from models import Sample
from models import SampleSource
from models import DownloadLog
from forms import SampleUploadForm
from forms import MalwarePublishForm
from forms import MalwareUpdateForm
from forms import MalwareFilterForm
from forms import SourceForm
from core.mixins import LoginRequiredMixin
from core.mongodb import get_compressed_file
from samples.utils import delete_sample


logger = logging.getLogger(__name__)


@login_required
def download(request, slug):
    try:
        malware = get_compressed_file('sha256', slug)
    except Exception as e:
        logger.debug(e)
        messages.error(request, 'Oops! We got an error!')
        return render(request, 'error.html')
    else:
        if malware:
            response = HttpResponse(malware.read())
            response['Content-Disposition'] = 'attachment; filename={}.zip'.format(slug)
            response['Content-Type'] = 'application/x-zip'
            DownloadLog(user=request.user, malware=slug).save()
            return response
        else:
            raise Http404


class MalwarePublishView(FormView):
    template_name = 'malware/publish.html'
    form_class = MalwarePublishForm
    success_url = reverse_lazy('malware.list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MalwarePublishView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        try:
            sha256 = self.kwargs['slug']
        except:
            return {}
        else:
            return {'malware': sha256}

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return form_class(
            **kwargs
        )

    def form_valid(self, form):
        form.save()
        return super(MalwarePublishView, self).form_valid(form)


class SampleUploadView(FormView, LoginRequiredMixin):

    """
    Sample upload view.
    """

    template_name = 'malware/upload.html'
    form_class = SampleUploadForm
    success_url = reverse_lazy('malware.upload')

    def get_form(self, form_class):
        """
        Get current user instance, and initialize the form class.
        """
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return form_class(**kwargs)

    def form_invalid(self, form):
        messages.info(
            self.request,
            "Your submission has not been saved. Try again."
        )
        return super(SampleUploadView, self).form_invalid(form)

    def form_valid(self, form):
        if form.save_sample():
            messages.info(self.request, 'Success!')
        else:
            messages.warning(self.request, 'Can not save sample!')
        return super(SampleUploadView, self).form_valid(form)


class MalwareUpdateView(UpdateView):
    template_name = 'malware/update.html'
    form_class = MalwareUpdateForm
    success_url = reverse_lazy('malware.list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # only owner of malware can update information
        obj = self.get_object()
        if obj.user != self.request.user:
            raise Http404
        return super(MalwareUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        return Sample.objects.get(slug=self.kwargs['slug'])


class MalwareListView(ListView, FormMixin):
    model = Sample
    template_name = 'malware/list.html'
    context_object_name = 'malwares'
    form_class = MalwareFilterForm
    success_url = reverse_lazy('malware.list')
    qs = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MalwareListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MalwareListView, self).get_context_data(**kwargs)
        context['filter'] = MalwareFilterForm()
        return context

    def get_queryset(self):
        if self.qs is not None:
            return self.qs
        return super(MalwareListView, self).get_queryset()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            self.qs = form.get_queryset()
        return self.get(request, *args, **kwargs)


class MalwareDeleteView(DeleteView):
    model = Sample
    template_name = 'malware/delete.html'
    success_url = reverse_lazy('malware.list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # only owner of malware can delete malware
        obj = self.get_object()
        if obj.user != self.request.user:
            raise Http404
        return super(MalwareDeleteView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        return Sample.objects.get(slug=self.kwargs['slug'])

    def delete(self, request, *args, **kwargs):
        delete_sample(self.kwargs['slug'])
        return super(MalwareDeleteView, self).delete(request, *args, **kwargs)


class MalwareProfileView(DetailView, LoginRequiredMixin):
    model = Sample
    template_name = 'malware/profile.html'
    context_object_name = 'malware'

    def get_object(self, **kwargs):
        return Sample.objects.get(slug=self.kwargs['slug'])


class SourceCreateView(CreateView, LoginRequiredMixin):
    model = SampleSource
    template_name = 'source/create.html'
    form_class = SourceForm
    fields = ['name', 'link', 'descr']
    success_url = reverse_lazy('source.list')

    def form_valid(self, form):
        # Save the user
        form.instance.user = self.request.user
        return super(SourceCreateView, self).form_valid(form)


class SourceUpdateView(UpdateView):
    template_name = 'source/update.html'
    form_class = SourceForm
    fields = ['name', 'link', 'descr']
    success_url = reverse_lazy('source.list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # user can only update their source
        obj = self.get_object()
        if obj.user != self.request.user:
            raise Http404
        return super(SourceUpdateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        return self.model.objects.get(slug=self.kwargs['slug'], user=self.request.user)


class SourceListView(ListView, LoginRequiredMixin):
    model = SampleSource
    template_name = 'source/list.html'
    context_object_name = 'malware_sources'

    def get_queryset(self):
        # user can only see their source
        return self.model.objects.filter(user=self.request.user)


class SourceDeleteView(DeleteView):
    model = SampleSource
    template_name = 'source/delete.html'
    success_url = reverse_lazy('source.list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # user can only delete their source
        obj = self.get_object()
        if obj.user != self.request.user:
            raise Http404
        return super(SourceDeleteView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        return self.model.objects.get(slug=self.kwargs['slug'], user=self.request.user)


class SourceProfileView(DetailView):
    model = SampleSource
    template_name = 'source/profile.html'
    context_object_name = 'malware_source'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # user can only see their source
        obj = self.get_object()
        if obj.user != self.request.user:
            raise Http404
        return super(SourceProfileView, self).dispatch(*args, **kwargs)

    def get_object(self, **kwargs):
        return self.model.objects.get(slug=self.kwargs['slug'], user=self.request.user)