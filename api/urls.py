"""
api/urls.py  —  All PlacePrep API routes
Imported by backend/urls.py under the /api/ prefix.

Final URLs:
  /api/auth/register/
  /api/auth/login/
  /api/auth/token/refresh/
  /api/auth/logout/
  /api/auth/profile/

  /api/placement/popular/
  /api/placement/company/<company_id>/
  /api/placement/company/<company_id>/cache/

  /api/skilltest/topics/
  /api/skilltest/generate/
  /api/skilltest/submit/<session_id>/
  /api/skilltest/attempts/
  /api/skilltest/leaderboard/

  /api/dev2dev/posts/
  /api/dev2dev/posts/<post_id>/
  /api/dev2dev/posts/<post_id>/like/
  /api/dev2dev/posts/<post_id>/comments/
  /api/dev2dev/posts/<post_id>/comments/<comment_id>/
  /api/dev2dev/posts/<post_id>/comments/<comment_id>/like/
  /api/dev2dev/posts/<post_id>/comments/<comment_id>/upvote/

  /api/dashboard/
"""

from django.urls import path
from api.views.auth_views import (
    RegisterView, LoginView, ProfileView,
)
from api.views.placement_views import (
    PopularCompaniesView, CompanyGuideView, CompanyCacheRefreshView,
)
from api.views.skilltest_views import (
    TopicsListView, GenerateTestView, SubmitSessionView,
    AttemptHistoryView, LeaderboardView,
)
from api.views.dev2dev_views import (
    PostListCreateView, PostDetailView, PostLikeView,
    CommentListCreateView, CommentDetailView,
    CommentLikeView, CommentUpvoteView,
)
from api.views.dashboard_views import DashboardView

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("auth/register/",      RegisterView.as_view(),     name="auth-register"),
    path("auth/login/",         LoginView.as_view(),         name="auth-login"),
    path("auth/profile/",       ProfileView.as_view(),       name="auth-profile"),

    # ── Placement (Gemini-powered company guides) ──────────────────────────────
    path("placement/popular/",                        PopularCompaniesView.as_view(),    name="placement-popular"),
    path("placement/company/<str:company_id>/",       CompanyGuideView.as_view(),        name="placement-company"),
    path("placement/company/<str:company_id>/cache/", CompanyCacheRefreshView.as_view(), name="placement-cache"),

    # ── SkillTest (dynamic Gemini MCQs) ───────────────────────────────────────
    path("skilltest/topics/",              TopicsListView.as_view(),    name="skilltest-topics"),
    path("skilltest/generate/",            GenerateTestView.as_view(),  name="skilltest-generate"),
    path("skilltest/submit/<str:session_id>/", SubmitSessionView.as_view(), name="skilltest-submit"),
    path("skilltest/attempts/",            AttemptHistoryView.as_view(), name="skilltest-attempts"),
    path("skilltest/leaderboard/",         LeaderboardView.as_view(),   name="skilltest-leaderboard"),

    # ── Dev2Dev (community Q&A) ───────────────────────────────────────────────
    path("dev2dev/posts/",                                          PostListCreateView.as_view(),   name="dev2dev-posts"),
    path("dev2dev/posts/<str:post_id>/",                            PostDetailView.as_view(),       name="dev2dev-post-detail"),
    path("dev2dev/posts/<str:post_id>/like/",                       PostLikeView.as_view(),         name="dev2dev-post-like"),
    path("dev2dev/posts/<str:post_id>/comments/",                   CommentListCreateView.as_view(), name="dev2dev-comments"),
    path("dev2dev/posts/<str:post_id>/comments/<str:comment_id>/",  CommentDetailView.as_view(),    name="dev2dev-comment-detail"),
    path("dev2dev/posts/<str:post_id>/comments/<str:comment_id>/like/",   CommentLikeView.as_view(),   name="dev2dev-comment-like"),
    path("dev2dev/posts/<str:post_id>/comments/<str:comment_id>/upvote/", CommentUpvoteView.as_view(), name="dev2dev-comment-upvote"),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]