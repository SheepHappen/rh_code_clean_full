from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from company.models import CompanyAssessment, CompanyFund


class DashboardView(LoginRequiredMixin, View):
    template_name = "dashboard.html"

    def get(self, request, *args, **kwargs):
        user = self.request.user
        assessments = None
        if hasattr(user, 'userprofile'):
            if user.userprofile.company:
                search_term = request.GET.get('searchTerm', None)
                # assessments = CompanyAssessment.objects.filter(
                #     created_by__userprofile__company__name=user.userprofile.company.name,
                #     is_latest=True
                # )
                assessments = CompanyAssessment.objects.filter(
                    created_by__userprofile__company__name=user.userprofile.company.name,
                ).select_related('created_by').select_related(
                    'company_fund'
                ).select_related('custom_risk_score').prefetch_related('industries').prefetch_related('countries')

                if search_term:
                    assessments = assessments.filter(company_name=search_term)

                    if not assessments:
                        messages.add_message(request, messages.INFO, "Assessments with {} not found please try another search term".format(search_term))

                if assessments:
                    sort_by = request.GET.get('sortBy', 'Most recent')

                    if sort_by == 'Company name':
                        assessments = assessments.order_by('company_name')
                    if sort_by == 'Most recent':
                        assessments = assessments.order_by('-date_updated')
                    if sort_by == 'Fund':
                        assessments = assessments.filter(company_fund__isnull=False).order_by('company_fund__name')

        if not assessments:
            initial_card_text = {
                'heading': "You don't have any activity yet",
                'text': 'Reports will be displayed here so you can easily access them or pick up where you left off',
                'button_text': 'Company assessment'
            }
        else:
            locations = []
            industries = []

            sort_options = ['Most recent', 'Company name', 'Fund']
            funds = user.userprofile.company.companyfund_set.all()

            for assessment in assessments:
                assessment.fund_options = []

                if assessment.status == 'C' or assessment.deal_type == 'P':
                    locations = locations + [country.name for country in assessment.countries.all()]
                    industries = industries + [industry.name for industry in assessment.industries.all()]

            assessment_location_count = len(list(set(locations)))
            assessment_industry_count = len(list(set(industries)))

        return render(request, self.template_name, locals())


def add_fund_to_assessment(request):
    if request.user.is_anonymous:
        raise Http404("page does not exist")

    assessment_id = request.POST.get('assessment')
    fund_id = request.POST.get('selectedFund')

    assessment = get_object_or_404(
        CompanyAssessment,
        created_by__userprofile__company=request.user.userprofile.company,
        id=assessment_id
    )

    if fund_id and fund_id != 'delete-me':
        fund = get_object_or_404(
            CompanyFund,
            company=request.user.userprofile.company,
            id=fund_id
        )
        assessment.company_fund = fund
    else:
        assessment.company_fund = None

    assessment.save()

    return HttpResponse('success')
