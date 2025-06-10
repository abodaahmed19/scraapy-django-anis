from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('media/<str:foldername>/<str:filename>', ProtectedDocumentView.as_view(), name='media'),
    path('', DocumentList.as_view(), name='document-list'),
    path('user-documents/', UserDocumentList.as_view(), name='user-document-list'),
    # path('choices/', DocumentListChoices.as_view(), name='document-choices'),
]
