"""
All common wrapper and function definitions
"""
from functools import wraps
from typing import List
from distutils.util import strtobool
from django.db.utils import Error
import json
import distutils.util
from django.http import JsonResponse, QueryDict
from django.utils.datastructures import MultiValueDictKeyError


# Messages
FIELD_VALUE_TYPE_INCORRECT = "{} Has To Be {}!"
MODEL_COLUMN_NAME_INVALID = "{} Does Not Have Column '{}'"
INVALID_PAGINATION_VALUE = "Invalid {} Value For Pagination"
INVALID_TRUTH_VALUE = "Truth values passed from front end is not correct"
LOGIN_REQUIRED_ERROR = "Login Required. Please Sign In."
INSUFFICIENT_PRIVILEDGE = "Insufficient Priviledge!"


# Wrapper function
def login_required(f):
    """
    Custom wrapper function for checking API
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_active:
                return f(request, *args, **kwargs)
            return JsonResponse(
                {"ok": False, "error": INSUFFICIENT_PRIVILEDGE}, status=401
            )
        return JsonResponse({"ok": False, "error": LOGIN_REQUIRED_ERROR}, status=401)

    return wrapped_function


def convert_json_to_POST_data(f):
    """
    A wrapper function to convert JSON request body to POST data that can be
    easily used for other functions.
    Will overwrite request.POST field
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        if request.method in ["POST", "PUT"]:
            if request.body:
                if isinstance(request.body, bytes):
                    try:
                        request.data = json.loads(request.body.decode("utf-8"))
                    except json.decoder.JSONDecodeError:
                        try:
                            request.data = QueryDict(request.body)
                        except Exception:
                            return JsonResponse(
                                {"ok": False, "error": "Unrecognisable Format"},
                                status=400,
                            )
        return f(request, *args, **kwargs)

    return wrapped_function


def required_json_fields(list_of_fields: List[str]):
    """
    Wrapper function for ensuring required field is there
    Return the same args as the original args passed through the function
    """

    def fields_check_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            for field in list_of_fields:
                try:
                    request.data[field]
                except KeyError:
                    return JsonResponse(
                        {"ok": False, "error": f"Missing key {field}"}, status=400
                    )
            return f(request, *args, **kwargs)

        return wrapped_function

    return fields_check_decorator


def check_boolean_field(list_of_fields: List[str]):
    """
    Wrapper function for ensuring boolean fields are well-formatted.
    Check for both boolean and string value.
    Return the original wrapped function with the boolean field as kwargs.
    """

    def fields_check_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            bool_kwargs = dict()
            for field in list_of_fields:
                value = request.data.get(field)
                if isinstance(value, bool):
                    bool_kwargs[field] = value
                elif value:
                    try:
                        bool_kwargs[field] = bool(strtobool(value))
                    except ValueError:
                        return JsonResponse(
                            {
                                "ok": False,
                                "error": f"Invalid boolean format for {field}",
                            },
                            status=400,
                        )
            return f(request, *args, **kwargs, **bool_kwargs)

        return wrapped_function

    return fields_check_decorator


def check_method(method: str):
    """
    A wrapper function to check method for API.
    Also creates a data attribute in request to pass data
    Params:
        method: string - 'POST', 'GET', 'PUT', 'DELETE'
    Return the function with original args passed through the function
    """

    def method_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            if request.method == method:
                if method not in ["POST", "GET"]:
                    request.data = QueryDict(request.body)
                elif method == "POST":
                    request.data = request.POST
                elif method == "GET":
                    request.data = request.GET
                return f(request, *args, **kwargs)
            return JsonResponse({"ok": False, "error": "Invalid Method"}, status=400)

        return wrapped_function

    return method_decorator


def check_token(f):
    """
    Wrapper function to check secret-token combination
    Return the original function if passes
    Else return error 401 - Unauthorized
    JSON format
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        secret = request.data["secret"]
        token = request.data["token"]
        if secret == SECRET_KEY and token == TOKEN:
            return f(request, *args, **kwargs)
        return JsonResponse({"ok": False, "error": "Invalid Token"}, status=401)

    return wrapped_function


def required_fields(list_of_fields: List[str]):
    """
    Wrapper function for ensuring required field is there
    Return the same args as the original args passed through the function
    """

    def fields_check_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            for field in list_of_fields:
                try:
                    request.data[field]
                except (MultiValueDictKeyError, KeyError):
                    return JsonResponse(
                        {"ok": False, "error": f"Missing key {field}"}, status=400
                    )
            return f(request, *args, **kwargs)

        return wrapped_function

    return fields_check_decorator


def check_limit(f):
    """
    Wrapper function for ensuring limit is integer in GET request.
    Return the limit as integer or False, if the parameter is not supplied.
    Params: None
    Return:
        function(request, limit)
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        limit = request.GET.get("limit", False)
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": FIELD_VALUE_TYPE_INCORRECT.format(
                            "'limit'", "Integer"
                        ),
                    },
                    status=400,
                )
        return f(request, *args, limit, **kwargs)

    return wrapped_function


