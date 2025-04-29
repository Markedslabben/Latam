# Project Documentation and References

This directory contains all reference materials, papers, and reports used in the project.

## Directory Structure

- `papers/`: Original PDF documents of academic papers and research publications
- `extracted_text/`: Text-only versions of papers for LLM processing
- `summaries/`: Markdown summaries of key concepts and methodologies
- `reports/`: Technical reports and documentation
- `references/`: Additional reference materials and resources

## Document Organization

### Papers and Their Extracted Text

| PDF File | Text/Summary File | Title | Authors | Year | Key Topics |
|----------|------------------|-------|---------|------|------------|
| <!-- Add papers here --> |

### Summaries of Key Concepts

| Summary File | Related Documents | Topics Covered |
|--------------|------------------|----------------|
| <!-- Add summaries here --> |

### Reports and References

| File Name | Type | Description |
|-----------|------|-------------|
| <!-- Add reports here --> |

## Usage Guidelines

1. When adding new documents:
   - Place PDF in appropriate directory: `papers/`, `reports/`, or `references/`
   - Create a text extraction in `extracted_text/` using the same base name
   - Add or update relevant summaries in `summaries/`
   - Update this README with document details

2. For text extraction:
   - Extract main content, equations, and diagrams descriptions
   - Maintain section structure for easy reference
   - Include page numbers from original PDF
   - Example filename: `2024_wind_turbine_analysis.txt`

3. For summaries:
   - Focus on methodology, algorithms, and key findings
   - Include relevant equations and pseudocode
   - Cross-reference related documents
   - Example filename: `wind_turbine_shading_methodology.md`

4. For code context:
   - Reference both PDF and text files in code comments
   - Use summaries for implementation guidance
   - Include relevant equations or algorithms from summaries

5. For LLM context:
   - Point to text files and summaries rather than PDFs
   - Reference specific sections or line numbers
   - Use summaries for high-level discussions

## Example Summary Format

```markdown
# Wind Turbine Shading Analysis
Source: `papers/2024_wind_turbine_analysis.pdf`

## Key Concepts
- Shadow calculation methodology
- Impact factors
- Mathematical models

## Relevant Equations
1. Shadow Length: L = H * tan(θ)
   where:
   - H: Tower height
   - θ: Solar elevation angle

## Implementation Notes
- Algorithm complexity: O(n)
- Key considerations
- Validation methods
``` 