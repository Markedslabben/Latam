import sys
from pathlib import Path
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import re

def detect_title(line):
    """Detect if a line is likely a title."""
    # Title characteristics
    if len(line) > 5 and len(line) < 100:  # Reasonable title length
        if line.isupper() or line.istitle():  # All caps or Title Case
            return True
        if re.match(r'^[0-9]+\.[0-9]* .*', line):  # Numbered sections
            return True
    return False

def detect_list_item(line):
    """Detect if a line is a list item."""
    # Common list item patterns
    patterns = [
        r'^\s*[\-\•\*]\s+',  # Bullet points
        r'^\s*[0-9]+[\.\)]\s+',  # Numbered lists
        r'^\s*[a-z][\.\)]\s+',  # Letter lists
    ]
    return any(re.match(pattern, line) for pattern in patterns)

def convert_pdf_to_markdown(pdf_path, output_path=None):
    """Convert PDF to a markdown-friendly format with enhanced structure detection."""
    # Extract text with better layout preservation
    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        boxes_flow=0.5,
    )
    text = extract_text(pdf_path, laparams=laparams)
    
    # Split into lines and process
    lines = text.split('\n')
    markdown_lines = []
    in_paragraph = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines but add spacing
        if not line:
            if in_paragraph:
                markdown_lines.append('')
                in_paragraph = False
            continue
        
        # Detect and format titles/headers
        if detect_title(line):
            if in_paragraph:
                markdown_lines.append('')
                in_paragraph = False
            
            # Determine header level based on characteristics
            if i == 0 or (len(line) < 50 and line.isupper()):
                markdown_lines.append(f'# {line.title()}')
            else:
                markdown_lines.append(f'## {line.title()}')
            markdown_lines.append('')
            continue
        
        # Handle list items
        if detect_list_item(line):
            if in_paragraph:
                markdown_lines.append('')
                in_paragraph = False
            
            # Convert to markdown list format
            if re.match(r'^\s*[\-\•\*]\s+', line):
                markdown_lines.append(f'- {re.sub(r"^\s*[\-\•\*]\s+", "", line)}')
            elif re.match(r'^\s*[0-9]+[\.\)]\s+', line):
                markdown_lines.append(f'1. {re.sub(r"^\s*[0-9]+[\.\)]\s+", "", line)}')
            else:
                markdown_lines.append(f'- {re.sub(r"^\s*[a-z][\.\)]\s+", "", line)}')
            continue
        
        # Handle equations (basic detection)
        if re.search(r'[=<>≈≤≥±∑∏∫√]', line) and not line.endswith('.'):
            markdown_lines.append('')
            markdown_lines.append(f'$${line}$$')
            markdown_lines.append('')
            continue
            
        # Regular text - handle paragraphs
        if not in_paragraph:
            markdown_lines.append(line)
            in_paragraph = True
        else:
            # Append to previous line if it's part of the same paragraph
            markdown_lines[-1] = f'{markdown_lines[-1]} {line}'
    
    # Clean up the markdown text
    markdown_text = '\n'.join(markdown_lines)
    
    # Fix common markdown issues
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)  # Remove excess newlines
    markdown_text = re.sub(r'[ ]{2,}', ' ', markdown_text)    # Remove excess spaces
    
    # If no output path specified, create one based on input
    if output_path is None:
        output_path = Path(pdf_path).with_suffix('.md')
    
    # Write the markdown file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    
    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_markdown.py <pdf_file> [output_file]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        output_path = convert_pdf_to_markdown(pdf_file, output_file)
        print(f"Successfully converted {pdf_file} to {output_path}")
    except Exception as e:
        print(f"Error converting PDF: {e}") 