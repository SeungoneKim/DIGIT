#!/usr/bin/env python3
"""
OpenHands API-based Research Paper Reviewer

This script uses the OpenHands API to conduct systematic peer review of research papers,
focusing on validity and methodology assessment with concrete evidence-based criticisms.
"""

import json
import asyncio
import aiohttp
import argparse
import sys
from typing import Dict, List, Any
from pathlib import Path


class OpenHandsPaperReviewer:
    """
    A class to conduct systematic peer review using OpenHands API
    """
    
    def __init__(self, api_base_url: str = "http://localhost:3000", api_key: str = None):
        """
        Initialize the reviewer with OpenHands API configuration
        
        Args:
            api_base_url: Base URL for OpenHands API
            api_key: API key for authentication (if required)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _create_review_prompt(self, paper_data: Dict[str, Any]) -> str:
        """
        Create the comprehensive review prompt based on paper data
        
        Args:
            paper_data: Dictionary containing paper content and metadata
            
        Returns:
            Formatted prompt string for the review task
        """
        
        prompt = f"""Your task is to assess a research paper based on its content and the code. The evaluation criteria are two fold:
1. Validity: Does the manuscript have flaws which should prohibit its publication? If so, please provide details.
2. Data and methodology: Please comment on the validity of the approach, quality of the data and quality of presentation. Please note that we expect our reviewers to review all data, including any extended data and supplementary information. Is the reporting of data and methodology sufficiently detailed and transparent to enable reproducing the results?

-> You may criticize up to 10 aspects, where we denote each aspect as an "item". An item should be consisted of a claim and an evidence. Each claim within an item should be a criticism of the paper with respect to the evaluation criteria and an evidence should be either a citation (e.g., There is a contradiction of the paper's XXX claim or XXX findings when contrasting with this other paper XXX) or an experimental result that you acquire by running the source code of this paper (e.g., I've ran the XXX file with the command line XXX and got XXX results, which do not match with the results in the paper).

I will provide you the paper's extracted content, where some are provided as a url (e.g., images). You should conduct this task by downloading and reading the files from the given url or reading the text.

Paper content:
```
{json.dumps(paper_data, indent=2)}
```

Please conduct a systematic review following these steps:

1. **Setup and Code Analysis**: Clone and analyze the provided code repository
2. **Content Analysis**: Examine the paper content, figures, and methodology
3. **Literature Review**: Compare claims with established literature
4. **Reproducibility Testing**: Attempt to reproduce key results
5. **Critical Assessment**: Document 10 specific items with concrete evidence

For each critical item, provide:
- **Claim**: Specific statement from the paper being criticized
- **Evidence**: Concrete evidence from code execution, literature citations, or experimental analysis
- **Impact**: Assessment of how this affects the paper's validity

Include a References section with citations to support your criticisms.

