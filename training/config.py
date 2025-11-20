"""Training configuration."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class QLoRAConfig:
    """QLoRA training configuration."""

    # Model
    model_name: str = "mistralai/Mistral-7B-v0.1"
    max_seq_length: int = 2048

    # QLoRA parameters
    lora_r: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    lora_target_modules: list[str] = None

    # Quantization
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "bfloat16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # Training arguments
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-4
    max_grad_norm: float = 0.3
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    optim: str = "paged_adamw_32bit"

    # Logging
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100

    # Output
    output_dir: str = "/tmp/training_output"

    def __post_init__(self):
        """Set default LoRA target modules if not provided."""
        if self.lora_target_modules is None:
            self.lora_target_modules = [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ]

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "model_name": self.model_name,
            "max_seq_length": self.max_seq_length,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "lora_target_modules": self.lora_target_modules,
            "load_in_4bit": self.load_in_4bit,
            "bnb_4bit_compute_dtype": self.bnb_4bit_compute_dtype,
            "bnb_4bit_quant_type": self.bnb_4bit_quant_type,
            "bnb_4bit_use_double_quant": self.bnb_4bit_use_double_quant,
            "num_train_epochs": self.num_train_epochs,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "max_grad_norm": self.max_grad_norm,
            "warmup_ratio": self.warmup_ratio,
            "lr_scheduler_type": self.lr_scheduler_type,
            "optim": self.optim,
            "logging_steps": self.logging_steps,
            "save_steps": self.save_steps,
            "eval_steps": self.eval_steps,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QLoRAConfig":
        """Create config from dictionary."""
        return cls(**data)


@dataclass
class ResourceLimits:
    """Resource limits for training jobs."""

    max_training_time_seconds: int = 3600  # 1 hour
    max_dataset_size_mb: int = 500  # 500 MB
    max_examples: int = 10000
    gpu_type: str = "A10G"  # Default GPU for Modal
