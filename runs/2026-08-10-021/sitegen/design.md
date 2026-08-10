# Design Document: sitegen.py

## 1. Structure

### File Composition
- `sitegen.py`: Main script for Markdown to HTML conversion and site generation.
- `md_src/`: Input directory containing `.md` files (Read-Only).
- `site/`: Output directory containing generated `.html` files.

### Data Flow
1. **Scan**: Scan `md_src/` for all files with `.md` extension.
2. **Convert**: For each `.md` file:
   - Read content.
   - Apply Markdown conversion rules.
   - Write to `site/[filename].html`.
3. **Index**: 
   - Generate a list of links to all converted `.html` files.
   - Write this list to `site/index.html`.
4. **Report**: Print the success marker `SITEGEN OK <count>` to stdout.

### Responsibility Division
- **File I/O Manager**: Handles directory scanning, reading `.md` files, and writing `.html` files.
- **Markdown Converter**: Implements the replacement logic for headers, lists, and links.
- **Site Orchestrator**: Coordinates the flow between scanning, conversion, and indexing.

## 2. Quality Characteristics & Implementation Structure

### Verifiability
To ensure the script is not a "silent failure" (exiting 0 without doing anything), the following verification structure is implemented:
- **Explicit Marker**: The script must print `SITEGEN OK <count>` where `<count>` is the actual number of converted files.
- **Atomic Output**: The `site/` directory is ensured to exist before writing.

### Conversion Logic (Regular Expressions)
The conversion will be performed in the following order to avoid overlapping patterns:
- **Headers**: `#` (1-6) $\rightarrow$ `<h1>` to `<h6>`.
  - Rule: Line starting with `#` repeated 1-6 times followed by a space.
- **Links**: `[text](url)` $\rightarrow$ `<a href="url">text</a>`.
  - Rule: Non-greedy match for text and URL within brackets/parentheses.
- **Unordered Lists**: `- item` $\rightarrow$ `<ul><li>item</li></ul>`.
  - Rule: Lines starting with `- `. Since Markdown lists are grouped, the script will wrap consecutive list items in a single `<ul>` block.

## 3. Design Rules

### File I/O Rules
- **Input files are read-only**: `md_src/*.md` must never be modified, overwritten, or deleted.
- **Output target**: Only files within the `site/` directory should be created.
- **Cleanup**: No temporary files shall be left in the working directory.

### Formatting Rules
- **Output Marker**: The exact string `SITEGEN OK <count>` must be printed to standard output (e.g., `SITEGEN OK 3`).
- **HTML Structure**: Each generated page must be a valid HTML fragment or document containing the converted tags.

### Implementation Constraints
- Use the `os` and `re` modules for directory traversal and pattern replacement.
- Ensure `site/` directory is created if it does not exist.

---
**Verification Marker**: SITEGEN OK
