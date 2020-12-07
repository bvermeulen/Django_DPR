from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.shortcuts import render
from django.views.generic import UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from seismicreport.utils.plogger import Logger
from seismicreport.utils.get_ip import get_client_ip
from .models import Home

logger = Logger.getlogger()


def home_page(request):
    welcome_text = ''
    welcome_image = None
    member_text = ''
    member_image = None
    try:
        welcome_text = Home.objects.last().welcome_text
        welcome_image = Home.objects.last().welcome_image
        member_text = Home.objects.last().member_text
        member_image = Home.objects.last().member_image

    except AttributeError:
        pass

    context = {'welcome_image': welcome_image,
               'welcome_text': welcome_text,
               'member_image': member_image,
               'member_text': member_text,
               'daily_id': 0,
              }

    return render(request, 'accounts/home.html', context)


@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'email', )
    template_name = 'accounts/my_account.html'
    success_url = reverse_lazy('home')

    def get_object(self):  #pylint: disable=arguments-differ
        logger.info(
            f'user: {self.request.user.username} (ip: {get_client_ip(self.request)}) '
            f'is updating account'
        )
        return self.request.user


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    # in tests there is no attribute user
    try:
        logger.info(
            f'user: {request.user.username} (ip: {get_client_ip(request)}) has logged in'
        )

    except AttributeError:
        pass


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    # in tests there is no attribute user
    try:
        logger.info(
            f'user: {request.user.username} (ip: {get_client_ip(request)}) has logged out'
        )

    except AttributeError:
        pass


@receiver(user_login_failed)
def user_login_failed_callback(sender, request, credentials, **kwargs):
    try:
        username = credentials["username"]

    except KeyError:
        username = ''

    logger.info(
        f'login failed for user: {username} (ip: {get_client_ip(request)})'
    )
