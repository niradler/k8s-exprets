import requests
import json
from typing import Dict

API_URL = "http://localhost:11434/api/generate"

class Agent:
    def __init__(self, model: str, name: str, responsibility: str):
        self.name = name
        self.responsibility = responsibility
        self.model = model

    def generate_prompt(self, user_query: str, context: Dict) -> str:
        """
        Create a prompt for the Llama 3 model based on the agent's responsibility and user query.
        """
        prompt = (
            f"Role: {self.name}\n"
            f"Responsibility: {self.responsibility}\n"
            f"Context: {json.dumps(context)}\n"
            f"User Query: {user_query}\n"
            f"Provide a detailed response in JSON format:"
        )
        return prompt

    def process(self, user_query: str, context: Dict) -> Dict:
        """
        Send the prompt to the Llama 3 model and return the JSON response.
        """
        prompt = self.generate_prompt(user_query, context)
        try:
            response = requests.post(
                API_URL,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                headers={}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"error": f"Request failed: {e}"}
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from model.")
            return {"error": "Invalid JSON response from model."}
