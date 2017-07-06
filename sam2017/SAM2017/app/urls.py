from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
        url(r'^$', views.index, name='index'),
        url(r'^register/$', views.RegisterUser.as_view(), name='user_register'),
        url(r'^chg/$', views.ChangePassword.as_view(), name='chg_pwd'),
        url(r'^updateprofile/$', views.UpdateProfile.as_view(), name='update_profile'),
        url(r'^login/$', views.user_login, name='login'),
        url(r'^upload/$', login_required(views.UploadPaper.as_view()), name='upload'),
        url(r'^reupload/$', views.reupload_paper, name='reupload'),
        url(r'^(?P<paper_id>[0-9]+)/assign/$', views.assign, name='assign'),
        url(r'^(?P<paper_id>[0-9]+)/download/$', views.download, name='download'),
        url(r'^logout/$', views.user_logout, name='logout'),
        url(r'^handle_notification/$', views.handle_notification),
        url(r'^(?P<paper_id>[0-9]+)/wishlist/$', views.pcm_wish_list, name='wishlist'),
        url(r'^(?P<paper_id>[0-9]+)/pcmreview/$', views.pcm_review, name='pcm_review'),
        url(r'^(?P<paper_id>[0-9]+)/pccreview/$', views.pcc_review, name='pcc_review'),
        url(r'^(?P<paper_id>[0-9]+)/report/$', views.report, name='report')
]
