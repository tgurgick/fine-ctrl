"""
Verification script for Modal deployment.

This script verifies that the training module can be deployed to Modal
and checks all dependencies.
"""
import sys
import os


def check_dependencies():
    """Check if all required dependencies are available."""
    print("Checking dependencies...")

    required = [
        "modal",
        "torch",
        "transformers",
        "peft",
        "trl",
        "bitsandbytes",
        "accelerate",
        "datasets",
        "boto3",
        "redis",
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True


def check_modal_auth():
    """Check if Modal is authenticated."""
    print("\nChecking Modal authentication...")

    try:
        import modal

        # Try to list apps (requires authentication)
        try:
            # This will fail if not authenticated
            modal.App.list()
            print("✓ Modal authenticated")
            return True
        except Exception as e:
            print(f"✗ Modal not authenticated: {e}")
            print("\nAuthenticate with:")
            print("  modal token set")
            return False
    except ImportError:
        print("✗ Modal not installed")
        return False


def check_environment_variables():
    """Check if required environment variables are set."""
    print("\nChecking environment variables...")

    required_vars = {
        "REDIS_URL": "redis://localhost:6379",
        "S3_ENDPOINT_URL": "http://localhost:9000",
        "AWS_ACCESS_KEY_ID": "minioadmin",
        "AWS_SECRET_ACCESS_KEY": "minioadmin",
    }

    missing = []
    for var, default in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✓ {var}={value}")
        else:
            print(f"⚠ {var} not set (will use default: {default})")
            missing.append(var)

    return len(missing) == 0


def verify_s3_path_validation():
    """Verify S3 path validation works correctly."""
    print("\nVerifying S3 path validation...")

    from uuid import uuid4
    from training.utils import S3Manager

    user_id = uuid4()
    dataset_id = uuid4()

    # Test valid path
    valid_path = f"finetune-models/{user_id}/datasets/{dataset_id}/train.jsonl"
    try:
        S3Manager.validate_s3_path(valid_path)
        print(f"✓ Valid path accepted: {valid_path}")
    except Exception as e:
        print(f"✗ Valid path rejected: {e}")
        return False

    # Test invalid path (directory traversal)
    invalid_path = f"finetune-models/{user_id}/datasets/{dataset_id}/../../../etc/passwd"
    try:
        S3Manager.validate_s3_path(invalid_path)
        print(f"✗ Invalid path accepted (security issue!): {invalid_path}")
        return False
    except ValueError:
        print(f"✓ Invalid path rejected (security working)")

    return True


def verify_config():
    """Verify training configuration."""
    print("\nVerifying training configuration...")

    from training.config import QLoRAConfig, ResourceLimits

    # Test default config
    config = QLoRAConfig()
    print(f"✓ Default config created")
    print(f"  - Model: {config.model_name}")
    print(f"  - LoRA rank: {config.lora_r}")
    print(f"  - Epochs: {config.num_train_epochs}")

    # Test to_dict/from_dict
    config_dict = config.to_dict()
    restored = QLoRAConfig.from_dict(config_dict)
    if restored.model_name == config.model_name:
        print(f"✓ Config serialization works")
    else:
        print(f"✗ Config serialization failed")
        return False

    # Test resource limits
    limits = ResourceLimits()
    print(f"✓ Resource limits:")
    print(f"  - Max time: {limits.max_training_time_seconds}s")
    print(f"  - Max examples: {limits.max_examples}")
    print(f"  - GPU: {limits.gpu_type}")

    return True


def check_modal_app_structure():
    """Check if Modal app is properly structured."""
    print("\nChecking Modal app structure...")

    try:
        # Import the training module
        import training.train as train_module

        # Check if app exists
        if hasattr(train_module, 'app'):
            print(f"✓ Modal app found: {train_module.app}")
        else:
            print("✗ Modal app not found")
            return False

        # Check if train_model function exists
        if hasattr(train_module, 'train_model'):
            print(f"✓ train_model function found")
        else:
            print("✗ train_model function not found")
            return False

        return True
    except Exception as e:
        print(f"✗ Error loading training module: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Modal Training Deployment Verification")
    print("=" * 60)

    checks = [
        ("Dependencies", check_dependencies),
        ("Modal Authentication", check_modal_auth),
        ("Environment Variables", check_environment_variables),
        ("S3 Path Validation", verify_s3_path_validation),
        ("Training Configuration", verify_config),
        ("Modal App Structure", check_modal_app_structure),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} failed with error: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✓ All checks passed! Ready to deploy to Modal.")
        print("\nNext steps:")
        print("  1. Deploy: modal deploy training/train.py")
        print("  2. Test: modal run training/train.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
