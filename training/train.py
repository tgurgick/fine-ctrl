"""
QLoRA training function for Modal.

This module implements fine-tuning using QLoRA (Quantized Low-Rank Adaptation)
on Modal's serverless GPU infrastructure.
"""
import os
import json
from typing import Dict, Any, Optional

import modal

from training.config import QLoRAConfig, ResourceLimits
from training.utils import (
    S3Manager,
    ProgressTracker,
    load_dataset_from_jsonl,
    format_examples_for_training,
)

# Create Modal app
app = modal.App("finetune-training")

# Create custom image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("training/requirements.txt")
    .env({"HF_HOME": "/cache/huggingface"})
)

# Secrets for S3 and Redis
secrets = [
    modal.Secret.from_name("aws-s3-credentials"),
    modal.Secret.from_name("redis-credentials"),
]


@app.function(
    image=image,
    gpu="A10G",
    timeout=3600,  # 1 hour max
    secrets=secrets,
    volumes={"/cache": modal.Volume.from_name("model-cache", create_if_missing=True)},
    memory=32768,  # 32 GB RAM
)
def train_model(
    job_id: str,
    dataset_s3_path: str,
    output_s3_path: str,
    config_dict: Dict[str, Any],
    redis_url: str,
) -> Dict[str, Any]:
    """
    Train a model using QLoRA on Modal.

    Args:
        job_id: Training job ID
        dataset_s3_path: S3 path to training dataset (JSONL format)
        output_s3_path: S3 path for model output
        config_dict: Training configuration dictionary
        redis_url: Redis URL for progress tracking

    Returns:
        Dictionary with training results and metrics

    Security:
        - S3 paths are validated to prevent directory traversal
        - Resource limits enforced
        - Progress tracking via Redis pub/sub
    """
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import Dataset

    # Initialize progress tracker
    progress = ProgressTracker(redis_url, job_id)
    progress.publish_progress("training", 0, message="Initializing training")

    try:
        # Parse config
        config = QLoRAConfig.from_dict(config_dict)
        limits = ResourceLimits()

        # Initialize S3 manager
        s3_manager = S3Manager(
            endpoint_url=os.getenv("S3_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        # Download dataset from S3
        progress.publish_progress("training", 5, message="Downloading dataset")
        local_dataset_path = "/tmp/dataset.jsonl"
        s3_manager.download_file(dataset_s3_path, local_dataset_path)

        # Load and validate dataset
        progress.publish_progress("training", 10, message="Loading dataset")
        raw_examples = load_dataset_from_jsonl(local_dataset_path)

        # Enforce resource limits
        if len(raw_examples) > limits.max_examples:
            raise ValueError(
                f"Dataset too large: {len(raw_examples)} examples "
                f"(max: {limits.max_examples})"
            )

        # Format examples for training
        formatted_examples = format_examples_for_training(raw_examples)
        dataset = Dataset.from_list(formatted_examples)

        # Load tokenizer
        progress.publish_progress("training", 15, message="Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(
            config.model_name,
            trust_remote_code=True,
            cache_dir="/cache/huggingface",
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        # Configure quantization
        progress.publish_progress("training", 20, message="Configuring quantization")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=config.load_in_4bit,
            bnb_4bit_quant_type=config.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
        )

        # Load model
        progress.publish_progress("training", 25, message="Loading base model")
        model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            cache_dir="/cache/huggingface",
        )

        # Prepare model for training
        progress.publish_progress("training", 30, message="Preparing model for training")
        model = prepare_model_for_kbit_training(model)

        # Configure LoRA
        peft_config = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=config.lora_target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )

        # Get PEFT model
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

        # Training arguments
        training_args = TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            optim=config.optim,
            save_steps=config.save_steps,
            logging_steps=config.logging_steps,
            learning_rate=config.learning_rate,
            max_grad_norm=config.max_grad_norm,
            warmup_ratio=config.warmup_ratio,
            lr_scheduler_type=config.lr_scheduler_type,
            fp16=False,
            bf16=True,
            group_by_length=True,
            report_to="none",  # Disable wandb/tensorboard
        )

        # Custom callback for progress tracking
        class ProgressCallback:
            def __init__(self, progress_tracker, total_steps):
                self.progress_tracker = progress_tracker
                self.total_steps = total_steps
                self.current_step = 0

            def on_log(self, args, state, control, logs=None, **kwargs):
                """Called on logging steps."""
                if logs:
                    self.current_step = state.global_step
                    progress_pct = 30 + (self.current_step / self.total_steps) * 60

                    metrics = {
                        "loss": logs.get("loss", 0),
                        "learning_rate": logs.get("learning_rate", 0),
                        "epoch": logs.get("epoch", 0),
                        "step": self.current_step,
                    }

                    self.progress_tracker.publish_progress(
                        "training",
                        progress_pct,
                        metrics=metrics,
                        message=f"Training step {self.current_step}/{self.total_steps}",
                    )

        # Calculate total training steps
        total_steps = (
            len(dataset)
            * config.num_train_epochs
            // (config.per_device_train_batch_size * config.gradient_accumulation_steps)
        )

        # Create trainer
        progress.publish_progress("training", 35, message="Starting training")
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            peft_config=peft_config,
            dataset_text_field="text",
            max_seq_length=config.max_seq_length,
            tokenizer=tokenizer,
            args=training_args,
            callbacks=[ProgressCallback(progress, total_steps)],
        )

        # Train
        trainer.train()

        # Save adapter
        progress.publish_progress("training", 90, message="Saving model")
        trainer.model.save_pretrained(config.output_dir)
        tokenizer.save_pretrained(config.output_dir)

        # Upload to S3
        progress.publish_progress("training", 95, message="Uploading model to S3")
        uploaded_files = s3_manager.upload_directory(config.output_dir, output_s3_path)

        # Get final metrics
        final_metrics = {
            "training_loss": trainer.state.log_history[-1].get("loss", 0),
            "total_steps": total_steps,
            "examples_trained": len(dataset),
            "uploaded_files": len(uploaded_files),
        }

        # Publish completion
        progress.publish_completion(final_metrics)

        return {
            "status": "completed",
            "metrics": final_metrics,
            "model_path": output_s3_path,
            "adapter_files": uploaded_files,
        }

    except Exception as e:
        # Log error
        error_msg = f"Training failed: {str(e)}"
        progress.publish_error(error_msg)

        return {
            "status": "failed",
            "error": error_msg,
        }


@app.local_entrypoint()
def main():
    """Test training function locally."""
    # Test configuration
    test_config = QLoRAConfig(
        num_train_epochs=1,
        per_device_train_batch_size=1,
    )

    result = train_model.remote(
        job_id="test-job-123",
        dataset_s3_path="finetune-models/test-user/datasets/test-dataset/train.jsonl",
        output_s3_path="finetune-models/test-user/adapters/test-adapter",
        config_dict=test_config.to_dict(),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    )

    print(f"Training result: {result}")
