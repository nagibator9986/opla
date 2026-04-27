from django.urls import path

from apps.blog.views import BlogPostDetailView, BlogPostListView

urlpatterns = [
    path("", BlogPostListView.as_view(), name="blog-list"),
    path("<slug:slug>/", BlogPostDetailView.as_view(), name="blog-detail"),
]
