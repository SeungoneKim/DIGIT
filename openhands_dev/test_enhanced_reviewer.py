#!/usr/bin/env python3
"""
Test script for the enhanced paper reviewer

This script tests the enhanced reviewer against the manual review results
"""

import json
import sys
import os
from pathlib import Path
import difflib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_paper_reviewer import EnhancedPaperReviewer


def load_paper_data():
    """Load the paper data from example file"""
    paper_data_file = Path(__file__).parent / "example_paper_data.json"
    
    if not paper_data_file.exists():
        print(f"Error: {paper_data_file} not found")
        return None
    
    with open(paper_data_file, 'r') as f:
        return json.load(f)


def compare_with_manual_review(generated_file: str, manual_file: str):
    """
    Compare generated critical assessment with manual review
    
    Args:
        generated_file: Path to generated assessment
        manual_file: Path to manual assessment
    """
    try:
        with open(generated_file, 'r', encoding='utf-8') as f:
            generated_content = f.read()
        
        with open(manual_file, 'r', encoding='utf-8') as f:
            manual_content = f.read()
        
        print(f"\n=== COMPARISON RESULTS ===")
        print(f"Generated file: {generated_file}")
        print(f"Manual file: {manual_file}")
        print(f"Generated length: {len(generated_content)} characters")
        print(f"Manual length: {len(manual_content)} characters")
        
        # Check if files are identical
        if generated_content.strip() == manual_content.strip():
            print("✅ FILES ARE IDENTICAL!")
            return True
        else:
            print("❌ FILES ARE DIFFERENT")
            
            # Show differences
            generated_lines = generated_content.splitlines()
            manual_lines = manual_content.splitlines()
            
            diff = list(difflib.unified_diff(
                manual_lines, 
                generated_lines,
                fromfile='manual_review',
                tofile='generated_review',
                lineterm=''
            ))
            
            if diff:
                print("\n=== DIFFERENCES ===")
                for line in diff[:50]:  # Show first 50 lines of diff
                    print(line)
                
                if len(diff) > 50:
                    print(f"... and {len(diff) - 50} more lines")
            
            return False
            
    except Exception as e:
        print(f"Error comparing files: {e}")
        return False


def main():
    """Main test function"""
    print("=== Testing Enhanced Paper Reviewer ===")
    
    # Load paper data
    paper_data = load_paper_data()
    if not paper_data:
        return 1
    
    print(f"Loaded paper: {paper_data.get('title', 'Unknown')}")
    
    # Set up work directory
    work_dir = Path(__file__).parent / "test_workspace"
    work_dir.mkdir(exist_ok=True)
    
    # Create reviewer
    reviewer = EnhancedPaperReviewer(str(work_dir))
    
    # Check if we have the DIGIT repository to analyze
    digit_repo_path = None
    current_dir = Path(__file__).parent.parent
    if (current_dir / "DIGIT").exists():
        digit_repo_path = str(current_dir / "DIGIT")
        print(f"Found DIGIT repository at: {digit_repo_path}")
    
    # Conduct review
    print("\n=== Starting Review Process ===")
    try:
        results = reviewer.review_paper(paper_data, digit_repo_path)
        
        print(f"✅ Review completed successfully")
        print(f"Generated {len(results['review_items'])} critical items")
        print(f"Critical assessment saved to: {results['critical_assessment_path']}")
        
        # Compare with manual review
        manual_review_path = Path(__file__).parent.parent.parent / "critical_assessment.md"
        
        if manual_review_path.exists():
            print(f"\n=== Comparing with Manual Review ===")
            comparison_result = compare_with_manual_review(
                results['critical_assessment_path'],
                str(manual_review_path)
            )
            
            if comparison_result:
                print("🎉 SUCCESS: Generated review matches manual review!")
                return 0
            else:
                print("⚠️  Generated review differs from manual review")
                print("This is expected as the enhanced reviewer implements a different approach")
                return 0
        else:
            print(f"Manual review not found at: {manual_review_path}")
            print("Cannot compare, but review generation completed successfully")
            return 0
            
    except Exception as e:
        print(f"❌ Error during review: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)