# System Patterns - Eagle Community Index

## Architecture Overview

### Component Architecture
```
GitHub Actions Workflows
├── verify-plugin.yaml    # Repository compliance checking
├── create-entry.yaml     # Index entry creation
└── update-index.yaml     # Scheduled maintenance

Python Scripts
├── repo-verify-correctness.py  # Core verification logic
├── create-index-entry.py       # Entry creation and management
└── update-index.py             # Bulk update operations

Data Storage
├── index/alldex.json          # Master plugin registry
├── index/candidate.json       # Candidate plugin entries
├── index/primary.json         # Primary plugin entries
└── configs/blacklist_repos.json  # Blocked repositories
```

## Key Design Patterns

### 1. Verification Pipeline Pattern
**Problem**: Need consistent, repeatable repository validation
**Solution**: Standardized verification class with method chaining
```python
verifier = RepoVerifier()
is_valid, issues = verifier.verify_repo(repo_name)
```

**Components**:
- Repository existence check
- Release validation (github-actions[bot] uploader)
- GitHub Actions workflow presence
- Manifest.json structure validation
- Plugin file presence (.eagleplugin)

### 2. Index Management Pattern
**Problem**: Multiple index files need synchronized updates
**Solution**: Atomic update operations with rollback capability

**Key Principles**:
- Load → Validate → Update → Save as single transaction
- Maintain referential integrity between alldex.json and type-specific files
- Preserve historical data (versions, timestamps)
- Handle type migrations (candidate → primary)

### 3. Rate Limiting Pattern
**Problem**: GitHub API rate limits require careful management
**Solution**: Configurable batch processing with delays

**Implementation**:
- 1-second delays between API calls
- Configurable batch sizes (default: 200)
- Priority-based processing (recent changes first)
- Graceful degradation on rate limit hits

### 4. Timestamp Tracking Pattern
**Problem**: Need audit trail and update scheduling
**Solution**: Comprehensive timestamp management

**Schema**:
```json
{
  "plugin-id": {
    "createdAt": "2024-01-15T10:30:45.123Z",
    "lastModified": "2024-01-15T10:30:45.123Z",
    // ... other fields
  }
}
```

### 5. Localization Resolution Pattern
**Problem**: Plugins may use localization keys instead of direct text
**Solution**: Dynamic localization key resolution

**Process**:
1. Detect localization keys (`{{key.path}}`)
2. Fetch `_locales/en.json` from repository
3. Navigate key path to resolve actual text
4. Fall back gracefully if resolution fails

### 6. Blacklist Management Pattern
**Problem**: Need to prevent repeated processing of problematic repositories
**Solution**: Automated blacklist with failure tracking

**Behavior**:
- First failure: Warning and cache invalidation
- Second failure: Automatic blacklist addition
- Manual blacklist removal required for redemption

## Critical Implementation Paths

### Plugin Submission Flow
1. Manual trigger or API call to `create-entry.yaml`
2. Repository verification via `repo-verify-correctness.py`
3. Manifest parsing and localization resolution
4. Index file updates with timestamp tracking
5. Git commit with descriptive message

### Scheduled Update Flow
1. Daily trigger of `update-index.yaml`
2. Load all index files and alldex registry
3. Filter entries by last modified date (>3 days old)
4. Batch process with rate limiting
5. Update versions and timestamps for changed entries
6. Prune invalid entries and commit changes

### Error Recovery Patterns
- **Verification Failures**: Add to blacklist after repeated failures
- **API Rate Limits**: Exponential backoff and batch size reduction
- **File Corruption**: Atomic operations with validation
- **Network Issues**: Retry logic with circuit breaker pattern

## Component Relationships

### Data Flow
```
Repository → Verification → Index Creation → Scheduled Updates
     ↓              ↓              ↓              ↓
Blacklist ← Failure Tracking ← Version Updates ← Maintenance
```

### Dependencies
- **Scripts**: Independent, reusable components
- **Workflows**: Orchestrate scripts with GitHub Actions context
- **Index Files**: JSON storage with referential integrity
- **Configuration**: External blacklists and settings