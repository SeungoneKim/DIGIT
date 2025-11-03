#!/usr/bin/env python3
"""
Review Tools for Paper Assessment

This module provides the actual implementation of tools needed for paper review,
including file downloading, web searching, code execution, and analysis.
"""

import os
import sys
import subprocess
import requests
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewTools:
    """
    Collection of tools for conducting paper reviews
    """
    
    def __init__(self, work_dir: str = "./review_workspace"):
        """
        Initialize review tools
        
        Args:
            work_dir: Working directory for downloads and analysis
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.downloads_dir = self.work_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        self.code_dir = self.work_dir / "code_analysis"
        self.code_dir.mkdir(exist_ok=True)
        
    def fetch_url(self, url: str, max_length: int = 5000, raw: bool = False) -> str:
        """
        Fetch content from a URL (simulates the fetch tool)
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
            raw: Whether to return raw HTML
            
        Returns:
            Content from the URL
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text if raw else response.text
            
            # Truncate if too long
            if len(content) > max_length:
                content = content[:max_length] + "\n[Content truncated...]"
                
            return content
            
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"
    
    def download_file(self, url: str, filename: Optional[str] = None) -> str:
        """
        Download a file from URL
        
        Args:
            url: URL to download
            filename: Optional filename, otherwise inferred from URL
            
        Returns:
            Path to downloaded file
        """
        try:
            if not filename:
                filename = url.split('/')[-1]
                if not filename or '.' not in filename:
                    filename = f"download_{int(time.time())}.pdf"
            
            filepath = self.downloads_dir / filename
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded {url} to {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"Error downloading {url}: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Simulate web search (simplified version of tavily search)
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        # This is a simplified simulation - in a real implementation,
        # you would integrate with a search API like Tavily, Google, or Bing
        
        logger.info(f"Simulating web search for: {query}")
        
        # Return simulated results that match the type of searches done in the manual review
        simulated_results = [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com/search-result",
                "content": f"This is a simulated search result for the query '{query}'. In a real implementation, this would return actual web search results from academic databases, Google Scholar, or other sources."
            }
        ]
        
        return simulated_results[:max_results]
    
    def execute_bash_command(self, command: str, cwd: Optional[str] = None) -> Tuple[str, int]:
        """
        Execute a bash command
        
        Args:
            command: Command to execute
            cwd: Working directory
            
        Returns:
            Tuple of (output, exit_code)
        """
        try:
            if cwd is None:
                cwd = str(self.code_dir)
            
            logger.info(f"Executing: {command} in {cwd}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            return output, result.returncode
            
        except subprocess.TimeoutExpired:
            return "Command timed out after 60 seconds", -1
        except Exception as e:
            return f"Error executing command: {str(e)}", -1
    
    def execute_python_code(self, code: str, cwd: Optional[str] = None) -> Tuple[str, int]:
        """
        Execute Python code
        
        Args:
            code: Python code to execute
            cwd: Working directory
            
        Returns:
            Tuple of (output, exit_code)
        """
        try:
            if cwd is None:
                cwd = str(self.code_dir)
            
            # Create a temporary Python file
            temp_file = self.code_dir / f"temp_code_{int(time.time())}.py"
            
            with open(temp_file, 'w') as f:
                f.write(code)
            
            logger.info(f"Executing Python code in {temp_file}")
            
            result = subprocess.run(
                [sys.executable, str(temp_file)],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            # Clean up temp file
            temp_file.unlink()
            
            return output, result.returncode
            
        except subprocess.TimeoutExpired:
            return "Python code execution timed out after 60 seconds", -1
        except Exception as e:
            return f"Error executing Python code: {str(e)}", -1
    
    def clone_repository(self, repo_url: str, target_dir: Optional[str] = None) -> str:
        """
        Clone a git repository
        
        Args:
            repo_url: Repository URL
            target_dir: Target directory name
            
        Returns:
            Path to cloned repository
        """
        try:
            if not target_dir:
                target_dir = repo_url.split('/')[-1].replace('.git', '')
            
            repo_path = self.code_dir / target_dir
            
            # Remove existing directory if it exists
            if repo_path.exists():
                shutil.rmtree(repo_path)
            
            command = f"git clone {repo_url} {target_dir}"
            output, exit_code = self.execute_bash_command(command, str(self.code_dir))
            
            if exit_code == 0:
                logger.info(f"Successfully cloned {repo_url} to {repo_path}")
                return str(repo_path)
            else:
                error_msg = f"Failed to clone repository: {output}"
                logger.error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error cloning repository: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def analyze_code_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a code file for issues
        
        Args:
            filepath: Path to code file
            
        Returns:
            Analysis results
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            analysis = {
                "filepath": filepath,
                "lines": len(content.split('\n')),
                "size_bytes": len(content.encode('utf-8')),
                "issues": [],
                "dependencies": [],
                "hardcoded_paths": []
            }
            
            lines = content.split('\n')
            
            # Look for common issues
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for hardcoded paths
                if '/home/' in line or 'C:\\' in line or 'Dropbox' in line:
                    analysis["hardcoded_paths"].append({
                        "line": i,
                        "content": line.strip(),
                        "issue": "Hardcoded path detected"
                    })
                
                # Check for imports/dependencies
                if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                    analysis["dependencies"].append(line.strip())
                
                # Check for file operations that might fail
                if 'loadmat(' in line or 'open(' in line:
                    analysis["issues"].append({
                        "line": i,
                        "content": line.strip(),
                        "type": "file_operation",
                        "description": "File operation that may fail if file doesn't exist"
                    })
            
            return analysis
            
        except Exception as e:
            return {
                "filepath": filepath,
                "error": f"Error analyzing file: {str(e)}"
            }
    
    def create_critical_assessment(self, paper_data: Dict[str, Any], 
                                 analysis_results: List[Dict[str, Any]]) -> str:
        """
        Create the critical assessment markdown file
        
        Args:
            paper_data: Paper information
            analysis_results: Results from various analyses
            
        Returns:
            Path to created critical assessment file
        """
        try:
            title = paper_data.get('title', 'Unknown Paper')
            
            # Create the critical assessment content
            content = f"""# Critical Assessment of "{title}"

## Summary of Findings

This paper presents {title}. Based on systematic analysis including code execution, literature review, and methodological assessment, several critical issues have been identified.

## Critical Assessment Items

"""
            
            # Add analysis results as items
            for i, result in enumerate(analysis_results, 1):
                content += f"""### Item {i}: {result.get('title', 'Analysis Result')}
**Claim**: {result.get('claim', 'No specific claim identified')}
**Evidence**: {result.get('evidence', 'Analysis conducted but no specific evidence generated')}

**Impact**: {result.get('impact', 'Impact assessment pending')}

"""
            
            # Add conclusion
            content += """## Conclusion

Based on the systematic analysis conducted, this paper requires significant revisions to address the identified methodological and reproducibility issues before it can be considered for publication.

## References

[References would be added based on literature search results]
"""
            
            # Save to file
            output_file = self.work_dir / "critical_assessment.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created critical assessment: {output_file}")
            return str(output_file)
            
        except Exception as e:
            error_msg = f"Error creating critical assessment: {str(e)}"
            logger.error(error_msg)
            return error_msg