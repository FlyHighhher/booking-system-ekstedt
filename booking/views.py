from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.db import models
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from .models import Booking, Table
from .forms import BookingForm
from datetime import date
from .messages import (
    BOOKING_SUCCESSFUL_CREATE,
    BOOKING_SUCCESSFUL_UPDATE,
    BOOKING_SUCCESSFUL_DELETE,
)
from django.contrib import messages

# Create your views here.
class HomePage(generic.TemplateView):
    template_name = "index.html"
    context_object_name = "homepage"

class MenuPage(generic.TemplateView):
    template_name = "menu.html"
    context_object_name = "menu"

class HistoryPage(generic.TemplateView):
    template_name = "history.html"
    context_object_name = "history"

class ContactPage(generic.TemplateView):
    template_name = "contact.html"
    context_object_name = "contact"

class BookingList(LoginRequiredMixin, generic.ListView):
    template_name = "bookings.html"
    context_object_name= "bookings"

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all().order_by('-date')
        else:
            return Booking.objects.filter(user=self.request.user).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = date.today()

        user_messages = messages.get_messages(self.request)
        context['user_messages'] = user_messages
        
        confirmed_bookings = Booking.objects.filter(
            user=self.request.user,
            status='Confirmed',
            date__gte=timezone.now().date()
        ).exists()

        if confirmed_bookings:
            messages.success(self.request, 'Your booking has been confirmed!')

        return context

class BookingDetail(generic.DetailView):
    model = Booking
    template_name = "details.html"


@method_decorator(login_required, name='dispatch')
class Profile(generic.DetailView):
    model = User
    template_name = "profile.html"
    context_object_name= "profile"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        past_bookings = Booking.objects.filter(
            user = self.request.user,
            date__lt=timezone.now().date()
        ).order_by('-date')

        context['past_bookings'] = past_bookings

        return context


class CreateBooking(generic.edit.CreateView):
    model = Booking
    form_class = BookingForm
    template_name = "create.html"
    success_url = reverse_lazy('booking:bookings')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.request = self.request
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user

        if not self.request.user.is_staff:
            today = timezone.now().date()
            if form.instance.date <= today:
                form.add_error('date', 'Tables can only be booked for future dates.')
                
        response = super().form_valid(form)

        messages.success(self.request, BOOKING_SUCCESSFUL_CREATE)

        return response

class UpdateBooking(generic.edit.UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = "update.html"
    success_url = reverse_lazy('booking:bookings')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.request = self.request
        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, BOOKING_SUCCESSFUL_UPDATE)

        return response

class DeleteBooking(generic.edit.DeleteView):
    model = Booking
    success_url = reverse_lazy('booking:bookings')
    template_name = "delete_booking.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(self.request, BOOKING_SUCCESSFUL_DELETE)

        return response