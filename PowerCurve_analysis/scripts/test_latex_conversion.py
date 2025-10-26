"""
Quick test of LaTeX to Word equation conversion.
"""

from pathlib import Path
import sys

# Add parent directory to path to import md_to_docx functions
sys.path.insert(0, str(Path(__file__).parent))

from md_to_docx import parse_markdown_to_docx

# Define paths
base_dir = Path("/mnt/c/Users/klaus/klauspython/Latam/PowerCurve_analysis")

md_file = base_dir / "test_latex_equation.md"
template_file = base_dir.parent / "latam_hybrid" / "docs" / "WFD template.docx"
output_file = base_dir / "test_latex_equation.docx"
figures_dir = base_dir / "figures"

# Verify files exist
if not md_file.exists():
    print(f"❌ Markdown file not found: {md_file}")
    sys.exit(1)

if not template_file.exists():
    print(f"❌ Template file not found: {template_file}")
    sys.exit(1)

print(f"📄 Converting: {md_file.name}")
print(f"📋 Template: {template_file.name}")
print(f"💾 Output: {output_file}")
print()

# Convert
try:
    parse_markdown_to_docx(
        md_path=md_file,
        template_path=template_file,
        output_path=output_file,
        figures_dir=figures_dir
    )

    print()
    print("✅ Conversion complete!")
    print(f"📂 Open: {output_file}")
    print()
    print("Check if LaTeX equations ($E = mc^2$, etc.) appear as proper Word equations.")

except Exception as e:
    print(f"❌ Conversion failed: {e}")
    import traceback
    traceback.print_exc()
