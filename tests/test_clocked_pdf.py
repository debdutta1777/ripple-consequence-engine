from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json

from app.clocked_pdf import create_marked_comparison

ROOT = Path(__file__).resolve().parent.parent
PREVIOUS = (ROOT / "web/samples/previous-policy.pdf").read_bytes()
CURRENT = (ROOT / "web/samples/updated-policy.pdf").read_bytes()


class FakeClockedPdf:
    def __init__(self, provide=True):
        self.provide = provide
        self.calls = 0
    def compare(self, **kwargs):
        self.calls += 1
        assert kwargs['return_pdf'] == 'highlight'
        assert kwargs['return_text'] is True
        assert [d['id'] for d in kwargs['documents']] == ['previous', 'current']
        assert kwargs['documents'][0]['pdf'] == PREVIOUS
        self.result = FakePdfResult(self.provide)
        return self.result


class FakePdfResult(dict):
    def __init__(self, provide):
        super().__init__(verdict='conflict', conflicts=[{'document_ids': ['previous', 'current']}])
        self.provide = provide
        self.credits = 3
        self.cost_usd = .0001
    def marked_pdf(self, document):
        if not self.provide:
            raise ValueError('No annotated PDF returned')
        return PREVIOUS if document == 'previous' else CURRENT


def test_pdf_proof_packs_only_actual_sdk_marked_pdfs():
    client = FakeClockedPdf()
    bundle, manifest = create_marked_comparison(client, PREVIOUS, CURRENT)
    assert client.calls == 1
    assert manifest['verdict'] == 'conflict'
    assert manifest['documents']['previous']['highlighted']
    assert manifest['usage']['credits'] == 3
    with ZipFile(BytesIO(bundle)) as archive:
        assert set(archive.namelist()) == {'manifest.json', 'previous-clocked-highlighted.pdf', 'current-clocked-highlighted.pdf'}
        saved = json.loads(archive.read('manifest.json'))
        assert saved['documents']['current']['highlighted']


def test_pdf_proof_does_not_fabricate_annotation_when_missing():
    bundle, manifest = create_marked_comparison(FakeClockedPdf(provide=False), PREVIOUS, CURRENT)
    assert not manifest['documents']['previous']['highlighted']
    with ZipFile(BytesIO(bundle)) as archive:
        assert archive.namelist() == ['manifest.json']


def test_pdf_proof_rejects_invalid_source_before_billable_call():
    client = FakeClockedPdf()
    from app.pdf_ingest import PdfInputError
    try:
        create_marked_comparison(client, b'not a pdf', CURRENT)
    except PdfInputError:
        pass
    else:
        raise AssertionError('Invalid document was accepted')
    assert client.calls == 0