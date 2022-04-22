from django.http import JsonResponse
from db.models import Feedback
from db.serializer import FeedbackSerializer
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def get_feedback(request):
	feedbacks = Feedback.objects.all()
	serializer = FeedbackSerializer(feedbacks, many=True)
	return JsonResponse(
		{
			"ok": True,
			"data" : serializer.data
		}
	)