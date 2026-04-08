"""
Tests for apps/media_files/views.py

Covers:
- MediaFileViewSet inherits from ApiModelViewSet
- queryset model is MediaFile
- default serializer class is MediaFileSerializer
- create action uses MediaFileUploadSerializer
- GET  /api/v1/media/       - public key ✓, internal key ✓
- GET  /api/v1/media/<id>/  - public key ✓, internal key ✓
- POST /api/v1/media/       - internal key ✓, public key ✗
- All methods rejected without auth header
- All methods rejected with a wrong key
- Response structure on list and detail
- Filtering
- Ordering
- Search
"""

import tempfile

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.media_files.models import MediaFile
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer
from apps.media_files.views import MediaFileViewSet


PUB_KEY = "pub-media-files-view-test-key"
INT_KEY = "int-media-files-view-test-key"


def int_headers():
    return {"HTTP_X_API_KEY": INT_KEY}


def pub_headers():
    return {"HTTP_X_API_KEY": PUB_KEY}


def wrong_headers():
    return {"HTTP_X_API_KEY": "completely-wrong-key"}


def results_list(response):
    return response.data.get("results", response.data)


def make_file(name="test.pdf", content=b"dummy", content_type="application/pdf"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content, content_type=content_type)


class TestMediaFileViewSetClass(TestCase):
    def test_inherits_from_api_model_viewset(self) -> None:
        assert issubclass(MediaFileViewSet, ApiModelViewSet)

    def test_queryset_model_is_media_file(self) -> None:
        assert MediaFileViewSet.queryset.model == MediaFile

    def test_default_serializer_class_is_media_file_serializer(self) -> None:
        assert MediaFileViewSet.serializer_class == MediaFileSerializer

    def test_get_serializer_class_returns_read_serializer_for_list(self) -> None:
        view = MediaFileViewSet()
        view.action = "list"
        assert view.get_serializer_class() == MediaFileSerializer

    def test_get_serializer_class_returns_upload_serializer_for_create(self) -> None:
        view = MediaFileViewSet()
        view.action = "create"
        assert view.get_serializer_class() == MediaFileUploadSerializer


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetList(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()

        self.a = MediaFile.objects.create(
            file=make_file("a.pdf"),
            original_name="a.pdf",
            mime_type="application/pdf",
            size_bytes=100,
        )
        self.b = MediaFile.objects.create(
            file=make_file("poster.png", content_type="image/png"),
            original_name="poster.png",
            mime_type="image/png",
            size_bytes=200,
        )

    def test_list_with_public_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/media/", **pub_headers())
        assert response.status_code == 200

    def test_list_with_internal_key_returns_200(self) -> None:
        response = self.client.get("/api/v1/media/", **int_headers())
        assert response.status_code == 200

    def test_list_without_auth_returns_401_or_403(self) -> None:
        response = self.client.get("/api/v1/media/")
        assert response.status_code in (401, 403)

    def test_list_with_wrong_key_returns_401_or_403(self) -> None:
        response = self.client.get("/api/v1/media/", **wrong_headers())
        assert response.status_code in (401, 403)

    def test_list_returns_all_media_files(self) -> None:
        response = self.client.get("/api/v1/media/", **pub_headers())
        assert len(results_list(response)) == 2

    def test_list_response_contains_expected_fields(self) -> None:
        response = self.client.get("/api/v1/media/", **pub_headers())
        item = results_list(response)[0]

        for field in (
            "id",
            "external_id",
            "file",
            "original_name",
            "mime_type",
            "size_bytes",
            "file_type",
            "uploaded_by",
            "created_at",
        ):
            with self.subTest(field=field):
                assert field in item


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetDetail(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.obj = MediaFile.objects.create(
            file=make_file("detail.pdf"),
            original_name="detail.pdf",
            mime_type="application/pdf",
            size_bytes=111,
        )

    def test_detail_with_public_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.obj.pk}/", **pub_headers())
        assert response.status_code == 200

    def test_detail_with_internal_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.obj.pk}/", **int_headers())
        assert response.status_code == 200

    def test_detail_without_auth_returns_401_or_403(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.obj.pk}/")
        assert response.status_code in (401, 403)

    def test_detail_returns_correct_object(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.obj.pk}/", **pub_headers())
        assert response.data["id"] == str(self.obj.pk)
        assert response.data["original_name"] == "detail.pdf"

    def test_detail_unknown_id_returns_404(self) -> None:
        response = self.client.get("/api/v1/media/00000000-0000-0000-0000-000000000000/", **pub_headers())
        assert response.status_code == 404


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetCreate(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @override_settings(MEDIA_ROOT=None)
    def test_create_with_internal_key_returns_201(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            response = self.client.post(
                "/api/v1/media/",
                {"file": make_file()},
                format="multipart",
                **int_headers(),
            )
        assert response.status_code == 201, getattr(response, "data", response.content)

    @override_settings(MEDIA_ROOT=None)
    def test_create_creates_object(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            response = self.client.post(
                "/api/v1/media/",
                {"file": make_file()},
                format="multipart",
                **int_headers(),
            )
        assert response.status_code == 201, getattr(response, "data", response.content)
        assert MediaFile.objects.count() == 1

    @override_settings(MEDIA_ROOT=None)
    def test_create_sets_metadata(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            response = self.client.post(
                "/api/v1/media/",
                {"file": make_file("poster.png", content_type="image/png")},
                format="multipart",
                **int_headers(),
            )

        assert response.status_code == 201, getattr(response, "data", response.content)

        obj = MediaFile.objects.get()
        assert obj.original_name == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_create_with_public_key_returns_401_or_403(self) -> None:
        response = self.client.post(
            "/api/v1/media/",
            {"file": make_file()},
            format="multipart",
            **pub_headers(),
        )
        assert response.status_code in (401, 403)

    def test_create_without_auth_returns_401_or_403(self) -> None:
        response = self.client.post(
            "/api/v1/media/",
            {"file": make_file()},
            format="multipart",
        )
        assert response.status_code in (401, 403)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetFiltering(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()

        self.pdf = MediaFile.objects.create(
            file=make_file("brochure.pdf"),
            original_name="brochure.pdf",
            mime_type="application/pdf",
            size_bytes=100,
        )
        self.png = MediaFile.objects.create(
            file=make_file("poster.png", content_type="image/png"),
            original_name="poster.png",
            mime_type="image/png",
            size_bytes=200,
        )

    def test_filter_by_file_type(self) -> None:
        response = self.client.get("/api/v1/media/?file_type=pdf", **pub_headers())
        assert len(results_list(response)) == 1

    def test_filter_by_mime_type(self) -> None:
        response = self.client.get("/api/v1/media/?mime_type=image/png", **pub_headers())
        assert len(results_list(response)) == 1

    def test_filter_by_original_name(self) -> None:
        response = self.client.get("/api/v1/media/?original_name=poster", **pub_headers())
        assert len(results_list(response)) == 1


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetOrdering(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()

        MediaFile.objects.create(
            file=make_file("large.pdf"),
            original_name="large.pdf",
            mime_type="application/pdf",
            size_bytes=300,
        )
        MediaFile.objects.create(
            file=make_file("small.pdf"),
            original_name="small.pdf",
            mime_type="application/pdf",
            size_bytes=100,
        )

    def test_ordering_by_size_bytes(self) -> None:
        response = self.client.get("/api/v1/media/?ordering=size_bytes", **pub_headers())
        sizes = [item["size_bytes"] for item in results_list(response)]
        assert sizes == sorted(sizes)


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetSearch(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()

        MediaFile.objects.create(
            file=make_file("poster.png", content_type="image/png"),
            original_name="poster.png",
            mime_type="image/png",
            size_bytes=100,
        )
        MediaFile.objects.create(
            file=make_file("doc.pdf"),
            original_name="doc.pdf",
            mime_type="application/pdf",
            size_bytes=100,
        )

    def test_search_by_filename(self) -> None:
        response = self.client.get("/api/v1/media/?search=poster", **pub_headers())
        assert len(results_list(response)) == 1

    def test_search_by_mime_type(self) -> None:
        response = self.client.get("/api/v1/media/?search=image", **pub_headers())
        assert len(results_list(response)) >= 1
        