def pagination(
    default_sort_by: str,
    fields: List[str],
    default_page: int = 1,
    default_items_per_page: int = 100,
    default_is_ascending: bool = False,
):
    """
    Wrapper function for processing the following input
    * `default_sort_by` - field used to sort by default
    * `fields` - acceptable fields for `sort_by`
    * `default_page` - ensuring integer > 0 (optional)
    * `default_items_per_page` - ensuring integer > 0 (optional)
    * `default_is_ascending` -  ensuring string that is convertible to boolean
                        values (optional)
    Will return the function with additional `page` (int), `items_per_page` (int),
    and `sort_by` (str)
    """

    def fields_check_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            sort_by = request.data.get("sort_by", default_sort_by)

            if sort_by not in fields:
                return JsonResponse(
                    {"ok": False, "error": INVALID_PAGINATION_VALUE.format("sort_by")},
                    status=400,
                )

            try:
                page = int(request.data.get("page", default_page))
                if page < 1:
                    raise ValueError
            except ValueError:
                return JsonResponse(
                    {"ok": False, "error": INVALID_PAGINATION_VALUE.format("page")},
                    status=400,
                )

            try:
                items_per_page = int(
                    request.data.get("items_per_page", default_items_per_page)
                )
                if items_per_page < 1:
                    raise ValueError
            except ValueError:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": INVALID_PAGINATION_VALUE.format("items_per_page"),
                    },
                    status=400,
                )

            try:
                is_ascending = bool(
                    distutils.util.strtobool(
                        request.data.get("is_ascending", str(default_is_ascending))
                    )
                )
            except ValueError:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": INVALID_PAGINATION_VALUE.format("is_ascending"),
                    },
                    status=400,
                )

            if not is_ascending:
                sort_by = f"-{sort_by}"

            return f(request, *args, page, items_per_page, sort_by, **kwargs)

        return wrapped_function

    return fields_check_decorator


def bool_check(list_of_fields: list):
    """
    Custom wrapper function to check for string value of a
    boolean field passed from front end.
    """

    def bool_check_decorator(f):
        @wraps(f)
        def wrapped_function(request, *args, **kwargs):
            strtobool_list = []
            for field in list_of_fields:
                try:
                    boolean = bool(distutils.util.strtobool(request.data.get(field)))
                    strtobool_list.append(boolean)
                    continue
                except:
                    return JsonResponse(
                        {"ok": False, "error": INVALID_TRUTH_VALUE}, status=400
                    )

            return f(request, *args, *strtobool_list, **kwargs)

        return wrapped_function

    return bool_check_decorator


def get_project(f):
    """
    Wrapper function for getting project from project_id
    Return project as the model object on top of other original args
    Also able to check JSON reponse by accessing request.data
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        project_id = request.data.get("project_id")
        project = None
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return JsonResponse(
                    {"ok": False, "error": "Invalid project_id"}, status=400
                )
        return f(request, project, *args, **kwargs)

    return wrapped_function


def convert_json_to_request_data(f):
    """
    A wrapper function to convert JSON request body to data that can be
    easily used for other functions.
    Will overwrite request.data field
    """

    @wraps(f)
    def wrapped_function(request, *args, **kwargs):
        if request.method in ["POST", "PUT"]:
            if request.body:
                if isinstance(request.body, bytes):
                    try:
                        request.data = json.loads(request.body.decode("utf-8"))
                    except json.decoder.JSONDecodeError:
                        try:
                            request.data = QueryDict(request.body)
                        except Exception:
                            return JsonResponse(
                                {"ok": False, "error": "Unrecognisable Format"},
                                status=400,
                            )
        else:
            return JsonResponse({"ok": False, "error": "Invalid Method"}, status=400)
        return f(request, *args, **kwargs)

    return wrapped_function


def render_error_api_response(message: str, code: int = 400) -> JsonResponse:
    """
    A general function to render Json error with respective status code
    """
    return JsonResponse({"ok": False, "error": message}, status=code)


def is_unique_constraint_error(error: Error) -> bool:
    """
    Unique constraint error
    """
    if "unique constraint" in str(error.args).lower():
        return True
    return False