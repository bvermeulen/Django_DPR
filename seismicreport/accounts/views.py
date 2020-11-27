from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .models import Home


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
        return self.request.user
