"""Sample selection logic for evaluation and feedback."""
from typing import List, Dict, Any, Optional
import random
from collections import defaultdict


class SampleSelector:
    """Select diverse samples for evaluation and user feedback."""

    @staticmethod
    def select_diverse_samples(
        examples: List[Dict[str, Any]],
        count: int = 10,
        strategy: str = "diverse",
    ) -> List[Dict[str, Any]]:
        """
        Select diverse samples from evaluation results.

        Args:
            examples: List of evaluation examples with input, output, ground_truth, etc.
            count: Number of samples to select
            strategy: Selection strategy - "diverse", "uncertain", "balanced"

        Returns:
            List of selected samples
        """
        if not examples:
            return []

        if len(examples) <= count:
            return examples

        if strategy == "diverse":
            return SampleSelector._select_diverse(examples, count)
        elif strategy == "uncertain":
            return SampleSelector._select_uncertain(examples, count)
        elif strategy == "balanced":
            return SampleSelector._select_balanced(examples, count)
        else:
            # Default to random selection
            return random.sample(examples, count)

    @staticmethod
    def _select_diverse(examples: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """
        Select diverse samples covering different categories and outcomes.

        Prioritizes:
        1. Different categories/labels
        2. Mix of correct and incorrect predictions
        3. Edge cases (low confidence, misclassifications)
        """
        selected = []
        remaining = examples.copy()

        # Group by category (if available)
        by_category = defaultdict(list)
        for ex in examples:
            category = ex.get("category") or ex.get("ground_truth") or "unknown"
            by_category[category].append(ex)

        # Select at least one from each category
        categories = list(by_category.keys())
        random.shuffle(categories)

        for category in categories:
            if len(selected) >= count:
                break
            if by_category[category]:
                sample = by_category[category].pop(0)
                selected.append(sample)
                if sample in remaining:
                    remaining.remove(sample)

        # Fill remaining slots with mix of correct and incorrect predictions
        if len(selected) < count:
            # Separate correct and incorrect
            correct = [ex for ex in remaining if ex.get("is_correct", True)]
            incorrect = [ex for ex in remaining if not ex.get("is_correct", True)]

            # Interleave correct and incorrect
            while len(selected) < count and (correct or incorrect):
                if incorrect and len(selected) < count:
                    selected.append(incorrect.pop(0))
                if correct and len(selected) < count:
                    selected.append(correct.pop(0))

        # Fill any remaining slots
        if len(selected) < count and remaining:
            needed = count - len(selected)
            selected.extend(remaining[:needed])

        return selected[:count]

    @staticmethod
    def _select_uncertain(examples: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """
        Select samples with highest uncertainty (low confidence or near decision boundary).

        Useful for active learning and identifying difficult examples.
        """
        # Sort by confidence (ascending) - lowest confidence first
        with_confidence = [ex for ex in examples if "confidence" in ex]
        without_confidence = [ex for ex in examples if "confidence" not in ex]

        # Sort by confidence
        sorted_examples = sorted(with_confidence, key=lambda x: x.get("confidence", 1.0))

        # Take low-confidence examples first, then random from remaining
        selected = sorted_examples[:count]

        if len(selected) < count:
            needed = count - len(selected)
            selected.extend(random.sample(without_confidence, min(needed, len(without_confidence))))

        return selected[:count]

    @staticmethod
    def _select_balanced(examples: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """
        Select balanced samples across all categories.

        Ensures equal representation of each category in the selected samples.
        """
        # Group by category
        by_category = defaultdict(list)
        for ex in examples:
            category = ex.get("category") or ex.get("ground_truth") or ex.get("predicted_label") or "unknown"
            by_category[category].append(ex)

        if not by_category:
            return random.sample(examples, min(count, len(examples)))

        # Calculate samples per category
        n_categories = len(by_category)
        samples_per_category = max(1, count // n_categories)
        remainder = count % n_categories

        selected = []
        categories = list(by_category.keys())
        random.shuffle(categories)

        # Select from each category
        for i, category in enumerate(categories):
            # Add one extra for first 'remainder' categories
            n_samples = samples_per_category + (1 if i < remainder else 0)

            category_examples = by_category[category]
            random.shuffle(category_examples)

            selected.extend(category_examples[:n_samples])

            if len(selected) >= count:
                break

        return selected[:count]

    @staticmethod
    def select_misclassified_samples(
        examples: List[Dict[str, Any]],
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Select only misclassified examples.

        Useful for error analysis and understanding model weaknesses.

        Args:
            examples: List of evaluation examples
            count: Number of samples to select

        Returns:
            List of misclassified samples
        """
        misclassified = [ex for ex in examples if not ex.get("is_correct", True)]

        if len(misclassified) <= count:
            return misclassified

        # Prioritize diverse misclassifications
        return SampleSelector._select_diverse(misclassified, count)

    @staticmethod
    def select_edge_cases(
        examples: List[Dict[str, Any]],
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Select edge cases (unusual, low-confidence, or boundary examples).

        Args:
            examples: List of evaluation examples
            count: Number of samples to select

        Returns:
            List of edge case samples
        """
        # Define edge case criteria
        edge_cases = []

        for ex in examples:
            confidence = ex.get("confidence", 1.0)
            is_correct = ex.get("is_correct", True)

            # Consider as edge case if:
            # - Low confidence (< 0.6)
            # - Incorrect prediction
            # - Marked as edge case
            is_edge_case = (
                confidence < 0.6
                or not is_correct
                or ex.get("is_edge_case", False)
            )

            if is_edge_case:
                edge_cases.append(ex)

        if len(edge_cases) <= count:
            return edge_cases

        # Sort by confidence (ascending) and take lowest
        sorted_edge_cases = sorted(edge_cases, key=lambda x: x.get("confidence", 1.0))
        return sorted_edge_cases[:count]
