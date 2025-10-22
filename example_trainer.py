#!/usr/bin/env python3
"""
Example training script with checkpoint support and failure recovery.
This demonstrates how to write training jobs compatible with the orchestrator.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingCheckpoint:
    """Handle checkpoint saving and loading"""
    
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"
    
    def save(self, state: dict):
        """Save training state to checkpoint"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Checkpoint saved: {self.checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def load(self) -> dict:
        """Load training state from checkpoint"""
        if not self.checkpoint_file.exists():
            logger.info("No checkpoint found, starting from scratch")
            return {}
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                state = json.load(f)
            logger.info(f"Checkpoint loaded from: {self.checkpoint_file}")
            return state
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return {}
    
    def exists(self) -> bool:
        """Check if checkpoint exists"""
        return self.checkpoint_file.exists()


class ModelTrainer:
    """Example model trainer with checkpoint support"""
    
    def __init__(self, args):
        self.args = args
        self.checkpoint = TrainingCheckpoint(args.checkpoint_dir)
        self.current_epoch = 0
        self.best_loss = float('inf')
        self.training_complete = False
        
        # Handle graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, saving checkpoint...")
        self._save_checkpoint()
        sys.exit(0)
    
    def _save_checkpoint(self):
        """Save current training state"""
        state = {
            'epoch': self.current_epoch,
            'best_loss': self.best_loss,
            'timestamp': datetime.now().isoformat(),
            'model_config': {
                'model_name': self.args.model,
                'learning_rate': self.args.learning_rate,
                'batch_size': self.args.batch_size
            }
        }
        self.checkpoint.save(state)
    
    def _load_checkpoint(self):
        """Load previous training state"""
        state = self.checkpoint.load()
        if state:
            self.current_epoch = state.get('epoch', 0)
            self.best_loss = state.get('best_loss', float('inf'))
            logger.info(f"Resuming from epoch {self.current_epoch}")
            logger.info(f"Best loss so far: {self.best_loss:.4f}")
    
    def train_epoch(self, epoch: int) -> float:
        """Simulate training for one epoch"""
        logger.info(f"Training epoch {epoch}/{self.args.epochs}")
        
        # Simulate training with progress
        num_batches = 100
        for batch in range(num_batches):
            time.sleep(0.01)  # Simulate computation
            
            if batch % 20 == 0:
                logger.info(f"  Batch {batch}/{num_batches}")
        
        # Simulate loss calculation (decreasing over epochs)
        loss = 1.0 / (epoch + 1) + (0.1 * (1 - (epoch / self.args.epochs)))
        logger.info(f"Epoch {epoch} - Loss: {loss:.4f}")
        
        # Simulate random failures for testing retry logic
        if self.args.simulate_failure and epoch == 2:
            raise RuntimeError("Simulated training failure at epoch 2")
        
        return loss
    
    def train(self):
        """Main training loop"""
        logger.info("=" * 50)
        logger.info(f"Starting training: {self.args.model}")
        logger.info(f"Job ID: {os.getenv('JOB_ID', 'unknown')}")
        logger.info(f"Epochs: {self.args.epochs}")
        logger.info(f"Learning rate: {self.args.learning_rate}")
        logger.info(f"Batch size: {self.args.batch_size}")
        logger.info("=" * 50)
        
        # Load checkpoint if resuming
        if self.args.resume_from_checkpoint and self.checkpoint.exists():
            self._load_checkpoint()
        
        # Training loop
        start_time = time.time()
        
        try:
            for epoch in range(self.current_epoch, self.args.epochs):
                self.current_epoch = epoch
                
                # Train one epoch
                loss = self.train_epoch(epoch)
                
                # Update best loss
                if loss < self.best_loss:
                    self.best_loss = loss
                    logger.info(f"New best loss: {self.best_loss:.4f}")
                
                # Save checkpoint periodically
                if (epoch + 1) % self.args.checkpoint_frequency == 0:
                    self._save_checkpoint()
            
            self.training_complete = True
            training_time = time.time() - start_time
            
            logger.info("=" * 50)
            logger.info("Training completed successfully!")
            logger.info(f"Total time: {training_time:.2f} seconds")
            logger.info(f"Final loss: {loss:.4f}")
            logger.info(f"Best loss: {self.best_loss:.4f}")
            logger.info("=" * 50)
            
            # Save final checkpoint
            self._save_checkpoint()
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            self._save_checkpoint()  # Save before failing
            raise


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Example training script with checkpoint support'
    )
    
    # Model arguments
    parser.add_argument(
        '--model',
        type=str,
        default='resnet50',
        help='Model architecture to train'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=10,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Training batch size'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=0.001,
        help='Learning rate'
    )
    
    # Checkpoint arguments
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default=os.getenv('CHECKPOINT_DIR', '/checkpoints'),
        help='Directory to save checkpoints'
    )
    parser.add_argument(
        '--checkpoint-frequency',
        type=int,
        default=2,
        help='Save checkpoint every N epochs'
    )
    parser.add_argument(
        '--resume-from-checkpoint',
        action='store_true',
        help='Resume training from last checkpoint'
    )
    
    # Testing arguments
    parser.add_argument(
        '--simulate-failure',
        action='store_true',
        help='Simulate a training failure (for testing)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    try:
        trainer = ModelTrainer(args)
        trainer.train()
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()