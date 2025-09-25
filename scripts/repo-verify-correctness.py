#!/usr/bin/env python3
"""
Repository verification script for Eagle Community Index.

This script verifies that a repository meets the requirements:
1. Latest release is uploaded by github-actions[bot] 
2. Release contains .eagleplugin files
3. Repository has GitHub Actions configured
"""

import requests
import sys
import json
import base64
from typing import List, Tuple


class RepoVerifier:
    """Verifies repository compliance with Eagle Community Index requirements."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set User-Agent to avoid rate limiting
        self.session.headers.update({
            'User-Agent': 'eagle-community-index-verifier/1.0'
        })
    
    def verify_repo(self, repo_name: str) -> Tuple[bool, List[str]]:
        """
        Verify a repository meets all requirements.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        try:
            # Check latest release
            release_valid, release_issues = self._check_latest_release(repo_name)
            if not release_valid:
                issues.extend(release_issues)
            
            # Check GitHub Actions
            actions_valid, actions_issues = self._check_github_actions(repo_name)
            if not actions_valid:
                issues.extend(actions_issues)
            
            # Check for manifest.json
            manifest_valid, manifest_issues = self._check_manifest_json(repo_name)
            if not manifest_valid:
                issues.extend(manifest_issues)
                
        except Exception as e:
            issues.append(f"Error verifying repository: {str(e)}")
            return False, issues
        
        return len(issues) == 0, issues
    
    def _check_latest_release(self, repo_name: str) -> Tuple[bool, List[str]]:
        """Check if latest release meets requirements."""
        issues = []
        
        # Fetch latest release
        url = f"https://api.github.com/repos/{repo_name}/releases"
        response = self.session.get(url)
        
        if response.status_code == 404:
            issues.append("Repository not found or no access")
            return False, issues
        elif response.status_code != 200:
            issues.append(f"Failed to fetch releases: HTTP {response.status_code}")
            return False, issues
        
        releases = response.json()
        
        if not releases:
            issues.append("No releases found")
            return False, issues
        
        latest_release = releases[0]
        
        # Check if uploader is github-actions[bot]
        author = latest_release.get('author', {})
        author_login = author.get('login', '')
        
        if author_login != 'github-actions[bot]':
            issues.append(f"Latest release not uploaded by github-actions[bot] (found: {author_login})")
        
        # Check if release contains .eagleplugin files
        assets = latest_release.get('assets', [])
        has_eagleplugin = False
        
        for asset in assets:
            download_url = asset.get('browser_download_url', '')
            if '.eagleplugin' in download_url:
                has_eagleplugin = True
                break
        
        if not has_eagleplugin:
            issues.append("Release does not contain .eagleplugin files")
        
        return len(issues) == 0, issues
    
    def _check_github_actions(self, repo_name: str) -> Tuple[bool, List[str]]:
        """Check if repository has GitHub Actions configured."""
        issues = []
        
        # Check for workflows in the repository
        url = f"https://api.github.com/repos/{repo_name}/actions/workflows"
        response = self.session.get(url)
        
        if response.status_code == 404:
            issues.append("Cannot access repository workflows")
            return False, issues
        elif response.status_code != 200:
            issues.append(f"Failed to fetch workflows: HTTP {response.status_code}")
            return False, issues
        
        workflows = response.json()
        workflow_list = workflows.get('workflows', [])
        
        if not workflow_list:
            issues.append("No GitHub Actions workflows found")
            return False, issues
        
        return True, issues
    
    def _check_manifest_json(self, repo_name: str) -> Tuple[bool, List[str]]:
        """Check if manifest.json exists at the root of the repository and is valid JSON."""
        issues = []
        
        # Check for manifest.json at the root
        url = f"https://api.github.com/repos/{repo_name}/contents/manifest.json"
        response = self.session.get(url)
        
        if response.status_code == 404:
            issues.append("manifest.json file not found at repository root")
            return False, issues
        elif response.status_code != 200:
            issues.append(f"Failed to check manifest.json: HTTP {response.status_code}")
            return False, issues
        
        # File exists, now validate JSON content
        try:
            file_data = response.json()
            content = file_data.get('content', '')
            
            # Decode base64 content
            decoded_content = base64.b64decode(content).decode('utf-8')
            
            # Try to parse as JSON
            content = json.loads(decoded_content)

            # has valid fields
            assert 'name' in content, "manifest.json missing 'name' field"
            assert 'version' in content, "manifest.json missing 'version' field"
            assert 'id' in content, "manifest.json missing 'id' field"

        except (KeyError, ValueError, json.JSONDecodeError, AssertionError) as e:
            issues.append(f"manifest.json contains invalid JSON: {str(e)}")
            return False, issues
        except Exception as e:
            issues.append(f"Failed to validate manifest.json: {str(e)}")
            return False, issues
        
        # File exists and contains valid JSON
        return True, issues


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: python repo-verify-correctness.py <owner/repo>")
        print("Example: python repo-verify-correctness.py eagle-cooler/eagle-webdav")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    
    # Validate repo name format
    if '/' not in repo_name or repo_name.count('/') != 1:
        print("Error: Repository name must be in format 'owner/repo'")
        sys.exit(1)
    
    print(f"Verifying repository: {repo_name}")
    print("-" * 50)
    
    verifier = RepoVerifier()
    is_valid, issues = verifier.verify_repo(repo_name)
    
    if is_valid:
        print("✅ Repository verification PASSED")
        print("All requirements met:")
        print("  - Latest release uploaded by github-actions[bot]")
        print("  - Release contains .eagleplugin files") 
        print("  - GitHub Actions are configured")
        print("  - manifest.json exists at repository root and contains valid JSON")
    else:
        print("❌ Repository verification FAILED")
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
