import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        total_pages = math.ceil(total_items / self.get_page_size(self.request)) if self.get_page_size(self.request) else 1

        return Response({
            'success': True,
            'message': 'Data retrieved successfully',
            'data': {
                'count': total_items,
                'total_pages': total_pages,
                'current_page': self.page.number,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
                'results': data
            }
        })

