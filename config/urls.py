from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from apps.contact.views import contact
from apps.core import views as core
from apps.portfolio import views as portfolio

urlpatterns = [
    path("", core.accueil, name="accueil"),
    path("a-propos/", core.apropos, name="apropos"),
    path("projets/", portfolio.projets, name="projets"),
    path("projets/<slug:slug>/", portfolio.projet, name="projet"),
    path("competences/", portfolio.competences, name="competences"),
    path("parcours/", portfolio.parcours, name="parcours"),
    path("collaborations/", portfolio.collaborations, name="collaborations"),
    path("contact/", contact, name="contact"),
    path("pages/<slug:slug>/", core.page, name="page"),
    path("robots.txt", core.robots, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": core.PLANS}, name="sitemap"),
    path(settings.ADMIN_URL, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
