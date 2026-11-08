"""PDF upload tests are offline and consume zero Clocked credits."""
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app
from app.pdf_ingest import MAX_PDF_BYTES, PdfInputError, parse_policy_pdf

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_OLD = ROOT / 'web' / 'samples' / 'previous-policy.pdf'
SAMPLE_NEW = ROOT / 'web' / 'samples' / 'updated-policy.pdf'


def two_page_pdf():
    writer = PdfWriter()
    writer.append(str(SAMPLE_OLD))
    writer.append(str(SAMPLE_NEW))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_pdf_text_and_page_offsets():
    result = parse_policy_pdf(two_page_pdf())
    assert result['page_count'] == 2
    assert result['clocked_calls'] == 0
    assert len(result['text']) == result['characters']
    assert 'minimum cumulative GPA of 3.2' in result['text']
    assert '2026' in result['text']
    assert result['pages'][0]['start'] == 0
    assert result['pages'][0]['end'] < result['pages'][1]['start']
    for page in result['pages']:
        excerpt = result['text'][page['start']:page['end']]
        assert len(excerpt) == page['characters']


def test_pdf_preview_route_does_not_need_a_key(monkeypatch):
    monkeypatch.delenv('CLOCKED_API_KEY', raising=False)
    monkeypatch.delenv('ENABLE_LIVE', raising=False)
    with TestClient(app) as client:
        r = client.post('/api/parse-pdf', files={'file': ('sample.pdf', two_page_pdf(), 'application/pdf')})
    assert r.status_code == 200
    assert r.json()['source'] == 'temporary_pdf_text_extraction'
    assert r.json()['page_count'] == 2


def test_pdf_rejects_forged_extension_and_non_pdf():
    with TestClient(app) as client:
        r = client.post('/api/parse-pdf', files={'file': ('policy.pdf', b'<html>not pdf</html>', 'application/pdf')})
        wrong = client.post('/api/parse-pdf', files={'file': ('policy.txt', two_page_pdf(), 'text/plain')})
    assert r.status_code == 422
    assert wrong.status_code == 415


def test_pdf_rejects_oversized_upload():
    with TestClient(app) as client:
        r = client.post('/api/parse-pdf', files={'file': ('huge.pdf', b'%PDF-' + b'x' * MAX_PDF_BYTES, 'application/pdf')})
    assert r.status_code == 422
    assert '2 MB' in r.json()['detail']


def test_pdf_rejects_scanned_or_blank_documents():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    pdf = BytesIO()
    writer.write(pdf)
    try:
        parse_policy_pdf(pdf.getvalue())
        assert False, 'A blank PDF must never be treated as a valid policy'
    except PdfInputError as exc:
        assert 'scanned' in str(exc).lower()


def test_pdf_rejects_too_many_pages():
    writer = PdfWriter()
    for _ in range(13):
        writer.add_blank_page(width=612, height=792)
    pdf = BytesIO()
    writer.write(pdf)
    try:
        parse_policy_pdf(pdf.getvalue())
        assert False, 'A PDF beyond the page limit must be rejected'
    except PdfInputError as exc:
        assert '12 pages' in str(exc)


def test_sample_pdfs_are_publicly_downloadable():
    with TestClient(app) as client:
        for file in ('previous-policy.pdf', 'updated-policy.pdf'):
            r = client.get('/assets/samples/' + file)
            assert r.status_code == 200
            assert r.content.startswith(b'%PDF-')
            assert len(r.content) < MAX_PDF_BYTES