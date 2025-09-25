#!/usr/bin/env python3
"""
Index entry creation script for Eagle Community Index.

This script creates or updates entries in the Eagle Community Index:
1. Verifies repository meets requirements
2. Fetches manifest.json and release information
3. Creates/updates entries         print("Files updated:")
        print("  - index/alldex.json")
        print(f"  - index/{entry_type}.json")alldex.json and candidates/primary.json
"""

import requests
import sys
import json
import base64
import re
from typing import Dict, List, Tuple, Optional


class IndexEntryCreator:
    """Creates and manages entries in Eagle Community Index."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set User-Agent to avoid rate limiting
        self.session.headers.update({
            'User-Agent': 'eagle-community-index-creator/1.0'
        })
    
    def create_entry(self, repo_name: str, entry_type: str, force_update: bool = False) -> Tuple[bool, List[str], Dict]:
        """
        Create or update an index entry.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            entry_type: "candidate" or "primary"
            force_update: Whether to update existing entries
            
        Returns:
            Tuple of (success, messages, entry_info)
        """
        messages = []
        entry_info = {}
        
        try:
            # Verify repository first
            from pathlib import Path
            verify_script = Path(__file__).parent / "repo-verify-correctness.py"
            
            import subprocess
            result = subprocess.run([sys.executable, str(verify_script), repo_name], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                messages.append(f"Repository verification failed: {result.stdout}")
                return False, messages, entry_info
            
            messages.append("Repository verification passed")
            
            # Fetch repository information
            manifest_data = self._fetch_manifest(repo_name)
            if not manifest_data:
                messages.append("Failed to fetch manifest.json")
                return False, messages, entry_info
            
            release_data = self._fetch_latest_release(repo_name)
            if not release_data:
                messages.append("Failed to fetch release information")
                return False, messages, entry_info
            
            # Extract plugin information
            plugin_id = manifest_data.get('id')
            plugin_name = manifest_data.get('name')
            plugin_description = manifest_data.get('description', '')
            manifest_version = manifest_data.get('version')
            
            if not plugin_id or not plugin_name:
                messages.append("manifest.json missing required fields (id or name)")
                return False, messages, entry_info
            
            # Create serialized name
            serialized_name = self._create_serialized_name(plugin_name)
            latest_version = release_data.get('tag_name', manifest_version)
            
            entry_info = {
                'plugin_id': plugin_id,
                'plugin_name': plugin_name,
                'plugin_description': plugin_description,
                'serialized_name': serialized_name,
                'latest_version': latest_version,
                'entry_type': entry_type
            }
            
            # Check if entry already exists
            existing_type = self._check_existing_entry(plugin_id)
            if existing_type and not force_update:
                messages.append(f"Entry already exists as '{existing_type}'. Use --force-update to override.")
                return False, messages, entry_info
            
            # Create/update the entry
            success = self._update_index_files(plugin_id, plugin_name, plugin_description, 
                                             serialized_name, latest_version, entry_type, existing_type)
            
            if success:
                action = "Updated" if existing_type else "Created"
                messages.append(f"{action} {entry_type} entry for {plugin_id}")
                return True, messages, entry_info
            else:
                messages.append("Failed to update index files")
                return False, messages, entry_info
                
        except Exception as e:
            messages.append(f"Error creating entry: {str(e)}")
            return False, messages, entry_info
    
    def _fetch_manifest(self, repo_name: str) -> Optional[Dict]:
        """Fetch and parse manifest.json from repository."""
        url = f"https://api.github.com/repos/{repo_name}/contents/manifest.json"
        response = self.session.get(url)
        
        if response.status_code != 200:
            return None
        
        try:
            file_data = response.json()
            content = file_data.get('content', '')
            decoded_content = base64.b64decode(content).decode('utf-8')
            return json.loads(decoded_content)
        except Exception:
            return None
    
    def _fetch_latest_release(self, repo_name: str) -> Optional[Dict]:
        """Fetch latest release information."""
        url = f"https://api.github.com/repos/{repo_name}/releases"
        response = self.session.get(url)
        
        if response.status_code != 200:
            return None
        
        try:
            releases = response.json()
            return releases[0] if releases else None
        except Exception:
            return None
    
    def _create_serialized_name(self, name: str) -> str:
        """Create serialized name from plugin name."""
        # Convert to lowercase, replace spaces with dots, remove non-alphanumeric except dots and dashes
        serialized = name.lower()
        serialized = re.sub(r'\s+', '.', serialized)  # spaces to dots
        serialized = re.sub(r'[^a-z0-9.-]', '', serialized)  # keep only alphanumeric, dots, dashes
        serialized = re.sub(r'\.+', '.', serialized)  # collapse multiple dots
        serialized = serialized.strip('.')  # remove leading/trailing dots
        return serialized
    
    def _check_existing_entry(self, plugin_id: str) -> Optional[str]:
        """Check if entry already exists in alldex.json."""
        try:
            with open('index/alldex.json', 'r') as f:
                alldex = json.load(f)
                return alldex.get(plugin_id)
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _update_index_files(self, plugin_id: str, name: str, description: str, 
                           serialized_name: str, latest_version: str, entry_type: str, 
                           existing_type: Optional[str]) -> bool:
        """Update alldex.json and the appropriate index file."""
        try:
            # Update alldex.json
            try:
                with open('index/alldex.json', 'r') as f:
                    alldex = json.load(f)
            except FileNotFoundError:
                alldex = {}
            
            alldex[plugin_id] = entry_type
            
            with open('index/alldex.json', 'w') as f:
                json.dump(alldex, f, indent=2, sort_keys=True)
            
            # Update the appropriate index file
            index_file = f'index/{entry_type}.json'
            
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
            except FileNotFoundError:
                index_data = {}
            
            # Create entry data
            entry_data = {
                'name': name,
                'description': description,
                'serializedName': serialized_name,
                'versions': [latest_version]
            }
            
            # If updating existing entry, merge versions
            if plugin_id in index_data:
                existing_versions = index_data[plugin_id].get('versions', [])
                # Add new version to front if not already present
                if latest_version not in existing_versions:
                    entry_data['versions'] = [latest_version] + existing_versions
                else:
                    # Move existing version to front
                    versions = [v for v in existing_versions if v != latest_version]
                    entry_data['versions'] = [latest_version] + versions
            
            index_data[plugin_id] = entry_data
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2, sort_keys=True)
            
            # If changing entry type, remove from old index
            if existing_type and existing_type != entry_type:
                old_index_file = f'index/{existing_type}.json'
                try:
                    with open(old_index_file, 'r') as f:
                        old_index_data = json.load(f)
                    
                    if plugin_id in old_index_data:
                        del old_index_data[plugin_id]
                        
                    with open(old_index_file, 'w') as f:
                        json.dump(old_index_data, f, indent=2, sort_keys=True)
                except FileNotFoundError:
                    pass
            
            return True
            
        except Exception as e:
            print(f"Error updating index files: {e}")
            return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 3:
        print("Usage: python create-index-entry.py <owner/repo> <candidate|primary> [--force-update]")
        print("Example: python create-index-entry.py eagle-cooler/eagle-webdav candidate")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    entry_type = sys.argv[2]
    force_update = '--force-update' in sys.argv
    
    # Validate inputs
    if '/' not in repo_name or repo_name.count('/') != 1:
        print("Error: Repository name must be in format 'owner/repo'")
        sys.exit(1)
    
    if entry_type not in ['candidate', 'primary']:
        print("Error: Entry type must be 'candidate' or 'primary'")
        sys.exit(1)
    
    print(f"Creating {entry_type} entry for repository: {repo_name}")
    if force_update:
        print("Force update enabled - will override existing entries")
    print("-" * 50)
    
    creator = IndexEntryCreator()
    success, messages, entry_info = creator.create_entry(repo_name, entry_type, force_update)
    
    # Print all messages
    for message in messages:
        print(f"  {message}")
    
    if success:
        print("\n✅ Index entry operation COMPLETED")
        print("Entry details:")
        print(f"  - Plugin ID: {entry_info.get('plugin_id')}")
        print(f"  - Plugin Name: {entry_info.get('plugin_name')}")
        print(f"  - Entry Type: {entry_info.get('entry_type')}")
        print(f"  - Latest Version: {entry_info.get('latest_version')}")
        print(f"  - Serialized Name: {entry_info.get('serialized_name')}")
        print("\nFiles updated:")
        print("  - index/alldex.json")
        print(f"  - index/{entry_type}.json")
    else:
        print("\n❌ Index entry operation FAILED")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()