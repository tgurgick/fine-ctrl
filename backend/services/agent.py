"""Agent service for task analysis and data generation using Claude API."""
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import Task, TrainingExample
from backend.utils.validation import sanitize_input, validate_prompt

logger = logging.getLogger(__name__)


class AgentService:
    """Service for Claude-powered task analysis and data generation."""

    def __init__(self):
        """Initialize agent service with Claude client."""
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.AGENT_MODEL

    async def analyze_task(
        self,
        description: str,
        sample_data: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a task description and return configuration.

        Args:
            description: User's task description
            sample_data: Optional sample examples provided by user

        Returns:
            Task configuration including:
            - task_type: classification, extraction, generation, etc.
            - complexity: simple, medium, complex
            - recommended_metrics: list of evaluation metrics
            - data_requirements: min/recommended example counts
            - training_config: suggested hyperparameters

        Raises:
            ValueError: If prompt injection detected
            Exception: If API call fails
        """
        # Validate and sanitize input
        safe_description = sanitize_input(description)
        validate_prompt(safe_description)

        # Build analysis prompt
        prompt = self._build_analysis_prompt(safe_description, sample_data)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            content = response.content[0].text
            config = self._parse_analysis_response(content)

            logger.info(f"Task analyzed successfully: type={config.get('task_type')}")
            return config

        except Exception as e:
            logger.error(f"Task analysis failed: {str(e)}")
            # Return a default configuration on failure
            return self._get_default_config()

    async def generate_examples(
        self,
        db: Session,
        task: Task,
        count: int = 10,
        focus_areas: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Generate synthetic training examples for a task.

        Args:
            db: Database session
            task: Task to generate examples for
            count: Number of examples to generate
            focus_areas: Optional specific areas to focus on (e.g., edge cases)

        Returns:
            List of generated examples with input/output pairs

        Raises:
            ValueError: If task config invalid or prompt injection detected
        """
        # Validate task description
        validate_prompt(task.description)

        # Build generation prompt
        prompt = self._build_generation_prompt(task, count, focus_areas)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,  # Higher temperature for diversity
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            content = response.content[0].text
            examples = self._parse_generation_response(content)

            logger.info(f"Generated {len(examples)} examples for task {task.id}")
            return examples[:count]  # Ensure we return exact count requested

        except Exception as e:
            logger.error(f"Example generation failed: {str(e)}")
            raise

    def _build_analysis_prompt(
        self,
        description: str,
        sample_data: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for task analysis."""
        sample_section = ""
        if sample_data:
            sample_section = f"\n\nSample data provided:\n{json.dumps(sample_data[:5], indent=2)}"

        return f"""Analyze this fine-tuning task and provide configuration recommendations.

Task Description:
{description}{sample_section}

Determine:
1. **Task Type**: Choose ONE from [classification, extraction, generation_creative, generation_factual, transformation, conversation]
2. **Complexity**: simple (single-turn, clear rules), medium (requires context), or complex (multi-step reasoning)
3. **Structured Output**: Does the task require structured output (JSON, specific format)? [yes/no]
4. **Recommended Metrics**: Which metrics to use for evaluation
5. **Data Requirements**: Minimum and recommended number of training examples
6. **Training Config**: Suggested hyperparameters (epochs, learning rate multiplier)
7. **Success Criteria**: What indicates the model is performing well

Output your analysis as a JSON object with these exact keys:
{{
  "task_type": "classification",
  "complexity": "simple",
  "structured_output": false,
  "recommended_metrics": ["accuracy", "f1_score"],
  "data_requirements": {{
    "minimum": 50,
    "recommended": 200
  }},
  "training_config": {{
    "num_epochs": 3,
    "learning_rate_multiplier": 1.0
  }},
  "success_criteria": "Achieve >85% accuracy on test set",
  "reasoning": "Brief explanation of your analysis"
}}

Respond with ONLY the JSON object, no additional text."""

    def _build_generation_prompt(
        self,
        task: Task,
        count: int,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Build prompt for example generation."""
        focus_section = ""
        if focus_areas:
            focus_section = f"\n\nFocus specifically on these areas:\n" + "\n".join(f"- {area}" for area in focus_areas)

        return f"""Generate {count} diverse training examples for this fine-tuning task.

Task Name: {task.name}
Task Description: {task.description}
Task Type: {task.config.get('task_type', 'unknown')}
Task Config: {json.dumps(task.config, indent=2)}{focus_section}

Requirements:
- Generate exactly {count} examples
- Ensure diversity in complexity, style, and edge cases
- Each example should have "input" and "output" keys
- Make examples realistic and representative of real use cases
- Include some edge cases and challenging examples

Output as a JSON array:
[
  {{
    "input": "example input text",
    "output": "expected output text"
  }},
  ...
]

Respond with ONLY the JSON array, no additional text."""

    def _parse_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse Claude's analysis response."""
        try:
            # Try to extract JSON from the response
            # Claude sometimes adds text before/after the JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                config = json.loads(json_str)
                return config
            else:
                logger.warning("No JSON found in analysis response")
                return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return self._get_default_config()

    def _parse_generation_response(self, content: str) -> List[Dict[str, str]]:
        """Parse Claude's generation response."""
        try:
            # Try to extract JSON array from the response
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                examples = json.loads(json_str)
                # Validate structure
                if isinstance(examples, list) and all(
                    isinstance(ex, dict) and 'input' in ex and 'output' in ex
                    for ex in examples
                ):
                    return examples

            logger.error("Invalid JSON structure in generation response")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse generation response: {e}")
            return []

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration when analysis fails."""
        return {
            "task_type": "classification",
            "complexity": "medium",
            "structured_output": False,
            "recommended_metrics": ["accuracy"],
            "data_requirements": {
                "minimum": 50,
                "recommended": 200
            },
            "training_config": {
                "num_epochs": 3,
                "learning_rate_multiplier": 1.0
            },
            "success_criteria": "Achieve reasonable performance on test set",
            "reasoning": "Default configuration (analysis failed)"
        }


# Global service instance
agent_service = AgentService()
