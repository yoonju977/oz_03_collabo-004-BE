from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Article
from ..serializers import ArticleListSerializer, ArticleSerializer


# 게시글 좋아요(두번 누르면 삭제)
class ArticleLikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        article_id = kwargs.get("id")
        article = get_object_or_404(Article, id=article_id)
        user = request.user

        # 작성자가 자신의 게시글에 좋아요를 할 수 없도록 함
        if article.user == user:
            return Response(
                {"message": "게시글 작성자는 좋아요를 누를 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user in article.likes.all():
            article.likes.remove(user)
            message = "Like removed"
        else:
            article.likes.add(user)
            message = "Like added"

        response_data = {
            "article_id": article_id,
            "like_count": article.like_count,
            "message": message,
        }
        return Response(response_data, status=status.HTTP_200_OK)


# 조회수 로직: 세션 기반으로 중복 방지
class ArticleViewCountView(APIView):

    def get(self, request, *args, **kwargs):
        article_id = kwargs.get("id")
        article = Article.objects.get(id=article_id)

        session_key = f"viewed_article_{article_id}"
        if not request.session.get(session_key, False):
            article.view_count += 1
            article.save()
            request.session[session_key] = True

        serializer = ArticleSerializer(article)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TopLikedArticlesView(APIView):
    """
    like_count 기준 상위 5개의 게시글을 반환하는 API
    """

    def get(self, request, *args, **kwargs):
        # likes 필드를 Count로 집계하여 like_count를 생성하고 이를 기준으로 정렬
        top_articles = Article.objects.annotate(like_count=Count("likes")).order_by(
            "-like_count"
        )[:5]
        # 시리얼라이저로 직렬화
        serializer = ArticleListSerializer(top_articles, many=True)
        # 응답 반환
        return Response(serializer.data, status=status.HTTP_200_OK)
