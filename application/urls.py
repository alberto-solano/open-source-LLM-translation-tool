"""
URL configuration for application project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path(
        "media/translated_documents/<str:filename>",
        views.serve_translated_document,
        name="serve_translated_document",
    ),
    path("", views.home, name="home"),
    path("translator/", views.upload_document, name="translator"),
    path(
        "translation-interface/",
        views.translation_interface,
        name="translation_interface",
    ),
    path(
        "delete_all_translations/",
        views.delete_all_translations,
        name="delete_all_translations",
    ),
    path("detect_language/", views.detect_language, name="detect_language"),
]
