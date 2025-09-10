# DeepLit Analyzer

DeepLit Analyzer is a literature analysis tool powered by the DeepSeek API, designed to help researchers and students efficiently read academic papers. It can automatically generate abstracts, section summaries, extract key points, and provide corresponding evidence information, making literature reading more efficient and reliable.

## Features

- **Abstract Generation**: Automatically generate concise abstracts from academic papers
- **Section Summarization**: Summarize specific sections of research papers  
- **Key Point Extraction**: Identify and extract the most important findings and contributions
- **Evidence Mapping**: Provide references to original text for verification
- **Multiple Output Formats**: Support for Markdown, JSON, and plain text output
- **Command Line Interface**: Easy-to-use CLI for batch processing

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/sign-river/deeplit-analyzer.git
cd deeplit-analyzer

# Install the package
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Add your DeepSeek API key to `.env`:
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## Usage

### Command Line Interface

**Analyze a complete paper:**
```bash
deeplit analyze paper.txt --output results.md --format markdown
```

**Generate summary:**
```bash
deeplit summarize paper.txt
```

**Check configuration:**
```bash
deeplit config
```

### Python API

```python
from deeplit_analyzer import DeepLitAnalyzer, Config

# Initialize with default config
analyzer = DeepLitAnalyzer()

# Analyze a paper
with open('paper.txt', 'r') as f:
    paper_text = f.read()

results = analyzer.analyze_paper(paper_text)
print(results['abstract'])
```

## Requirements

- Python 3.8+
- DeepSeek API key
- Internet connection for API access

## License

MIT License - see LICENSE file for details.
