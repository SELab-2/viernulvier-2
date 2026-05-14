from apps.imports.scrapers import viernulvier_media as vmedia


class _DummyImg:
    def __init__(self, *, mode="RGB", is_animated=False, n_frames=1, webp_bytes=b"WEBP"):
        self.mode = mode
        self.is_animated = is_animated
        self.n_frames = n_frames
        self._webp = webp_bytes

    def load(self):
        return None

    def convert(self, _mode):
        return self

    def close(self):
        return None

    def save(self, buf_out, **_kwargs):
        # write configured webp bytes
        buf_out.write(self._webp)


class _DummyImageModule:
    def __init__(self, webp_bytes=b"WEBP", img_mode="RGB", is_animated=False, n_frames=1):
        self._webp = webp_bytes
        self._img_mode = img_mode
        self._is_animated = is_animated
        self._n_frames = n_frames

    def open(self, _buf):
        # ignore buffer contents; return a _DummyImg configured to write _webp
        return _DummyImg(mode=self._img_mode, is_animated=self._is_animated, n_frames=self._n_frames, webp_bytes=self._webp)


def test_maybe_convert_to_webp_short_circuits_for_webp_extension(monkeypatch):
    src = b"originalbytes"
    # Ensure Image.open would raise if called; function should short-circuit on URL
    monkeypatch.setattr(vmedia, "Image", None)
    res, converted = vmedia._maybe_convert_to_webp(src, "https://cdn.example/media/img.webp")
    assert res == src
    assert converted is False


def test_maybe_convert_to_webp_skips_animation(monkeypatch):
    src = b"orig"
    # configure dummy image module that reports animation
    dummy = _DummyImageModule(webp_bytes=b"small", is_animated=True)
    monkeypatch.setattr(vmedia, "Image", dummy)
    monkeypatch.setattr(vmedia, "UnidentifiedImageError", Exception)

    res, converted = vmedia._maybe_convert_to_webp(src, "http://example/img.jpg")
    assert res == src
    assert converted is False


def test_maybe_convert_to_webp_keeps_original_if_webp_larger(monkeypatch):
    src = b"origbytes"
    # make webp larger than source
    dummy = _DummyImageModule(webp_bytes=b"X" * (len(src) + 10))
    monkeypatch.setattr(vmedia, "Image", dummy)
    monkeypatch.setattr(vmedia, "UnidentifiedImageError", Exception)

    res, converted = vmedia._maybe_convert_to_webp(src, "http://example/img.jpg")
    assert res == src
    assert converted is False


def test_maybe_convert_to_webp_converts_when_smaller(monkeypatch):
    src = b"origbytes_long"
    webp = b"small"
    dummy = _DummyImageModule(webp_bytes=webp)
    monkeypatch.setattr(vmedia, "Image", dummy)
    monkeypatch.setattr(vmedia, "UnidentifiedImageError", Exception)

    res, converted = vmedia._maybe_convert_to_webp(src, "http://example/img.jpg")
    assert res == webp
    assert converted is True


def test_maybe_convert_to_webp_short_circuits_when_url_is_webp(monkeypatch):
    src = b"orig"
    dummy = _DummyImageModule(webp_bytes=b"small")
    monkeypatch.setattr(vmedia, "Image", dummy)
    # URL endswith .webp should short-circuit before attempting conversion
    res, converted = vmedia._maybe_convert_to_webp(src, "https://cdn.example/image.webp")
    assert res == src
    assert converted is False


def test_maybe_convert_to_webp_preserve_alpha_and_palette(monkeypatch):
    src = b"longsourcebytes"
    webp = b"smallwebp"
    # Test alpha-preserve branch (RGBA)
    dummy_alpha = _DummyImageModule(webp_bytes=webp, img_mode="RGBA")
    monkeypatch.setattr(vmedia, "Image", dummy_alpha)
    monkeypatch.setattr(vmedia, "UnidentifiedImageError", Exception)
    res, converted = vmedia._maybe_convert_to_webp(src, "http://example/alpha.jpg")
    assert res == webp
    assert converted is True

    # Test palette/other mode -> normalise to RGB branch
    dummy_palette = _DummyImageModule(webp_bytes=webp, img_mode="P")
    monkeypatch.setattr(vmedia, "Image", dummy_palette)
    res2, converted2 = vmedia._maybe_convert_to_webp(src, "http://example/pal.jpg")
    assert res2 == webp
    assert converted2 is True


def test_maybe_convert_to_webp_handles_unexpected_exceptions(monkeypatch):
    src = b"orig"

    class BadOpen:
        def open(self, _):
            raise RuntimeError("boom")

    monkeypatch.setattr(vmedia, "Image", BadOpen())
    res, converted = vmedia._maybe_convert_to_webp(src, "http://example/img.jpg")
    assert res == src
    assert converted is False
