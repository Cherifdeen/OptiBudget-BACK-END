# Custom pagination class for cursor-based pagination
from rest_framework.pagination import CursorPagination
class CustomCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at' 
    page_size_query_param = 'page'  # pour que le client puisse changer la taille via URL
    max_page_size = 200