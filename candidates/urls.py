from django.urls import path
from . import views

urlpatterns = [
    path('add-candidates-manually/', views.add_candidates_manually, name='add_candidates_manually'),
    path('add-candidates-pdf/', views.add_candidates_pdf, name='add_candidates_pdf'),
    path('your-candidates/', views.your_candidates, name='your_candidates'),
    path('candidate/<slug:slug>/', views.candidate_detail, name='candidate_detail'),
    path('candidate/<slug:slug>/edit/', views.edit_candidate, name='edit_candidate'),
    path('candidate/<slug:slug>/delete/', views.delete_candidate, name='delete_candidate'),
    path('save-test/<slug:slug>/', views.save_test_to_candidate, name='save_test_to_candidate'),
    path('create-candidate-from-test/', views.create_new_candidate_from_test, name='create_new_candidate_from_test'),
    path('find-matching-candidate/', views.find_matching_candidate, name='find_matching_candidate'),
    path('save-summary-to-existing/', views.save_summary_to_existing, name='save_summary_to_existing'),
    path('save-summary-as-new/', views.save_summary_as_new_candidate, name='save_summary_as_new_candidate'),
]