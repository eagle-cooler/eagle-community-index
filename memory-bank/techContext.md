# Technical Context - Eagle Community Index

## Technology Stack

### Core Technologies
- **Python 3.11**: Primary scripting language
- **GitHub Actions**: CI/CD and automation platform
- **GitHub API**: Repository data access and validation
- **JSON**: Data storage format for indices and configuration
- **Git**: Version control and automated commits

### Python Dependencies
- **requests**: HTTP client for GitHub API interactions
- **json**: Built-in JSON parsing and generation
- **datetime**: Timestamp management and date calculations
- **base64**: Content decoding from GitHub API
- **re**: Regular expression pattern matching
- **subprocess**: External script execution

### GitHub Actions Features
- **workflow_dispatch**: Manual workflow triggering with inputs
- **schedule**: Cron-based automated execution
- **actions/checkout@v4**: Repository checkout
- **actions/setup-python@v4**: Python environment setup
- **Matrix strategies**: Not currently used but available

## Development Environment

### Repository Structure
```
eagle-community-index/
├── .github/workflows/     # GitHub Actions automation
│   ├── verify-plugin.yaml
│   ├── create-entry.yaml
│   └── update-index.yaml
├── scripts/              # Python automation scripts
│   ├── repo-verify-correctness.py
│   ├── create-index-entry.py
│   └── update-index.py
├── index/               # JSON data storage
│   ├── alldex.json     # Master registry
│   ├── candidate.json  # Candidate plugins
│   └── primary.json    # Primary plugins
├── configs/            # Configuration files
│   ├── blacklist_repos.json
│   └── whitelist.json
└── memory-bank/        # Project documentation
```

### File Permissions and Access
- **Scripts**: Executable Python files with shebang
- **Workflows**: GitHub Actions YAML with proper permissions
- **Index Files**: Read/write JSON with atomic operations
- **Configuration**: Read-only during runtime, write via automation

## Technical Constraints

### GitHub API Limitations
- **Rate Limiting**: 5000 requests/hour for authenticated, 60 for anonymous
- **Request Size**: Large file content requires base64 decoding
- **Response Caching**: Not implemented, relies on GitHub's caching
- **Authentication**: Currently using anonymous access

### Data Format Constraints
- **JSON Schema**: No formal schema validation (could be added)
- **File Size**: Index files must remain manageable for git operations
- **Character Encoding**: UTF-8 required for international plugin names
- **Timestamp Format**: ISO 8601 with UTC timezone

### Performance Considerations
- **Batch Processing**: 200 entry default limit for update operations
- **Rate Limiting**: 1-second delays between API calls
- **Memory Usage**: Loading entire index files into memory
- **Network Latency**: Sequential API calls (could be parallelized)

## Integration Patterns

### GitHub Actions Integration
- **Environment Variables**: Limited use, mostly input parameters
- **Secrets Management**: Not currently required (anonymous API access)
- **Artifact Storage**: Not used, all data committed to repository
- **Status Reporting**: Step summaries and workflow outputs

### External API Integration
- **GitHub REST API**: Primary integration point
- **Error Handling**: Retry logic and graceful degradation
- **Response Parsing**: JSON parsing with error handling
- **Content Decoding**: Base64 decoding for file contents

### File System Integration
- **Atomic Operations**: Read → Modify → Write pattern
- **Path Handling**: Cross-platform path construction
- **Error Recovery**: File corruption detection and recovery
- **Backup Strategy**: Git history serves as backup

## Development Workflow

### Local Development
```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install requests

# Run verification
python scripts/repo-verify-correctness.py owner/repo

# Create index entry
python scripts/create-index-entry.py owner/repo candidate

# Update index
python scripts/update-index.py --days 7 --max-updates 50
```

### Testing Strategy
- **Manual Testing**: Direct script execution with test repositories
- **Integration Testing**: GitHub Actions workflow execution
- **Error Case Testing**: Invalid repositories and API failures
- **Performance Testing**: Batch operations with rate limiting

### Deployment Strategy
- **Zero Downtime**: Git-based deployment via commits
- **Rollback**: Git revert capabilities
- **Monitoring**: GitHub Actions workflow status
- **Configuration**: Environment-based parameter tuning

## Tool Usage Patterns

### Python Script Patterns
- **Argument Parsing**: argparse for CLI interfaces
- **Error Handling**: Try-catch with informative messages
- **Logging**: Print statements with emoji indicators
- **Exit Codes**: Standard success (0) and failure (1) codes

### GitHub Actions Patterns
- **Input Validation**: Shell script validation steps
- **Output Capture**: Step outputs and summary generation
- **Conditional Execution**: Success/failure-based step execution
- **Commit Automation**: Git configuration and automated commits