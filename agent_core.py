import os
import json
import tempfile
import shutil
from google import genai
from google.genai import types
import git
from tools import DevOpsTools

SYSTEM_PROMPT = """You are an expert DevOps Auditing Agent. Your job is to autonomously inspect a given code repository to identify genuine DevOps best-practice violations across categories like repository hygiene, dependency management, code quality, testing, CI/CD pipelines, security credentials, and configuration management.

You must follow an iterative loop: Observe -> Reason -> Select Tool -> Execute Tool -> Interpret Results -> Report.
- Do NOT treat absent optional files as proof of a defect.
- Distinguish acceptable alternatives from genuine defects.
- When you have gathered enough evidence, produce your final JSON report matching the required schema precisely.
"""

REPORT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "repository": {"type": "STRING"},
        "violations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "rule_id": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "severity": {"type": "STRING", "enum": ["critical", "high", "medium", "low"]},
                    "file": {"type": "STRING"},
                    "line": {"type": ["INTEGER", "NULL"]},
                    "description": {"type": "STRING"},
                    "evidence": {"type": "STRING"},
                    "recommendation": {"type": "STRING"}
                },
                "required": ["rule_id", "category", "severity", "file", "line", "description", "evidence", "recommendation"]
            }
        }
    },
    "required": ["repository", "violations"]
}

class DevOpsAuditingAgent:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.temp_dir = None
        self.tools = None

    def _clone_repo(self) -> str:
        self.temp_dir = tempfile.mkdtemp(prefix="devops_audit_")
        git.Repo.clone_from(self.repo_url, self.temp_dir, depth=50)
        return self.temp_dir

    def run(self) -> dict:
        local_path = self._clone_repo()
        self.tools = DevOpsTools(local_path)

        # Define tool declarations for Gemini Function Calling
        tool_declarations = [
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="list_files",
                    description="Discover all files and directory structure in the repository.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={})
                ),
                types.FunctionDeclaration(
                    name="read_file",
                    description="Read the contents of a specific file path relative to repo root.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={"path": types.Schema(type=types.Type.STRING, description="Relative path to the file.")},
                        required=["path"]
                    )
                ),
                types.FunctionDeclaration(
                    name="search_code",
                    description="Search for a suspicious pattern or keyword string across the codebase.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={"pattern": types.Schema(type=types.Type.STRING, description="Search query string.")},
                        required=["pattern"]
                    )
                ),
                types.FunctionDeclaration(
                    name="git_log",
                    description="Inspect recent commit history.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={"max_count": types.Schema(type=types.Type.INTEGER, description="Max commits to fetch.")}
                    )
                )
            ])
        ]

        chat = self.client.chats.create(model="gemini-3.8-flash")
        
        initial_message = (
            f"Please audit the repository located at {self.repo_url}. "
            "Start by listing the repository files to understand its layout, inspect high-risk files "
            "(such as configurations, CI workflows, lockfiles, and code entrypoints), search for security "
            "or hygiene issues, and output the final audit report."
        )

        response = chat.send_message(
            initial_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tool_declarations,
                temperature=0.1
            )
        )

        # Autonomous Agent Execution Loop
        max_turns = 10
        turn_count = 0

        while turn_count < max_turns and response.function_calls:
            turn_count += 1
            function_call = response.function_calls[0]
            func_name = function_call.name
            func_args = function_call.args

            # Execute tool locally
            tool_output = ""
            try:
                if func_name == "list_files":
                    tool_output = json.dumps(self.tools.list_files())
                elif func_name == "read_file":
                    tool_output = self.tools.read_file(func_args.get("path"))
                elif func_name == "search_code":
                    tool_output = self.tools.search_code(func_args.get("pattern"))
                elif func_name == "git_log":
                    max_c = int(func_args.get("max_count", 20))
                    tool_output = self.tools.git_log(max_c)
                else:
                    tool_output = f"Error: Unknown tool {func_name}"
            except Exception as e:
                tool_output = f"Error executing tool {func_name}: {str(e)}"

            # Feed tool results back to the model
            response = chat.send_message(
                types.Part.from_function_response(
                    name=func_name,
                    response={"result": tool_output}
                ),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=tool_declarations,
                    temperature=0.1
                )
            )

        # Request final structured JSON output from the model
        final_prompt = (
            "Based on your investigation, now generate the final JSON report according to the required schema. "
            "Ensure all violations are fully supported by evidence."
        )
        
        final_response = self.client.models.generate_content(
            model="gemini-3.8-flash",
            contents=chat.get_history() + [types.Part.from_text(text=final_prompt)],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=REPORT_SCHEMA,
                temperature=0.0
            )
        )

        # Cleanup temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        try:
            return json.loads(final_response.text)
        except json.JSONDecodeError:
            return {
                "repository": self.repo_url,
                "violations": []
            }