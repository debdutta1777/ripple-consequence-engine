"""Create source-position-friendly fictional scholarship PDFs using only stdlib.

One continuous PDF text object keeps a stable ordered text layer for SDK-native
spans; vector backgrounds/shapes add visual polish without adding prose.
"""
from __future__ import annotations
from pathlib import Path


def pdf_for(year: int) -> bytes:
    if year not in (2025, 2026):
        raise ValueError('Unsupported fictional year')
    gpa, income = ('3.25','$52,000') if year == 2025 else ('3.65','$66,000')
    lines = [
        f'FICTIONAL BRIGHT FUTURES SCHOLARSHIP - {year} (DEMO ONLY)',
        f'Eligibility requires a minimum cumulative GPA of {gpa}.',
        f'Annual household income must not exceed {income}.',
        'An applicant must satisfy both rules to qualify.',
    ]
    def esc(value: str) -> str:
        return value.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream = ('q 0.970 0.974 0.992 rg 0 0 612 792 re f Q\n'
              'q 0.115 0.133 0.235 rg 0 633 612 159 re f Q\n'
              'q 0.99 0.99 1 rg 37 342 538 233 re f Q\n'
              'q 0.84 0.84 0.98 RG 1 w 37 342 538 233 re S Q\n'
              'q 0.36 0.34 0.81 rg 50 495 5 42 re f Q\n'
              'q 0.36 0.34 0.81 rg 50 414 5 42 re f Q\n'
              'BT /F1 12 Tf 0.94 0.94 1 rg 49 730 Td\n'
              f'({esc(lines[0])}) Tj\n'
              '18 -211 Td 0.12 0.14 0.25 rg /F1 14 Tf\n'
              f'({esc(lines[1])}) Tj\n'
              '0 -81 Td\n'
              f'({esc(lines[2])}) Tj\n'
              '0 -61 Td /F1 12 Tf\n'
              f'({esc(lines[3])}) Tj\nET\n')
    objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        f'<< /Length {len(stream.encode("ascii"))} >>\nstream\n{stream}endstream',
    ]
    data='%PDF-1.4\n'
    offsets=[0]
    for i,obj in enumerate(objects, start=1):
        offsets.append(len(data.encode('ascii')))
        data+=f'{i} 0 obj\n{obj}\nendobj\n'
    xref=len(data.encode('ascii'))
    data+='xref\n0 6\n0000000000 65535 f \n'
    data+=''.join(f'{n:010d} 00000 n \n' for n in offsets[1:])
    data+=f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'
    return data.encode('ascii')


def write(target:Path)->None:
    target.mkdir(parents=True,exist_ok=True)
    for year in (2025,2026):
        (target/f'judge-compact-{year}.pdf').write_bytes(pdf_for(year))

if __name__=='__main__':
    write(Path('web/samples'))