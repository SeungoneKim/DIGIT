#!/usr/bin/env python3
"""
Batch Paper Reviewer

This script processes multiple papers in batch using the OpenHands API.
Useful for reviewing multiple papers or conducting comparative studies.
"""

import json
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from paper_reviewer import OpenHandsPaperReviewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_review.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchPaperReviewer:
    """
    Batch processor for multiple paper reviews
    """
    
    def __init__(self, api_url: str = "http://localhost:3000", api_key: str = None, 
                 max_concurrent: int = 2):
        """
        Initialize batch reviewer
        
        Args:
            api_url: OpenHands API URL
            api_key: API key for authentication
            max_concurrent: Maximum concurrent reviews
        """
        self.api_url = api_url
        self.api_key = api_key
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def review_single_paper(self, paper_file: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Review a single paper with concurrency control
        
        Args:
            paper_file: Path to paper JSON file
            output_dir: Output directory for this paper
            
        Returns:
            Review results dictionary
        """
        async with self.semaphore:
            logger.info(f"Starting review of {paper_file.name}")
            
            try:
                # Load paper data
                with open(paper_file, 'r') as f:
                    paper_data = json.load(f)
                
                # Create paper-specific output directory
                paper_output_dir = output_dir / paper_file.stem
                paper_output_dir.mkdir(exist_ok=True)
                
                # Conduct review
                async with OpenHandsPaperReviewer(self.api_url, self.api_key) as reviewer:
                    results = await reviewer.review_paper(paper_data, str(paper_output_dir))
                    
                logger.info(f"Completed review of {paper_file.name}")
                return {
                    "paper_file": str(paper_file),
                    "output_dir": str(paper_output_dir),
                    "status": "success",
                    "results": results
                }
                
            except Exception as e:
                logger.error(f"Failed to review {paper_file.name}: {e}")
                return {
                    "paper_file": str(paper_file),
                    "output_dir": str(output_dir / paper_file.stem),
                    "status": "error",
                    "error": str(e)
                }
    
    async def review_batch(self, paper_files: List[Path], output_dir: Path) -> Dict[str, Any]:
        """
        Review multiple papers in batch
        
        Args:
            paper_files: List of paper JSON files
            output_dir: Base output directory
            
        Returns:
            Batch results summary
        """
        logger.info(f"Starting batch review of {len(paper_files)} papers")
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Process papers concurrently
        tasks = [
            self.review_single_paper(paper_file, output_dir)
            for paper_file in paper_files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = []
        failed = []
        
        for result in results:
            if isinstance(result, Exception):
                failed.append({"error": str(result), "status": "exception"})
            elif result["status"] == "success":
                successful.append(result)
            else:
                failed.append(result)
        
        # Create summary
        summary = {
            "total_papers": len(paper_files),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(paper_files) * 100,
            "successful_reviews": successful,
            "failed_reviews": failed
        }
        
        # Save batch summary
        with open(output_dir / "batch_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Batch review completed: {len(successful)}/{len(paper_files)} successful")
        return summary
    
    def generate_comparative_report(self, batch_results: Dict[str, Any], output_dir: Path):
        """
        Generate a comparative report across multiple papers
        
        Args:
            batch_results: Results from batch review
            output_dir: Output directory
        """
        logger.info("Generating comparative report")
        
        report_lines = [
            "# Comparative Paper Review Report",
            "",
            f"## Summary",
            f"- Total papers reviewed: {batch_results['total_papers']}",
            f"- Successful reviews: {batch_results['successful']}",
            f"- Failed reviews: {batch_results['failed']}",
            f"- Success rate: {batch_results['success_rate']:.1f}%",
            "",
            "## Individual Paper Results",
            ""
        ]
        
        # Add results for each successful paper
        for result in batch_results["successful_reviews"]:
            paper_name = Path(result["paper_file"]).stem
            paper_title = result["results"].get("paper_title", "Unknown")
            
            report_lines.extend([
                f"### {paper_name}",
                f"**Title**: {paper_title}",
                f"**Status**: ✅ Success",
                f"**Output**: {result['output_dir']}",
                ""
            ])
        
        # Add failed papers
        if batch_results["failed_reviews"]:
            report_lines.extend([
                "## Failed Reviews",
                ""
            ])
            
            for result in batch_results["failed_reviews"]:
                paper_name = Path(result["paper_file"]).stem if "paper_file" in result else "Unknown"
                error = result.get("error", "Unknown error")
                
                report_lines.extend([
                    f"### {paper_name}",
                    f"**Status**: ❌ Failed",
                    f"**Error**: {error}",
                    ""
                ])
        
        # Save report
        with open(output_dir / "comparative_report.md", "w") as f:
            f.write("\n".join(report_lines))
        
        logger.info("Comparative report generated")


async def main():
    """Main function for batch paper reviewer"""
    parser = argparse.ArgumentParser(description="Batch OpenHands Research Paper Reviewer")
    parser.add_argument("--papers-dir", required=True, help="Directory containing paper JSON files")
    parser.add_argument("--api-url", default="http://localhost:3000", help="OpenHands API base URL")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--output-dir", default="./batch_review_output", help="Output directory")
    parser.add_argument("--max-concurrent", type=int, default=2, help="Maximum concurrent reviews")
    parser.add_argument("--pattern", default="*.json", help="File pattern for paper files")
    
    args = parser.parse_args()
    
    # Find paper files
    papers_dir = Path(args.papers_dir)
    if not papers_dir.exists():
        logger.error(f"Papers directory does not exist: {papers_dir}")
        sys.exit(1)
    
    paper_files = list(papers_dir.glob(args.pattern))
    if not paper_files:
        logger.error(f"No paper files found in {papers_dir} matching {args.pattern}")
        sys.exit(1)
    
    logger.info(f"Found {len(paper_files)} paper files")
    
    # Create batch reviewer
    batch_reviewer = BatchPaperReviewer(
        api_url=args.api_url,
        api_key=args.api_key,
        max_concurrent=args.max_concurrent
    )
    
    # Run batch review
    try:
        output_dir = Path(args.output_dir)
        results = await batch_reviewer.review_batch(paper_files, output_dir)
        
        # Generate comparative report
        batch_reviewer.generate_comparative_report(results, output_dir)
        
        print("\n" + "="*60)
        print("BATCH REVIEW COMPLETED")
        print("="*60)
        print(f"Total papers: {results['total_papers']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success rate: {results['success_rate']:.1f}%")
        print(f"Results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Batch review failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())