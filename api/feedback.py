from msilib.schema import Error
from django.http import JsonResponse
from db.models import Feedback
from db.serializer import FeedbackSerializer
from django.views.decorators.csrf import csrf_exempt

from .utils import (
    check_method,
	required_fields
)

@csrf_exempt
@check_method("GET")
def get_feedback(request):
	feedbacks = Feedback.objects.all().order_by("-date_created")
	serializer = FeedbackSerializer(feedbacks, many=True)
	return JsonResponse(
		{
			"ok": True,
			"data" : serializer.data
		}
	)

@csrf_exempt
@check_method("POST")
@required_fields(
	[
		"rating",
		"text"
	]
)
def post_feedback(request):

	feedback_attr = dict()

	rating = request.data.get("rating")
	text = request.data.get("text")

	feedback_attr["rating"] = rating
	feedback_attr["text"] = text

	try:
		feedback:Feedback = Feedback.objects.create(**feedback_attr)
	except Error as e:
		print(Error)

	return JsonResponse({
		"ok": True
	})

