# TODO: Markdown til Word-konvertering med firmatemplate

## Sammendrag av anbefalinger

Du har flere alternativer for å konvertere .md-rapport til .docx med firmaets template (som inkluderer logoer, headere/footere).

---

## Alternativer

### 1. **docxtpl** (Anbefalt hvis rapportstruktur er konsistent)

**Hva**: Template-basert tilnærming med Jinja2-placeholders

**Fordeler**:
- ✅ Beholder ALLE template-elementer (logoer, headere, footere)
- ✅ Enkel separasjon: design i Word, data i Python
- ✅ Perfekt for rapporter med forhåndsdefinert struktur

**Ulemper**:
- ❌ Må legge til placeholders i template først
- ❌ Mindre fleksibel for dynamiske strukturer

**Installasjon**:
```bash
conda install -c conda-forge docxtpl
```

**Eksempel**:
```python
from docxtpl import DocxTemplate

doc = DocxTemplate('company_template.docx')
context = {
    'title': 'Prosjektrapport',
    'sections': [...],
    'figure1': InlineImage(doc, 'plot.png')
}
doc.render(context)
doc.save('rapport.docx')
```

---

### 2. **Hybrid: Pandoc + python-docx** (Anbefalt hvis markdown er kompleks)

**Hva**: Bruk pandoc for konvertering, python-docx for å merge inn i template

**Fordeler**:
- ✅ Pandoc håndterer kompleks markdown utmerket
- ✅ Beholder template-elementer via python-docx
- ✅ Best of both worlds

**Ulemper**:
- ❌ Mer kompleks (to-trinns prosess)

**Du har allerede**:
- ✅ pandoc (3.7.0.2)
- ✅ python-docx (1.2.0)

**Fremgangsmåte**:
```python
# Steg 1: Konverter markdown
import os
os.system('pandoc rapport.md -o temp.docx')

# Steg 2: Merge inn i template
from docx import Document
template = Document('company_template.docx')
content = Document('temp.docx')

# Kopier innhold fra temp.docx til template
for element in content.element.body:
    template.element.body.append(element)

template.save('final_rapport.docx')
```

---

### 3. **python-docx** (Hvis du vil ha full kontroll)

**Hva**: Manuell parsing av markdown og bygging av Word-dokument

**Fordeler**:
- ✅ Full kontroll over alt
- ✅ Beholder template-elementer

**Ulemper**:
- ❌ Må manuelt parse markdown
- ❌ Mer kode

**Du har allerede**:
- ✅ python-docx (1.2.0)

---

### 4. **Pandoc alene** (Enklest, men begrenset)

**Hva**: Direkte konvertering med `--reference-doc`

**Fordeler**:
- ✅ Svært enkelt
- ✅ Utmerket markdown-håndtering

**Ulemper**:
- ❌ Beholder IKKE logoer/headere/footere
- ❌ Kun styles overføres

**Kommando**:
```bash
pandoc rapport.md -o rapport.docx --reference-doc=company_template.dotx
```

---

## Min anbefaling

**Scenario 1**: Rapporter med fast struktur (samme seksjoner hver gang)
→ **Bruk docxtpl** (Alternativ 1)

**Scenario 2**: Kompleks markdown med varierende struktur
→ **Bruk Hybrid-tilnærming** (Alternativ 2)

**Scenario 3**: Kun styles er viktig, ikke logoer/headere
→ **Bruk Pandoc alene** (Alternativ 4)

---

## Neste steg

1. Avgjør hvilken tilnærming som passer best for dine behov
2. Hvis docxtpl: installer med `conda install -c conda-forge docxtpl`
3. Test med én rapport
4. Automatiser prosessen når den fungerer

---

## Notater

- Både .dotx og .docx fungerer som template-filer
- Du har allerede: pandoc (3.7.0.2) og python-docx (1.2.0)
- Figurer/tabeller: Sørg for at stiene er korrekte i markdown
- Referanser: Bruk `![caption](path/to/figure.png)` syntaks

---

**Dato opprettet**: 2025-10-19
