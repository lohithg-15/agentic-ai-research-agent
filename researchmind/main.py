"""
main.py — CLI Entry Point for ResearchMind

Usage:
    python -m researchmind.main --query "your research topic"
    python -m researchmind.main --query "transformer architecture in NLP" --output results
"""

import argparse
import asyncio
import sys

from researchmind.orchestrator import run_research


def main():
    parser = argparse.ArgumentParser(
        description="ResearchMind — AI-Powered Academic Literature Review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m researchmind.main --query "transformer architecture in NLP"
  python -m researchmind.main --query "reinforcement learning robotics" --output results
  python -m researchmind.main --query "gene editing CRISPR applications"
        """,
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="The research topic to investigate",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Output directory for results (default: output)",
    )

    args = parser.parse_args()

    if not args.query.strip():
        print("❌ Error: Query cannot be empty.")
        sys.exit(1)

    print(f"\n🚀 Starting ResearchMind...")
    print(f"📌 Topic: {args.query}")
    print(f"📁 Output: {args.output}/\n")

    # Run the async pipeline
    try:
        memory = asyncio.run(run_research(args.query, args.output))

        print(f"\n🎉 Done! Check {args.output}/ for your report:")
        print(f"   📄 {args.output}/research_report.md")
        print(f"   📊 {args.output}/research_output.json")

    except KeyboardInterrupt:
        print("\n\n⚠ Research interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
