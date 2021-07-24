"""
urls.py: contains the URL endpoints/ redirection to different views or services offered by campussim.
"""
from django.urls import include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'campus', campusTransCoeffViewSet)
router.register(r'sim', simResultsViewSet)

sim_result_rest = simResultsViewSet.as_view({
    'get':'retrieve',
})

urlpatterns = [
    re_path(r'^api/', include(router.urls)),

    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT, 'show_indexes': settings.DEBUG}),

    re_path(r'^$', IndexView.as_view(), name='index'),
    re_path(r'^about/$', AboutView.as_view(), name='about'),

    re_path(r'^user-activation/(?P<token>[\w-]+)$', user_activation, name="user_activation"),
    re_path(r'^user-password-reset/(?P<token>[\w-]+)$', user_password_reset, name="user_password_reset"),
    re_path(r'^login/$', LogInView.as_view(), name='login'),
    re_path(r'^logout/$', logout_view, name="logout"),
    re_path(r'^register/$', RegisterView.as_view(), name='register'),
    re_path(r'^forgotPassword/$', ForgottenPasswordView.as_view(), name='forgotPassword'),

    re_path(r'^profile/$', ProfileView.as_view(), name='profile'),
    re_path(r'^profile/activity/$', userActivityView.as_view(), name='userActivity'),
    re_path(r'^profile/edit/$', ProfileEditView.as_view(), name='profile_edit'),

    re_path(r'^campusData/add/$', addDataView.as_view(), name='campusData'),
    re_path(r'^campusData/delete/(?P<pk>\d+)/$', deleteDataView.as_view(), name='delCampusData'),
    re_path(r'^instantiation/delete/(?P<pk>\d+)/$', deleteInstantiationView.as_view(), name='deleteCampus'),

    re_path(r'^intervention/create/$', createIntervention.as_view(), name='createIntervention'),
    re_path(r'^intervention/update/(?P<pk>\d+)/$', updateIntervention.as_view(), name='updateIntervention'),
    re_path(r'^intervention/delete/(?P<pk>\d+)/$', deleteInterventionView.as_view(), name='deleteIntervention'),

    re_path(r'^simulation/create/$', createSimulationView.as_view(), name='createSimulation'),
    re_path(r'^simulation/delete/(?P<pk>\d+)/$', deleteSimulationView.as_view(), name='deleteSimulation'),
    re_path(r'^simulation/view/(?P<pk>\d+)/$', viewSimulationView.as_view(), name='viewSimulation'),
    re_path(r'^simulation/render/(?P<pk>\d+)/$', visualizeSingleSimulation.as_view(), name='visualizeSimulation'),
    re_path(r'^simulation/fetch/(?P<pk>\d+)/$', sim_result_rest, name='rest_sim_result'),
    re_path(r'^simulation/render/multiple/$', visualizeMultiSimulation.as_view(), name='visualizeMultiSimulations'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
