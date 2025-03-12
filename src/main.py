from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import subprocess
import yaml
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class KubectlToolInput(BaseModel):
    """Input schema for KubectlTool."""
    command: str = Field(
        ..., description="The kubectl command to execute (e.g., 'apply -f file.yaml').")


class KubectlTool(BaseTool):
    name: str = "Kubectl Tool"
    description: str = "Executes kubectl commands to manage Kubernetes resources."
    args_schema: Type[BaseModel] = KubectlToolInput

    def _run(self, command: str) -> str:
        try:
            result = subprocess.run(
                f"kubectl {command}", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.decode('utf-8')}"


class YAMLValidatorToolInput(BaseModel):
    """Input schema for YAMLValidatorTool."""
    file_path: str = Field(...,
                           description="The path to the YAML file to validate.")


class YAMLValidatorTool(BaseTool):
    name: str = "YAML Validator Tool"
    description: str = "Validates Kubernetes YAML files for syntax and structure."
    args_schema: Type[BaseModel] = YAMLValidatorToolInput

    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as file:
                yaml.safe_load(file)
            return "YAML file is valid."
        except yaml.YAMLError as e:
            return f"Invalid YAML: {e}"


@CrewBase
class KubernetesCrew:
    def __init__(self):
        self.common_model = os.getenv("OPENAI_MODEL_NAME")  # ollama/llama3.2:3b

    @agent
    def classifier_agent(self) -> Agent:
        return Agent(
            role="Kubernetes Classifier",
            goal="Analyze user input and determine which Kubernetes agents should handle the request.",
            backstory="You classify Kubernetes-related requests and return a structured JSON list of relevant agents.",
            llm=LLM(model=self.common_model,
                    base_url="http://localhost:11434"),
            verbose=True,
            allow_delegation=False
        )

    @agent
    def admin_agent(self) -> Agent:
        return Agent(
            role="Kubernetes Administrator",
            goal="Manage Kubernetes cluster operations, including installation, upgrades, and maintenance.",
            backstory="You handle cluster administration tasks like node scaling, cluster setup, and maintenance.",
            llm=LLM(model=self.common_model,
                    base_url="http://localhost:11434"),
            verbose=True,
            # tools=[KubectlTool()]
        )

    @agent
    def ops_agent(self) -> Agent:
        return Agent(
            role="Kubernetes Operations Expert",
            goal="Debug, monitor, and optimize Kubernetes operations.",
            backstory="You provide expert-level debugging and operational support for Kubernetes workloads.",
            llm=LLM(model=self.common_model,
                    base_url="http://localhost:11434"),
            verbose=True,
            # tools=[KubectlTool()]
        )

    @agent
    def sec_agent(self) -> Agent:
        return Agent(
            role="Kubernetes Security Expert",
            goal="Ensure security best practices and compliance.",
            backstory="You review Kubernetes YAML files, secrets, RBAC policies, and security configurations.",
            llm=LLM(model=self.common_model,
                    base_url="http://localhost:11434"),
            verbose=True,
            # tools=[]
        )

    @agent
    def dev_agent(self) -> Agent:
        return Agent(
            role="Kubernetes Developer",
            goal="Assist in application deployment within Kubernetes.",
            backstory="You generate Kubernetes YAML manifests for deployments, services, and configurations.",
            llm=LLM(model=self.common_model,
                    base_url="http://localhost:11434"),
            verbose=True,
            # tools=[KubectlTool(), YAMLValidatorTool()]
        )

    # --- Define Tasks ---
    @task
    def classify_task(self) -> Task:
        return Task(
            description="Classify the user's Kubernetes request and determine which agents should handle it.",
            agent=self.classifier_agent(),
            expected_output="A JSON array of relevant agents (e.g., ['DevAgent', 'SecAgent']).",
            human_input=True
        )

    @task
    def dev_task(self) -> Task:
        return Task(
            description="Generate Kubernetes YAML manifests for the user's request and validate them.",
            agent=self.dev_agent(),
            expected_output="A JSON object containing YAML files, validation results, and a summary."
        )

    @task
    def sec_task(self) -> Task:
        return Task(
            description="Review the generated YAML files for security best practices.",
            agent=self.sec_agent(),
            expected_output="A JSON object containing a security review and recommended fixes."
        )

    @task
    def ops_task(self) -> Task:
        return Task(
            description="Provide operational insights and debugging for the Kubernetes request.",
            agent=self.ops_agent(),
            expected_output="A JSON object containing operational recommendations."
        )

    @task
    def admin_task(self) -> Task:
        return Task(
            description="Manage cluster operations for the user's request.",
            agent=self.admin_agent(),
            expected_output="A JSON object containing cluster administration tasks."
        )

    # --- Define Crew ---
    @crew
    def crew(self) -> Crew:
        """Creates the Kubernetes crew."""
        return Crew(
            agents=[

                self.dev_agent(),
                self.sec_agent(),
                self.ops_agent(),
                self.admin_agent()
            ],
            tasks=[
                self.classify_task(),
                self.dev_task(),
                self.sec_task(),
                self.ops_task(),
                self.admin_task()
            ],
            # process=Process.sequential,  # Tasks are executed sequentially
            process=Process.hierarchical,
            manager_agent=self.classifier_agent(),
            memory=True,
            verbose=True
        )


# --- Main Execution ---
if __name__ == "__main__":
    # Initialize the crew
    print("Starting:")
    kubernetes_crew = KubernetesCrew().crew()

    # Run the crew with a user input
    user_input = "Deploy an Nginx app with 2 replicas and a service."
    result = kubernetes_crew.kickoff(inputs={"user_input": user_input})

    # Display the final output
    print("\n🚀 Final Output:")
    print(result)
