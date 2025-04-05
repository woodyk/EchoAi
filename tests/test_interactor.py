import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../echoai')))
from interactor import Interactor

def mock_function(param1: str, param2: int) -> str:
    """Mock function for testing."""
    return f"Received {param1} and {param2}"

class TestInteractor(unittest.TestCase):

    def setUp(self):
        api_key = os.getenv("OPENAI_API_KEY", "test_key")
        self.interactor = Interactor(api_key=api_key, model="openai:gpt-4o-mini")

    def test_initialization(self):
        self.assertEqual(self.interactor.model, "gpt-4o-mini")
        self.assertTrue(self.interactor.stream)
        self.assertEqual(self.interactor.context_length, 16000)

    def test_add_function(self):
        self.interactor.add_function(mock_function, name="mock_function")
        self.assertIn("mock_function", dir(self.interactor))
        self.assertEqual(len(self.interactor.get_functions()), 1)

    def test_interact(self):
        self.interactor.add_function(mock_function, name="mock_function")
        response = self.interactor.interact(user_input="Test input", tools=False, stream=False)
        self.assertIsNotNone(response)

    def test_messages_system(self):
        system_message = "You are a test assistant."
        self.interactor.messages_system(system_message)
        self.assertEqual(self.interactor.history[0]["content"], system_message)

    def test_messages_flush(self):
        self.interactor.messages_add(role="user", content="Test message")
        self.interactor.messages_flush()
        self.assertEqual(len(self.interactor.history), 1)  # Only system message remains

if __name__ == "__main__":
    unittest.main()