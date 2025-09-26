#!/usr/bin/env python3
"""
Index update script for Eagle Community Index.

This script updates existing entries in the Eagle Community Index:
1. Prunes entries not in alldex.json
2. Checks last modified timestamp
3. Updates versions with latest releases for recently modified entries
4. Respects rate limiting and batch size limits
"""

import requests
import sys
import json
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class IndexUpdater:
    """Updates entries in Eagle Community Index."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set User-Agent to avoid rate limiting
        self.session.headers.update({
            'User-Agent': 'eagle-community-index-updater/1.0'
        })
    
    def update_index(self, days_threshold: int = 3, max_updates: int = 200) -> Tuple[bool, List[str]]:
        """
        Update index entries.
        
        Args:
            days_threshold: Only update entries modified within this many days
            max_updates: Maximum number of entries to update (rate limiting)
            
        Returns:
            Tuple of (success, messages)
        """
        messages = []
        
        try:
            # Load alldex.json to get authoritative entry list
            alldex = self._load_alldex()
            if alldex is None:
                messages.append("Failed to load alldex.json")
                return False, messages
            
            messages.append(f"Loaded alldex.json with {len(alldex)} entries")
            
            # Process candidate and primary indices
            total_processed = 0
            total_updated = 0
            total_pruned = 0
            
            for index_type in ['candidate', 'primary']:
                if total_processed >= max_updates:
                    messages.append(f"Reached maximum update limit ({max_updates}), stopping")
                    break
                
                processed, updated, pruned, type_messages = self._update_index_file(
                    index_type, alldex, days_threshold, max_updates - total_processed
                )
                
                messages.extend(type_messages)
                total_processed += processed
                total_updated += updated
                total_pruned += pruned
            
            messages.append("\n📊 Update Summary:")
            messages.append(f"  - Total entries processed: {total_processed}")
            messages.append(f"  - Entries updated: {total_updated}")
            messages.append(f"  - Entries pruned: {total_pruned}")
            
            return True, messages
            
        except Exception as e:
            messages.append(f"Error updating index: {str(e)}")
            return False, messages
    
    def _load_alldex(self) -> Optional[Dict]:
        """Load alldex.json file."""
        try:
            with open('index/alldex.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _update_index_file(self, index_type: str, alldex: Dict, days_threshold: int, 
                          remaining_quota: int) -> Tuple[int, int, int, List[str]]:
        """
        Update a specific index file (candidate.json or primary.json).
        
        Returns:
            Tuple of (processed_count, updated_count, pruned_count, messages)
        """
        messages = []
        index_file = f'index/{index_type}.json'
        
        # Load index file
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
        except FileNotFoundError:
            messages.append(f"Index file {index_file} not found, skipping")
            return 0, 0, 0, messages
        except Exception as e:
            messages.append(f"Failed to load {index_file}: {str(e)}")
            return 0, 0, 0, messages
        
        messages.append(f"\n🔄 Processing {index_type}.json ({len(index_data)} entries)")
        
        # Track changes
        entries_to_remove = []
        entries_updated = 0
        entries_processed = 0
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        for plugin_id, entry_data in index_data.items():
            if entries_processed >= remaining_quota:
                messages.append(f"  Reached quota limit for {index_type}, stopping at {entries_processed} entries")
                break
            
            # Check if entry exists in alldex
            if plugin_id not in alldex:
                entries_to_remove.append(plugin_id)
                messages.append(f"  🗑️  Marking {plugin_id} for removal (not in alldex)")
                continue
            
            # Check if entry type matches alldex
            if alldex[plugin_id] != index_type:
                entries_to_remove.append(plugin_id)
                messages.append(f"  🔄 Marking {plugin_id} for removal (type changed to {alldex[plugin_id]})")
                continue
            
            # Check last modified date
            last_modified_str = entry_data.get('lastModified')
            if not last_modified_str:
                messages.append(f"  ⏭️  Skipping {plugin_id} (no lastModified timestamp)")
                entries_processed += 1
                continue
            
            try:
                # Parse ISO timestamp
                last_modified = datetime.fromisoformat(last_modified_str.replace('Z', '+00:00'))
                if last_modified < cutoff_date:
                    messages.append(f"  ⏭️  Skipping {plugin_id} (last modified {last_modified.strftime('%Y-%m-%d')}, older than {days_threshold} days)")
                    entries_processed += 1
                    continue
            except Exception:
                messages.append(f"  ⚠️  Skipping {plugin_id} (invalid lastModified timestamp)")
                entries_processed += 1
                continue
            
            # Entry is recent, check for updates
            repository = entry_data.get('repository')
            if not repository:
                messages.append(f"  ⚠️  Skipping {plugin_id} (no repository field)")
                entries_processed += 1
                continue
            
            # Fetch latest release
            latest_version = self._fetch_latest_release_version(repository)
            if not latest_version:
                messages.append(f"  ⚠️  Could not fetch latest release for {plugin_id} ({repository})")
                entries_processed += 1
                continue
            
            # Check if we need to update versions
            current_versions = entry_data.get('versions', [])
            if not current_versions or current_versions[0] != latest_version:
                # Update versions list
                if latest_version in current_versions:
                    # Move existing version to front
                    new_versions = [latest_version] + [v for v in current_versions if v != latest_version]
                else:
                    # Add new version to front
                    new_versions = [latest_version] + current_versions
                
                entry_data['versions'] = new_versions
                entry_data['lastModified'] = datetime.utcnow().isoformat() + 'Z'
                entries_updated += 1
                messages.append(f"  ✅ Updated {plugin_id} to version {latest_version}")
            else:
                messages.append(f"  ✓  {plugin_id} already up to date ({latest_version})")
            
            entries_processed += 1
        
        # Remove pruned entries
        for plugin_id in entries_to_remove:
            del index_data[plugin_id]
        
        # Save updated index file
        try:
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2, sort_keys=True)
            messages.append(f"  💾 Saved {index_file}")
        except Exception as e:
            messages.append(f"  ❌ Failed to save {index_file}: {str(e)}")
            return entries_processed, 0, len(entries_to_remove), messages
        
        return entries_processed, entries_updated, len(entries_to_remove), messages
    
    def _fetch_latest_release_version(self, repo_name: str) -> Optional[str]:
        """Fetch the latest release version from a repository."""
        url = f"https://api.github.com/repos/{repo_name}/releases"
        
        try:
            # Add 1 second delay to avoid rate limiting
            time.sleep(1)
            
            response = self.session.get(url)
            if response.status_code != 200:
                return None
            
            releases = response.json()
            if not releases:
                return None
            
            latest_release = releases[0]
            
            # Verify it's uploaded by github-actions[bot]
            author = latest_release.get('author', {})
            author_login = author.get('login', '')
            
            if author_login != 'github-actions[bot]':
                return None
            
            # Check if release contains .eagleplugin files
            assets = latest_release.get('assets', [])
            has_eagleplugin = any('.eagleplugin' in asset.get('browser_download_url', '') 
                               for asset in assets)
            
            if not has_eagleplugin:
                return None
            
            return latest_release.get('tag_name')
            
        except Exception:
            return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Update Eagle Community Index entries')
    parser.add_argument('--days', type=int, default=3,
                       help='Only update entries modified within this many days (default: 3)')
    parser.add_argument('--max-updates', type=int, default=200,
                       help='Maximum number of entries to process (default: 200)')
    
    args = parser.parse_args()
    
    print(f"🔄 Starting index update")
    print(f"  - Days threshold: {args.days}")
    print(f"  - Max updates: {args.max_updates}")
    print("-" * 50)
    
    updater = IndexUpdater()
    success, messages = updater.update_index(args.days, args.max_updates)
    
    # Print all messages
    for message in messages:
        print(message)
    
    if success:
        print("\n✅ Index update COMPLETED")
    else:
        print("\n❌ Index update FAILED")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()