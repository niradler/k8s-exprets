import yaml
import subprocess
from abc import ABC, abstractmethod

class BaseTool(ABC):
    @abstractmethod
    def run(self, params):
        pass

class YAMLValidationTool(BaseTool):
    def run(self, params):
        """
        Validate the given YAML content.
        
        :param params: dict, should contain 'yaml_content' key with YAML content as a string
        :return: bool, True if valid, False otherwise
        """
        yaml_content = params.get('yaml_content', '')
        try:
            yaml.safe_load(yaml_content)
            return True
        except yaml.YAMLError as exc:
            print(f"YAML validation error: {exc}")
            return False

class KubectlCommandTool(BaseTool):
    def run(self, params):
        """
        Run a kubectl command.
        
        :param params: dict, should contain 'command' key with kubectl command to run
        :return: str, output of the command
        """
        command = params.get('command', '')
        try:
            result = subprocess.run(['kubectl'] + command.split(), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as exc:
            print(f"Error running kubectl command: {exc.stderr.decode('utf-8')}")
            return None