from django.urls import path
from . import feedback

urlpatterns = [
	path("get_feedback", feedback.get_feedback, name="get_feedback")
]