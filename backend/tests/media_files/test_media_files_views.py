"""Tests for apps/media_files/views.py."""

import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.views import ApiModelViewSet
from apps.languages.models import Language
from apps.media_files.models import MediaFile, MediaFileTranslation
from apps.media_files.serializers import MediaFileSerializer, MediaFileUploadSerializer
from apps.media_files.views import MediaFileViewSet
from tests.helpers.api import internal_headers as int_headers
from tests.helpers.api import paginated_results as results_list
from tests.helpers.api import public_headers as pub_headers
from tests.helpers.api import wrong_headers

PUB_KEY = "pub-media-files-view-test-key"
INT_KEY = "int-media-files-view-test-key"


def make_file(
    name: str = "test.pdf",
    content: bytes = b"dummy",
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
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

    def test_get_serializer_class_returns_write_serializer_for_create(self) -> None:
        view = MediaFileViewSet()
        view.action = "create"
        assert view.get_serializer_class() == MediaFileUploadSerializer

    def test_get_serializer_class_returns_write_serializer_for_update(self) -> None:
        view = MediaFileViewSet()
        view.action = "update"
        assert view.get_serializer_class() == MediaFileUploadSerializer

    def test_get_serializer_class_returns_write_serializer_for_partial_update(self) -> None:
        view = MediaFileViewSet()
        view.action = "partial_update"
        assert view.get_serializer_class() == MediaFileUploadSerializer


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY, LANGUAGE_CODE="nl")
class TestMediaFileViewSetListAndDetail(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()
        self.nl = Language.objects.create(code="nl", name="Dutch", is_active=True)
        self.en = Language.objects.create(code="en", name="English", is_active=True)

        self.a = MediaFile.objects.create(file=make_file("a.pdf"))
        MediaFileTranslation.objects.create(
            media_file=self.a,
            language=self.nl,
            description="Algemene brochure",
        )
        MediaFileTranslation.objects.create(
            media_file=self.a,
            language=self.en,
            description="General brochure",
        )

        self.b = MediaFile.objects.create(file=make_file("poster.png", content_type="image/png"))
        MediaFileTranslation.objects.create(
            media_file=self.b,
            language=self.nl,
            description="Premièreposter",
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
            "filename",
            "display_description",
            "description",
            "mime_type",
            "size_bytes",
            "file_type",
            "created_at",
        ):
            with self.subTest(field=field):
                assert field in item

    def test_detail_with_public_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.a.pk}/", **pub_headers())
        assert response.status_code == 200

    def test_detail_with_internal_key_returns_200(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.a.pk}/", **int_headers())
        assert response.status_code == 200

    def test_detail_returns_correct_object(self) -> None:
        response = self.client.get(f"/api/v1/media/{self.a.pk}/", **pub_headers())
        assert response.data["id"] == str(self.a.pk)
        assert response.data["filename"] == "a.pdf"
        assert response.data["display_description"] == "Algemene brochure"
        assert response.data["description"] == {"nl": "Algemene brochure", "en": "General brochure"}

    def test_detail_unknown_id_returns_404(self) -> None:
        response = self.client.get("/api/v1/media/00000000-0000-0000-0000-000000000000/", **pub_headers())
        assert response.status_code == 404


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY)
class TestMediaFileViewSetCreateUpdateDelete(TestCase):
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
                {"file": make_file(), "external_id": "new-media"},
                format="multipart",
                **int_headers(),
            )
        assert response.status_code == 201, getattr(response, "data", response.content)

    @override_settings(MEDIA_ROOT=None)
    def test_create_creates_object_and_sets_metadata(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            response = self.client.post(
                "/api/v1/media/",
                {"file": make_file("poster.png", content_type="image/png"), "external_id": "poster-1"},
                format="multipart",
                **int_headers(),
            )

        assert response.status_code == 201, getattr(response, "data", response.content)
        assert MediaFile.objects.count() == 1

        obj = MediaFile.objects.get()
        assert obj.filename == "poster.png"
        assert obj.mime_type == "image/png"
        assert obj.file_type == MediaFile.FileType.IMAGE
        assert obj.external_id == "poster-1"

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

    @override_settings(MEDIA_ROOT=None)
    def test_create_rejects_mismatching_content_signature(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            response = self.client.post(
                "/api/v1/media/",
                {
                    "file": make_file(
                        "poster.png",
                        content=b"%PDF-1.7 fake",
                        content_type="image/png",
                    )
                },
                format="multipart",
                **int_headers(),
            )
        assert response.status_code == 422
        pointers = [error["pointer"] for error in response.data.get("errors", [])]
        assert "/file" in pointers

    @override_settings(MEDIA_ROOT=None)
    def test_patch_updates_metadata_only(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            obj = MediaFile.objects.create(file=make_file("old.pdf"), external_id="old")
            response = self.client.patch(
                f"/api/v1/media/{obj.pk}/",
                {"external_id": "ext-55"},
                format="json",
                **int_headers(),
            )
        assert response.status_code == 200, getattr(response, "data", response.content)
        obj.refresh_from_db()
        assert obj.external_id == "ext-55"
        assert obj.filename == "old.pdf"

    @override_settings(MEDIA_ROOT=None)
    def test_put_replaces_file(self) -> None:
        with override_settings(MEDIA_ROOT=self.temp_dir.name):
            obj = MediaFile.objects.create(file=make_file("old.pdf"))
            response = self.client.put(
                f"/api/v1/media/{obj.pk}/",
                {"file": make_file("new.png", content=b"abc", content_type="image/png"), "external_id": "new-ext"},
                format="multipart",
                **int_headers(),
            )
        assert response.status_code == 200, getattr(response, "data", response.content)
        obj.refresh_from_db()
        assert obj.filename == "new.png"
        assert obj.external_id == "new-ext"
        assert obj.file_type == MediaFile.FileType.IMAGE

    def test_delete_with_internal_key_returns_204(self) -> None:
        obj = MediaFile.objects.create(file=make_file("delete.pdf"))
        response = self.client.delete(f"/api/v1/media/{obj.pk}/", **int_headers())
        assert response.status_code == 204
        assert not MediaFile.objects.filter(pk=obj.pk).exists()


@override_settings(PUBLIC_API_KEY=PUB_KEY, INTERNAL_API_KEY=INT_KEY, LANGUAGE_CODE="nl")
class TestMediaFileViewSetFilteringOrderingSearch(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        MediaFile.objects.all().delete()
        self.nl = Language.objects.create(code="nl", name="Dutch", is_active=True)
        self.en = Language.objects.create(code="en", name="English", is_active=True)

        self.pdf = MediaFile.objects.create(file=make_file("brochure.pdf"))
        MediaFileTranslation.objects.create(
            media_file=self.pdf,
            language=self.nl,
            description="Programmabrochure voorjaar",
        )
        MediaFileTranslation.objects.create(
            media_file=self.pdf,
            language=self.en,
            description="Spring programme brochure",
        )

        self.png = MediaFile.objects.create(file=make_file("poster.png", content_type="image/png"))
        MediaFileTranslation.objects.create(
            media_file=self.png,
            language=self.nl,
            description="Social campagne poster",
        )

    def test_filter_by_file_type(self) -> None:
        response = self.client.get("/api/v1/media/?file_type=pdf", **pub_headers())
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == str(self.pdf.pk)

    def test_filter_by_mime_type(self) -> None:
        response = self.client.get("/api/v1/media/?mime_type=image/png", **pub_headers())
        assert len(results_list(response)) == 1

    def test_filter_by_filename(self) -> None:
        response = self.client.get("/api/v1/media/?filename=poster", **pub_headers())
        assert len(results_list(response)) == 1

    def test_filter_by_description(self) -> None:
        response = self.client.get("/api/v1/media/?description=campagne", **pub_headers())
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == str(self.png.pk)

    def test_filter_by_description_in_second_language(self) -> None:
        response = self.client.get("/api/v1/media/?description=Spring", **pub_headers())
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == str(self.pdf.pk)

    def test_ordering_by_size_bytes(self) -> None:
        response = self.client.get("/api/v1/media/?ordering=size_bytes", **pub_headers())
        sizes = [item["size_bytes"] for item in results_list(response)]
        assert sizes == sorted(sizes)

    def test_search_by_filename(self) -> None:
        response = self.client.get("/api/v1/media/?search=poster", **pub_headers())
        assert len(results_list(response)) == 1

    def test_search_by_mime_type(self) -> None:
        response = self.client.get("/api/v1/media/?search=image", **pub_headers())
        assert len(results_list(response)) >= 1

    def test_search_by_translated_description(self) -> None:
        response = self.client.get("/api/v1/media/?search=voorjaar", **pub_headers())
        items = results_list(response)
        assert len(items) == 1
        assert items[0]["id"] == str(self.pdf.pk)
