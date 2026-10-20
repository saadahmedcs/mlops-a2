import unittest
from unittest.mock import patch, MagicMock
from agent_core import DevOpsAuditingAgent

class TestDevOpsAuditingAgent(unittest.TestCase):
    
    @patch("agent_core.genai.Client")
    @patch("agent_core.git.Repo.clone_from")
    def test_agent_initialization_and_mock_run(self, mock_clone, mock_genai_client):
        # Setup mock behavior
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        # Mock chat response returning no function calls to immediately conclude
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = []
        mock_chat.send_message.return_value = mock_response
        mock_client_instance.chats.create.return_value = mock_chat
        
        # Mock final content generation
        mock_final_response = MagicMock()
        mock_final_response.text = '{"repository": "https://github.com/test/repo", "violations": []}'
        mock_client_instance.models.generate_content.return_value = mock_final_response

        agent = DevOpsAuditingAgent("https://github.com/test/repo")
        
        # Run agent (which uses mocks for git clone and API calls)
        # Note: We mock out clone_from so it doesn't actually hit network
        with patch("tempfile.mkdtemp", return_value="/tmp/mock_repo"):
            with patch("shutil.rmtree"):
                with patch("os.path.exists", return_value=True):
                    result = agent.run()

        self.assertEqual(result["repository"], "https://github.com/test/repo")
        self.assertEqual(result["violations"], [])