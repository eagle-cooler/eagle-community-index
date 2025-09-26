# Eagle Community Index - Project Brief

## Project Overview
Eagle Community Index is a comprehensive plugin repository management system for the Eagle file management application. The system provides automated verification, indexing, and maintenance of Eagle plugins from GitHub repositories.

## Core Requirements

### 1. Repository Verification
- Verify repositories meet Eagle plugin standards
- Check GitHub Actions automation
- Validate manifest.json files
- Ensure releases are properly built and distributed

### 2. Index Management
- Maintain categorized plugin index (candidate/primary)
- Track plugin metadata, versions, and timestamps
- Support localization for internationalized plugins
- Provide traceability to source repositories

### 3. Automated Workflows
- GitHub Actions for verification and indexing
- Blacklist management for non-compliant repositories
- Scheduled updates and maintenance
- Rate limiting and error handling

### 4. Data Integrity
- Comprehensive timestamp tracking (created/modified)
- Version history maintenance
- Automatic pruning of invalid entries
- Cache optimization for performance

## Key Constraints
- GitHub API rate limiting (200 requests default)
- Eagle plugin format requirements (.eagleplugin files)
- GitHub Actions bot deployment requirement
- JSON-based storage format
- Community-driven submission process

## Success Criteria
- Automated verification of plugin repositories
- Reliable index maintenance with minimal manual intervention
- Clear audit trail for all changes
- Scalable system supporting community growth
- Robust error handling and recovery

## Repository Structure
```
eagle-community-index/
├── scripts/           # Python automation scripts
├── .github/workflows/ # GitHub Actions workflows
├── index/            # JSON index files
├── configs/          # Configuration and blacklists
└── memory-bank/      # Project documentation
```

## Key Stakeholders
- Eagle plugin developers (repository submitters)
- Eagle user community (plugin consumers)
- Index maintainers (automated systems)
- Project maintainers (oversight and configuration)