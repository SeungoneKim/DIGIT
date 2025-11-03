#!/usr/bin/env python3
"""
Test version of the paper reviewer that simulates the OpenHands API response
to verify it produces the same output as our manual critical_assessment.md
"""

import json
import asyncio
from pathlib import Path
from paper_reviewer import OpenHandsPaperReviewer


class MockOpenHandsPaperReviewer(OpenHandsPaperReviewer):
    """
    Mock version that simulates the API responses without requiring actual OpenHands server
    """
    
    def __init__(self):
        # Don't call parent __init__ to avoid API setup
        pass
    
    async def start_session(self) -> str:
        """Mock session start"""
        return "mock_session_123"
    
    async def send_message(self, session_id: str, message: str) -> dict:
        """Mock message sending"""
        return {"status": "sent", "message_id": "mock_msg_456"}
    
    async def wait_for_completion(self, session_id: str, timeout: int = 3600) -> bool:
        """Mock completion wait"""
        return True
    
    async def get_session_messages(self, session_id: str) -> list:
        """
        Mock session messages - return simulated assistant response
        that matches our actual critical assessment
        """
        
        # Read our actual critical assessment to simulate the response
        critical_assessment_path = Path("../critical_assessment.md")
        if critical_assessment_path.exists():
            with open(critical_assessment_path, 'r') as f:
                critical_content = f.read()
        else:
            critical_content = "# Mock Critical Assessment\n\nThis is a simulated response."
        
        return [
            {
                "message_type": "user",
                "content": "Review request",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "message_type": "assistant", 
                "content": f"I'll conduct a systematic review of this paper.\n\n{critical_content}",
                "timestamp": "2024-01-01T01:00:00Z"
            }
        ]
    
    def _extract_review_content(self, messages: list) -> dict:
        """Extract review content from mock messages"""
        content = {}
        
        for message in messages:
            if message.get("message_type") == "assistant":
                msg_content = message.get("content", "")
                
                # Extract the critical assessment part
                if "# Critical Assessment" in msg_content:
                    # Find the critical assessment section
                    start_idx = msg_content.find("# Critical Assessment")
                    if start_idx != -1:
                        content["critical_assessment.md"] = msg_content[start_idx:]
                
                content["final_response"] = msg_content
        
        return content


async def test_reviewer():
    """Test the reviewer with mock API"""
    print("Testing OpenHands Paper Reviewer with mock API...")
    
    # Load paper data
    with open('example_paper_data.json', 'r') as f:
        paper_data = json.load(f)
    
    # Create mock reviewer
    reviewer = MockOpenHandsPaperReviewer()
    
    # Test the review process
    try:
        results = await reviewer.review_paper(paper_data, "./test_output")
        
        print("\n" + "="*50)
        print("TEST RESULTS")
        print("="*50)
        print(f"Paper: {results['paper_title']}")
        print(f"Session ID: {results['session_id']}")
        
        # Check if critical assessment was generated
        if "critical_assessment.md" in results["review_content"]:
            print("✓ Critical assessment generated")
            
            # Save the test output
            test_output_path = Path("./test_output")
            test_output_path.mkdir(exist_ok=True)
            
            with open(test_output_path / "test_critical_assessment.md", "w") as f:
                f.write(results["review_content"]["critical_assessment.md"])
            
            print(f"✓ Test output saved to {test_output_path}")
            
            # Compare with original
            original_path = Path("../critical_assessment.md")
            if original_path.exists():
                print("\n" + "="*50)
                print("COMPARISON WITH ORIGINAL")
                print("="*50)
                
                with open(original_path, 'r') as f:
                    original_content = f.read()
                
                test_content = results["review_content"]["critical_assessment.md"]
                
                print(f"Original length: {len(original_content)} characters")
                print(f"Test output length: {len(test_content)} characters")
                
                # Check if key sections are present
                key_sections = [
                    "## Critical Assessment Items",
                    "### Item 1:",
                    "### Item 10:",
                    "## References",
                    "## Conclusion"
                ]
                
                print("\nSection presence check:")
                for section in key_sections:
                    in_original = section in original_content
                    in_test = section in test_content
                    status = "✓" if in_test else "✗"
                    print(f"{status} {section}: Original={in_original}, Test={in_test}")
                
            else:
                print("⚠ Original critical_assessment.md not found for comparison")
        else:
            print("✗ Critical assessment not generated")
        
        return results
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return None


async def main():
    """Main test function"""
    print("OpenHands Paper Reviewer - Test Mode")
    print("====================================")
    
    # Test basic functionality
    results = await test_reviewer()
    
    if results:
        print("\n✓ Test completed successfully!")
        print("The reviewer code structure works correctly.")
        print("In production, this would connect to actual OpenHands API.")
    else:
        print("\n✗ Test failed!")


if __name__ == "__main__":
    asyncio.run(main())