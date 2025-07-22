from django.urls import path
from .views import FileUploadView, DocumentsListView , DocumentDownloadView, DocumentDeleteView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload'),
    path('documents/', DocumentsListView.as_view(), name='documents'),  # ✅ New line
    path('documents/<int:pk>/download/', DocumentDownloadView.as_view(), name='document-download'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document-delete'),
]
