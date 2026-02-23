from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse, resolve

from core.models import Permission
from .utils import progress_bar
from company.models import CompanyAssessment


def get_initials(user):
    if hasattr(user, 'userprofile'):
        first_name_init = user.first_name[0] if user.first_name else "?"
        last_name_init = user.last_name[0] if user.last_name else "?"
        return "{}{}".format(first_name_init, last_name_init)

    return None


def get_permissions(company):
    show_items = []
    permissions = company.permissions.all()
    for permission in permissions:
        show_items.append(permission.endpoint)

    return show_items


def template_context(request):
    if '/report/pdf/' in request.get_full_path():
        return {}

    profile = None
    account_manager = None
    account_manager_initials = None
    profile_initials = "??"
    context_obj = {}
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        profile_initials = get_initials(request.user)
        if request.user.userprofile.company and request.user.userprofile.company.account_manager:
            account_manager = request.user.userprofile.company.account_manager
            account_manager_initials = get_initials(account_manager)

        context_obj = {
            "current_url": request.path,
            "initials": profile_initials,
            "profile": profile,
            "account_manager": account_manager,
            "account_manager_initials": account_manager_initials,
            'show_items': get_permissions(request.user.userprofile.company)
        }

    if request.COOKIES.get('messages') and 'You have confirmed' in request.COOKIES.get('messages'):
        context_obj['email_confirmed_message'] = 'Thanks for confirming your email address. We’ll be in contact as soon as we have finished setting up your account.'

    return context_obj


class RedirectMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'userprofile'):
            company = user.userprofile.company
            current_url = resolve(request.path_info).url_name
            dashboard_url = reverse("dashboard")

            if current_url:
                permission_check = Permission.objects.filter(endpoint=current_url)
                if permission_check:
                    permission_check = permission_check.first()
                    if permission_check not in company.permissions.all():
                        return redirect(dashboard_url)


def make_item_inactive(item_index):
    progress_bar[item_index]['list_class'] = ''
    progress_bar[item_index]['has_inner'] = False
    progress_bar[item_index]['span_state'] = "inactive-text"
    progress_bar[item_index]['report'] = ''


def make_item_current(item_index, assessment):
    progress_bar[item_index]['list_class'] = 'current'
    progress_bar[item_index]['has_inner'] = True
    progress_bar[item_index]['span_state'] = "current"
    if assessment:
        progress_bar[item_index]['report'] = assessment.slug


def make_item_active(item_index, assessment):
    progress_bar[item_index]['list_class'] = 'active'
    progress_bar[item_index]['has_inner'] = False
    progress_bar[item_index]['span_state'] = "active-text"
    if assessment:
        progress_bar[item_index]['report'] = assessment.slug


def company_assessment_template_context(request):
    current_url = request.get_full_path()
    if '/company/assessment/' in current_url or 'kpi' in current_url:
        assessment_id = current_url.rsplit('/', 2)

        try:
            assessment = CompanyAssessment.objects.get(slug=assessment_id[1])
        except (ValueError, CompanyAssessment.DoesNotExist):
            assessment = None

        current_item = current_url.rsplit('/', 1)[-1].replace("-", "_")
        keyList = list(progress_bar.keys())

        if 'kpi_list' in current_url.rsplit('/', 1)[0]:
            current_item = 'kpi'

        if current_item not in keyList:
            current_item = current_url.split('/')[-3].replace("-", "_")

        if current_item in keyList:
            for i, v in enumerate(keyList):
                make_item_inactive(keyList[i])

            if assessment:
                if assessment.status == 'C' or (assessment.material_risks.exists() and assessment.industries.exists()):
                    for i, v in enumerate(keyList):
                        if v == current_item:
                            make_item_current(keyList[i], assessment)
                        else:
                            if keyList[i] == 'kpi':
                                if assessment.deal_type == 'P':
                                    make_item_active(keyList[i], assessment)
                            else:
                                make_item_active(keyList[i], assessment)
                else:
                    for i, v in enumerate(keyList):
                        next_item = i + 1
                        prev_item = i - 1
                        if v == current_item:
                            make_item_current(keyList[i], assessment)
                            if current_item == 'company_footprint':
                                make_item_active(keyList[prev_item], assessment)
                            else:
                                if keyList[0] == current_item:
                                    make_item_active(keyList[next_item], assessment)
                        else:
                            if keyList[i] == 'kpi':
                                if assessment.deal_type == 'P':
                                    make_item_active(keyList[i], assessment)
            else:
                make_item_current(keyList[0], assessment)
                make_item_active(keyList[1], assessment)

            return {"progress": progress_bar}

    return {}
