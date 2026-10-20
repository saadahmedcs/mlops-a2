import argparse
import json
import sys
import os
from dotenv import load_dotenv
from agent_core import DevOpsAuditingAgent

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="AI-powered DevOps Repository Auditing Agent")
    parser.add_argument("--repo", required=True, help="Public GitHub repository URL")
    parser.add_argument("--output", required=True, help="Path to output JSON report file")
    
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting audit for repository: {args.repo}")
    try:
        agent = DevOpsAuditingAgent(repo_url=args.repo)
        report_data = agent.run()
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
            
        print(f"Audit completed successfully. Report written to {args.output}")
    except Exception as e:
        print(f"Fatal error during audit execution: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()