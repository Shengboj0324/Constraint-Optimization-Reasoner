"""
Tests for config module.
"""

import pytest
from src.config import RLConfig, Config


def test_rl_config_default():
    """Test RLConfig with default values."""
    config = RLConfig()
    
    assert len(config.reward_weights) == 4
    assert config.reward_weights == [1.0, 2.0, 3.0, 0.5]
    assert config.per_device_train_batch_size == 4
    assert config.learning_rate == 1e-6


def test_rl_config_custom_weights():
    """Test RLConfig with custom reward weights."""
    config = RLConfig(reward_weights=[2.0, 3.0, 4.0, 1.0])
    
    assert config.reward_weights == [2.0, 3.0, 4.0, 1.0]


def test_rl_config_invalid_weights_count():
    """Test RLConfig validation with wrong number of weights."""
    with pytest.raises(ValueError, match="Expected 4 reward weights"):
        RLConfig(reward_weights=[1.0, 2.0])
    
    with pytest.raises(ValueError, match="Expected 4 reward weights"):
        RLConfig(reward_weights=[1.0, 2.0, 3.0, 0.5, 1.0])


def test_rl_config_invalid_weights_negative():
    """Test RLConfig validation with negative weights."""
    with pytest.raises(ValueError, match="non-negative"):
        RLConfig(reward_weights=[1.0, -1.0, 3.0, 0.5])
    
    with pytest.raises(ValueError, match="non-negative"):
        RLConfig(reward_weights=[-1.0, -2.0, -3.0, -0.5])


def test_rl_config_invalid_weights_all_zero():
    """Test RLConfig validation with all zero weights."""
    with pytest.raises(ValueError, match="At least one"):
        RLConfig(reward_weights=[0.0, 0.0, 0.0, 0.0])


def test_rl_config_invalid_weights_type():
    """Test RLConfig validation with non-numeric weights."""
    with pytest.raises(ValueError, match="must be numeric"):
        RLConfig(reward_weights=[1.0, "2.0", 3.0, 0.5])
    
    with pytest.raises(ValueError, match="must be numeric"):
        RLConfig(reward_weights=[1.0, None, 3.0, 0.5])


def test_rl_config_invalid_weights_not_list():
    """Test RLConfig validation with non-list weights."""
    with pytest.raises(ValueError, match="must be a list"):
        RLConfig(reward_weights=(1.0, 2.0, 3.0, 0.5))


def test_rl_config_invalid_batch_size():
    """Test RLConfig validation with invalid batch size."""
    with pytest.raises(ValueError, match="per_device_train_batch_size must be positive"):
        RLConfig(per_device_train_batch_size=0)
    
    with pytest.raises(ValueError, match="per_device_train_batch_size must be positive"):
        RLConfig(per_device_train_batch_size=-1)


def test_rl_config_invalid_gradient_accumulation():
    """Test RLConfig validation with invalid gradient accumulation."""
    with pytest.raises(ValueError, match="gradient_accumulation_steps must be positive"):
        RLConfig(gradient_accumulation_steps=0)
    
    with pytest.raises(ValueError, match="gradient_accumulation_steps must be positive"):
        RLConfig(gradient_accumulation_steps=-1)


def test_rl_config_invalid_learning_rate():
    """Test RLConfig validation with invalid learning rate."""
    with pytest.raises(ValueError, match="learning_rate must be positive"):
        RLConfig(learning_rate=0)
    
    with pytest.raises(ValueError, match="learning_rate must be positive"):
        RLConfig(learning_rate=-0.001)


def test_rl_config_invalid_kl_coeff():
    """Test RLConfig validation with invalid KL coefficient."""
    with pytest.raises(ValueError, match="kl_coeff must be non-negative"):
        RLConfig(kl_coeff=-0.1)


def test_rl_config_valid_edge_cases():
    """Test RLConfig with valid edge cases."""
    # Zero KL coefficient is valid
    config = RLConfig(kl_coeff=0.0)
    assert config.kl_coeff == 0.0
    
    # Single non-zero weight is valid
    config = RLConfig(reward_weights=[1.0, 0.0, 0.0, 0.0])
    assert config.reward_weights == [1.0, 0.0, 0.0, 0.0]
    
    # Very small learning rate is valid
    config = RLConfig(learning_rate=1e-10)
    assert config.learning_rate == 1e-10


def test_config_main_class():
    """Test main Config class."""
    config = Config()
    
    assert hasattr(config, 'data')
    assert hasattr(config, 'model')
    assert hasattr(config, 'training')
    assert hasattr(config, 'rl')
    assert hasattr(config, 'inference')
    assert hasattr(config, 'deployment')
    assert hasattr(config, 'verification')
    assert hasattr(config, 'logging')
    
    # Check that RL config is properly initialized
    assert len(config.rl.reward_weights) == 4


def test_config_from_env():
    """Test Config.from_env() method."""
    import os
    
    # Set environment variables
    os.environ['MODEL_PATH'] = '/test/model/path'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    config = Config.from_env()
    
    assert config.inference.model_path == '/test/model/path'
    assert config.deployment.model_path == '/test/model/path'
    assert config.logging.log_level == 'DEBUG'
    assert config.deployment.log_level == 'debug'
    
    # Clean up
    del os.environ['MODEL_PATH']
    del os.environ['LOG_LEVEL']

