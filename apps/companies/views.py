from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Company
from .serializers import CompanySerializer
from .permissions import IsCompanyRecruiterOrReadOnly
from apps.accounts.models import UserRole
from apps.common.utils import api_response

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = (IsCompanyRecruiterOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('industry', 'location', 'company_size')
    search_fields = ('name', 'description', 'industry', 'location')
    ordering_fields = ('name', 'created_at', 'founded_year')

    def get_queryset(self):
        return Company.objects.all().select_related('recruiter').annotate(
            active_jobs_count=Count('jobs', filter=Q(jobs__status='PUBLISHED'), distinct=True)
        )

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            success=True,
            data=serializer.data,
            message="Company details retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        if request.user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
            return api_response(
                success=False,
                message="Only recruiters can create a company profile.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_response(
            success=True,
            data=serializer.data,
            message="Company created successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(
            success=True,
            data=serializer.data,
            message="Company updated successfully"
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_company(self, request):
        company = Company.objects.filter(recruiter=request.user).first()
        if not company:
            return api_response(
                success=False,
                data=None,
                message="No company found for this recruiter.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(company)
        return api_response(
            success=True,
            data=serializer.data,
            message="Company retrieved successfully"
        )

