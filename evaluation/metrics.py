"""Metrics calculator for model evaluation."""
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter


class MetricsCalculator:
    """Calculate classification metrics for model evaluation."""

    @staticmethod
    def calculate_classification_metrics(
        predictions: List[str],
        ground_truth: List[str],
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate classification metrics including accuracy, precision, recall, F1, and confusion matrix.

        Args:
            predictions: List of predicted labels
            ground_truth: List of true labels
            labels: Optional list of all possible labels (for confusion matrix)

        Returns:
            Dictionary with metrics including:
            - accuracy: Overall accuracy
            - precision: Macro-averaged precision
            - recall: Macro-averaged recall
            - f1_score: Macro-averaged F1 score
            - confusion_matrix: Confusion matrix as 2D list
            - per_category_metrics: Per-category precision, recall, F1
            - total_examples: Total number of examples
        """
        if len(predictions) != len(ground_truth):
            raise ValueError(
                f"Length mismatch: {len(predictions)} predictions vs {len(ground_truth)} ground truth"
            )

        if len(predictions) == 0:
            raise ValueError("Cannot calculate metrics for empty predictions")

        # Get unique labels
        if labels is None:
            labels = sorted(list(set(predictions + ground_truth)))

        # Calculate accuracy
        correct = sum(p == g for p, g in zip(predictions, ground_truth))
        accuracy = correct / len(predictions)

        # Calculate confusion matrix
        confusion_matrix = MetricsCalculator._calculate_confusion_matrix(
            predictions, ground_truth, labels
        )

        # Calculate per-category metrics
        per_category = {}
        all_precision = []
        all_recall = []
        all_f1 = []

        for i, label in enumerate(labels):
            tp, fp, fn = MetricsCalculator._get_tp_fp_fn(
                confusion_matrix, i, len(labels)
            )

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            per_category[label] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "support": tp + fn,  # Total true instances of this class
            }

            all_precision.append(precision)
            all_recall.append(recall)
            all_f1.append(f1)

        # Calculate macro averages
        macro_precision = sum(all_precision) / len(all_precision)
        macro_recall = sum(all_recall) / len(all_recall)
        macro_f1 = sum(all_f1) / len(all_f1)

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(macro_precision, 4),
            "recall": round(macro_recall, 4),
            "f1_score": round(macro_f1, 4),
            "confusion_matrix": confusion_matrix,
            "per_category_metrics": per_category,
            "total_examples": len(predictions),
        }

    @staticmethod
    def _calculate_confusion_matrix(
        predictions: List[str], ground_truth: List[str], labels: List[str]
    ) -> List[List[int]]:
        """
        Calculate confusion matrix.

        Args:
            predictions: List of predicted labels
            ground_truth: List of true labels
            labels: List of all possible labels

        Returns:
            Confusion matrix as 2D list where matrix[i][j] is the count of
            true label i predicted as label j
        """
        n_labels = len(labels)
        label_to_idx = {label: i for i, label in enumerate(labels)}

        # Initialize matrix with zeros
        matrix = [[0 for _ in range(n_labels)] for _ in range(n_labels)]

        # Populate matrix
        for pred, true in zip(predictions, ground_truth):
            true_idx = label_to_idx.get(true, -1)
            pred_idx = label_to_idx.get(pred, -1)

            if true_idx >= 0 and pred_idx >= 0:
                matrix[true_idx][pred_idx] += 1

        return matrix

    @staticmethod
    def _get_tp_fp_fn(
        confusion_matrix: List[List[int]], class_idx: int, n_classes: int
    ) -> Tuple[int, int, int]:
        """
        Extract true positives, false positives, and false negatives for a class.

        Args:
            confusion_matrix: Confusion matrix
            class_idx: Index of the class
            n_classes: Total number of classes

        Returns:
            Tuple of (true_positives, false_positives, false_negatives)
        """
        # True positives: diagonal element
        tp = confusion_matrix[class_idx][class_idx]

        # False positives: sum of column excluding diagonal
        fp = sum(confusion_matrix[i][class_idx] for i in range(n_classes)) - tp

        # False negatives: sum of row excluding diagonal
        fn = sum(confusion_matrix[class_idx][j] for j in range(n_classes)) - tp

        return tp, fp, fn

    @staticmethod
    def calculate_category_distribution(
        examples: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate category distribution statistics.

        Args:
            examples: List of category labels

        Returns:
            Dictionary with category distribution stats
        """
        if not examples:
            return {}

        counter = Counter(examples)
        total = len(examples)

        distribution = {}
        for category, count in counter.items():
            distribution[category] = {
                "count": count,
                "percentage": round(count / total * 100, 2),
            }

        return distribution

    @staticmethod
    def identify_misclassification_patterns(
        predictions: List[str],
        ground_truth: List[str],
        inputs: Optional[List[str]] = None,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Identify common misclassification patterns.

        Args:
            predictions: List of predicted labels
            ground_truth: List of true labels
            inputs: Optional list of input examples
            top_n: Number of top patterns to return

        Returns:
            List of top misclassification patterns with counts
        """
        misclassifications = []

        for i, (pred, true) in enumerate(zip(predictions, ground_truth)):
            if pred != true:
                pattern = {
                    "true_label": true,
                    "predicted_label": pred,
                    "example_input": inputs[i] if inputs and i < len(inputs) else None,
                }
                misclassifications.append(pattern)

        # Count pattern frequencies (true -> predicted transitions)
        pattern_counts = Counter(
            (m["true_label"], m["predicted_label"]) for m in misclassifications
        )

        # Get top N patterns
        top_patterns = []
        for (true_label, pred_label), count in pattern_counts.most_common(top_n):
            top_patterns.append(
                {
                    "true_label": true_label,
                    "predicted_label": pred_label,
                    "count": count,
                    "percentage": round(count / len(ground_truth) * 100, 2),
                }
            )

        return top_patterns