Focus on providing concrete, evidence-based assessments rather than surface-level feedback."""

        return prompt
    
    async def start_session(self) -> str:
        """
        Start a new OpenHands session
        
        Returns:
            Session ID for the created session
        """
        url = f"{self.api_base_url}/api/sessions"
        headers = self._prepare_headers()
        
        payload = {
            "agent": "CodeActAgent",
            "args": {
                "model_name": "anthropic/claude-3-5-sonnet-20241022",
                "max_iterations": 100
            }
        }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Failed to start session: {response.status} - {await response.text()}")
            
            data = await response.json()
            return data["session_id"]
    
    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message to the OpenHands session
        
        Args:
            session_id: The session ID
            message: The message to send
            
        Returns:
            Response from the API
        """
        url = f"{self.api_base_url}/api/sessions/{session_id}/messages"
        headers = self._prepare_headers()
        
        payload = {
            "message": message,
            "message_type": "user"
        }
        
        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Failed to send message: {response.status} - {await response.text()}")
            
            return await response.json()
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the current status of a session
        
        Args:
            session_id: The session ID
            
        Returns:
            Session status information
        """
        url = f"{self.api_base_url}/api/sessions/{session_id}/status"
        headers = self._prepare_headers()
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to get session status: {response.status} - {await response.text()}")
            
            return await response.json()
    
    async def wait_for_completion(self, session_id: str, timeout: int = 3600) -> bool:
        """
        Wait for the session to complete processing
        
        Args:
            session_id: The session ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if completed successfully, False if timeout
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = await self.get_session_status(session_id)
            
            if status.get("status") == "completed":
                return True
            elif status.get("status") == "error":
                raise Exception(f"Session failed with error: {status.get('error', 'Unknown error')}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        return False
    
    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a session
        
        Args:
            session_id: The session ID
            
        Returns:
            List of messages from the session
        """
        url = f"{self.api_base_url}/api/sessions/{session_id}/messages"
        headers = self._prepare_headers()
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to get messages: {response.status} - {await response.text()}")
            
            data = await response.json()
            return data.get("messages", [])
    
    async def review_paper(self, paper_data: Dict[str, Any], output_dir: str = "./review_output") -> Dict[str, Any]:
        """
        Conduct a complete paper review
        
        Args:
            paper_data: Dictionary containing paper content and metadata
            output_dir: Directory to save review outputs
            
        Returns:
            Dictionary containing review results and metadata
        """
        print("Starting paper review...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Start session
        session_id = await self.start_session()
        print(f"Started session: {session_id}")
        
        # Create and send review prompt
        prompt = self._create_review_prompt(paper_data)
        
        print("Sending review prompt...")
        await self.send_message(session_id, prompt)
        
        # Wait for completion
        print("Waiting for review completion...")
        completed = await self.wait_for_completion(session_id)
        
        if not completed:
            raise Exception("Review timed out")
        
        # Get all messages
        messages = await self.get_session_messages(session_id)
        
        # Extract review content
        review_content = self._extract_review_content(messages)
        
        # Save results
        results = {
            "session_id": session_id,
            "paper_title": paper_data.get("title", "Unknown"),
            "review_content": review_content,
            "messages": messages
        }
        
        # Save to files
        with open(output_path / "review_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Extract and save critical assessment if available
        if "critical_assessment.md" in review_content:
            with open(output_path / "critical_assessment.md", "w") as f:
                f.write(review_content["critical_assessment.md"])
        
        print(f"Review completed. Results saved to {output_dir}")
        return results
    
    def _extract_review_content(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract review content from session messages
        
        Args:
            messages: List of messages from the session
            
        Returns:
            Dictionary containing extracted review content
        """
        content = {}
        
        for message in messages:
            if message.get("message_type") == "assistant":
                # Look for file creation or content
                msg_content = message.get("content", "")
                
                # Extract markdown files or other relevant content
                if "critical_assessment.md" in msg_content:
                    content["critical_assessment.md"] = msg_content
                
                # Store the final assistant response
                content["final_response"] = msg_content
        
        return content


async def main():
    """Main function to run the paper reviewer"""
    parser = argparse.ArgumentParser(description="OpenHands Research Paper Reviewer")
    parser.add_argument("--paper-file", required=True, help="JSON file containing paper data")
    parser.add_argument("--api-url", default="http://localhost:3000", help="OpenHands API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--output-dir", default="./review_output", help="Output directory for review results")
    
    args = parser.parse_args()
    
    # Load paper data
    try:
        with open(args.paper_file, 'r') as f:
            paper_data = json.load(f)
    except Exception as e:
        print(f"Error loading paper file: {e}")
        sys.exit(1)
    
    # Conduct review
    try:
        async with OpenHandsPaperReviewer(args.api_url, args.api_key) as reviewer:
            results = await reviewer.review_paper(paper_data, args.output_dir)
            
            print("\n" + "="*50)
            print("REVIEW COMPLETED SUCCESSFULLY")
            print("="*50)
            print(f"Paper: {results['paper_title']}")
            print(f"Session ID: {results['session_id']}")
            print(f"Output saved to: {args.output_dir}")
            
    except Exception as e:
        print(f"Error during review: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())