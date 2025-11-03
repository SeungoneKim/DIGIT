# OpenHands Research Paper Reviewer

This directory contains code to run the research paper reviewer using the OpenHands API. The reviewer conducts systematic peer review focusing on validity and methodology assessment with concrete evidence-based criticisms.

## Overview

The `paper_reviewer.py` script uses the OpenHands API to:

1. **Setup and Code Analysis**: Clone and analyze provided code repositories
2. **Content Analysis**: Examine paper content, figures, and methodology  
3. **Literature Review**: Compare claims with established literature
4. **Reproducibility Testing**: Attempt to reproduce key results
5. **Critical Assessment**: Document up to 10 specific items with concrete evidence

## Requirements

- Python 3.7+
- OpenHands API server running locally or remotely
- Required Python packages (see `requirements.txt`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure OpenHands API server is running. If running locally:
```bash
# Follow OpenHands installation instructions to start the API server
# Default URL: http://localhost:3000
```

## Usage

### Basic Usage

```bash
python paper_reviewer.py --paper-file example_paper_data.json
```

### Advanced Usage

```bash
python paper_reviewer.py \
    --paper-file your_paper_data.json \
    --api-url http://your-openhands-server:3000 \
    --api-key your_api_key \
    --output-dir ./custom_output
```

### Parameters

- `--paper-file`: JSON file containing paper data (required)
- `--api-url`: OpenHands API base URL (default: http://localhost:3000)
- `--api-key`: API key for authentication (optional)
- `--output-dir`: Output directory for review results (default: ./review_output)

## Input Format

The paper data should be provided as a JSON file with the following structure:

```json
{
  "title": "Paper Title",
  "journal": "Journal Name",
  "published": "Publication Date",
  "code": ["https://github.com/repo/url"],
  "supplementary_0": [
    {
      "label": "Supplementary Information",
      "link": "https://link-to-supplementary.pdf"
    }
  ],
  "nature_content": [
    {
      "section_name": "Abstract",
      "section_text": "Abstract text...",
      "section_image": ["https://link-to-figure.png"]
    }
  ]
}
```

See `example_paper_data.json` for a complete example.

## Output

The reviewer generates:

1. **review_results.json**: Complete review results with session metadata
2. **critical_assessment.md**: Detailed critical assessment with 10 items
3. Session logs and intermediate outputs

### Output Structure

```
review_output/
├── review_results.json      # Complete results with metadata
├── critical_assessment.md   # Main critical assessment
└── session_logs/           # Detailed session information
```

## Critical Assessment Format

Each critical item includes:

- **Claim**: Specific statement from the paper being criticized
- **Evidence**: Concrete evidence from:
  - Code execution results (e.g., "Line 25 in `file.py` produces error X")
  - Literature citations (e.g., "Contradicts findings in Smith et al. [1]")
  - Experimental analysis (e.g., "Figure 2 shows scale bar of 200nm but claims 0.178Å precision")
- **Impact**: Assessment of how this affects the paper's validity

## Example Critical Assessment Items

### Item 1: Code Reproducibility Issues
**Claim**: Authors state code is available at GitHub repository
**Evidence**: 
- Line 25 in `emitterExperimentMLE.py` contains hardcoded path `/home/user/...` producing `FileNotFoundError`
- Repository lacks `requirements.txt` violating reproducibility standards [5]

**Impact**: Code cannot be executed without access to authors' private filesystem

### Item 2: Extraordinary Precision Claims
**Claim**: Authors claim "unprecedented localization of σp = 0.178 ± 0.107 Å"
**Evidence**:
- Claimed precision is 8.7x smaller than diamond lattice constant (3.567 Å)
- No comparison with Cramér-Rao Lower Bound established by Thompson et al. [1]
- Relative uncertainty (60%) violates measurement quality standards [2]

**Impact**: Extraordinary precision claim lacks rigorous validation

## API Configuration

### Local OpenHands Setup

If running OpenHands locally, ensure the API server is configured with:

```yaml
# config.yaml
api:
  port: 3000
  host: "0.0.0.0"
  cors_enabled: true

agent:
  model: "anthropic/claude-3-5-sonnet-20241022"
  max_iterations: 100
```

### Remote OpenHands Setup

For remote OpenHands instances:

```bash
python paper_reviewer.py \
    --paper-file paper.json \
    --api-url https://your-openhands-instance.com \
    --api-key your_authentication_token
```

## Error Handling

The reviewer handles common errors:

- **Connection errors**: Retries with exponential backoff
- **Timeout errors**: Configurable timeout (default: 1 hour)
- **API errors**: Detailed error messages and logging
- **File access errors**: Graceful handling of inaccessible URLs

## Customization

### Custom Review Criteria

Modify the `_create_review_prompt()` method to customize review criteria:

```python
def _create_review_prompt(self, paper_data: Dict[str, Any]) -> str:
    # Add custom review criteria here
    custom_criteria = """
    Additional criteria:
    3. Ethical considerations: Are there ethical issues with the research?
    4. Statistical rigor: Are statistical methods appropriate?
    """
    # ... rest of prompt
```

### Custom Output Processing

Override `_extract_review_content()` to customize output processing:

```python
def _extract_review_content(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Custom content extraction logic
    pass
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure OpenHands API server is running
2. **Authentication failed**: Check API key configuration
3. **Timeout errors**: Increase timeout for complex papers
4. **Memory errors**: Use smaller batch sizes for large papers

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Session Recovery

If a session fails, you can recover using the session ID:

```python
async with OpenHandsPaperReviewer() as reviewer:
    messages = await reviewer.get_session_messages(session_id)
    # Process recovered messages
```

## Contributing

To extend the reviewer:

1. Add new analysis methods to the `OpenHandsPaperReviewer` class
2. Extend the prompt template for new review criteria
3. Add custom output processors for specific paper types
4. Implement domain-specific validation rules

## License

This code is provided under the same license as the OpenHands project.

## Support

For issues related to:
- OpenHands API: Check OpenHands documentation
- Paper reviewer logic: Create an issue in this repository
- Specific paper reviews: Ensure paper data format is correct