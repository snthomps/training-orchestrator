# 🎓 Training Job Examples & Learning Guide

This guide provides hands-on examples to help you learn how to use your Training Orchestrator API.

---

## 📋 Table of Contents

1. [Your Current Jobs](#your-current-jobs)
2. [Computer Vision Jobs](#computer-vision-jobs)
3. [Natural Language Processing Jobs](#nlp-jobs)
4. [ML Framework Training Jobs](#ml-framework-training-jobs)
5. [Learning Exercises](#learning-exercises)
6. [Job Management Examples](#job-management-examples)
7. [Troubleshooting Examples](#troubleshooting-examples)

---

## 🎯 Your Current Jobs

Based on your orchestrator setup, here are the jobs you're currently running:

### Job 1: ResNet50 Training

**What it does:**
- Trains a ResNet50 image classification model
- Runs daily at 2 AM
- Uses checkpoints for recovery
- Retries up to 3 times on failure

**View this job:**
```bash
# List all jobs to find the ResNet job
curl http://localhost:8000/jobs | grep -i resnet

# Get details (replace {job_id} with actual ID)
curl http://localhost:8000/jobs/{job_id}
```

**Create a similar job via API:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet50-imagenet-training",
    "image": "gcr.io/my-project/trainer:latest",
    "command": [
      "python", "train.py",
      "--model", "resnet50",
      "--dataset", "imagenet",
      "--epochs", "100",
      "--batch-size", "256",
      "--lr", "0.1"
    ],
    "schedule": "0 2 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/resnet50"
  }'
```

**What happens:**
- Orchestrator schedules it to run at 2 AM daily
- Trains ResNet50 on ImageNet
- Saves checkpoints every epoch
- If it fails, retries from last checkpoint
- Sends notifications to Slack/Email when complete

---

### Job 2: BERT Fine-tuning

**What it does:**
- Fine-tunes BERT for text classification
- Runs daily at 3 AM
- Uses transfer learning
- Retries up to 2 times on failure

**Create a BERT fine-tuning job:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bert-sentiment-analysis",
    "image": "gcr.io/my-project/nlp-trainer:latest",
    "command": [
      "python", "finetune.py",
      "--model", "bert-base-uncased",
      "--task", "sentiment",
      "--dataset", "imdb",
      "--epochs", "3",
      "--batch-size", "32"
    ],
    "schedule": "0 3 * * *",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/bert"
  }'
```

---

## 🖼️ Computer Vision Jobs

### Example 1: EfficientNet Training

**What it does:** Trains EfficientNet for image classification with data augmentation

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "efficientnet-b0-training",
    "image": "gcr.io/my-project/cv-trainer:latest",
    "command": [
      "python", "train_efficientnet.py",
      "--model", "efficientnet-b0",
      "--dataset", "cifar100",
      "--epochs", "50",
      "--augmentation", "autoaugment"
    ],
    "schedule": "0 4 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/efficientnet"
  }'
```

### Example 2: Object Detection (YOLO)

**What it does:** Trains YOLOv8 for object detection

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "yolo-object-detection",
    "image": "ultralytics/ultralytics:latest",
    "command": [
      "yolo", "detect", "train",
      "data=coco.yaml",
      "model=yolov8n.pt",
      "epochs=100",
      "imgsz=640"
    ],
    "schedule": "0 1 * * 0",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/yolo"
  }'
```

**Note:** `0 1 * * 0` means run at 1 AM every Sunday

### Example 3: Image Segmentation

**What it does:** Trains U-Net for medical image segmentation

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "unet-medical-segmentation",
    "image": "gcr.io/my-project/medical-ai:latest",
    "command": [
      "python", "train_unet.py",
      "--architecture", "unet",
      "--dataset", "medical-images",
      "--loss", "dice",
      "--epochs", "200"
    ],
    "schedule": "0 23 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/unet"
  }'
```

---

## 🗣️ Natural Language Processing Jobs

### Example 4: GPT-2 Fine-tuning

**What it does:** Fine-tunes GPT-2 for text generation

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gpt2-story-generation",
    "image": "gcr.io/my-project/llm-trainer:latest",
    "command": [
      "python", "finetune_gpt2.py",
      "--model", "gpt2-medium",
      "--dataset", "stories",
      "--epochs", "5",
      "--max-length", "1024"
    ],
    "schedule": "0 0 * * 1",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/gpt2"
  }'
```

**Note:** `0 0 * * 1` means run at midnight every Monday

### Example 5: Named Entity Recognition (NER)

**What it does:** Trains NER model for entity extraction

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ner-biomedical",
    "image": "gcr.io/my-project/nlp-trainer:latest",
    "command": [
      "python", "train_ner.py",
      "--model", "bert-base-cased",
      "--dataset", "biomedical-corpus",
      "--task", "ner",
      "--epochs", "10"
    ],
    "schedule": "0 5 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/ner"
  }'
```

### Example 6: Question Answering

**What it does:** Fine-tunes model for question answering

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "qa-squad-training",
    "image": "gcr.io/my-project/nlp-trainer:latest",
    "command": [
      "python", "train_qa.py",
      "--model", "distilbert-base-uncased",
      "--dataset", "squad",
      "--epochs", "3",
      "--max-seq-length", "384"
    ],
    "schedule": "0 6 * * *",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/qa"
  }'
```

---

## 🔧 ML Framework Training Jobs

### PyTorch Jobs

#### Example 7: PyTorch Image Classification

**What it does:** Trains a ResNet model using PyTorch with distributed training

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pytorch-resnet-training",
    "image": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
    "command": [
      "python", "train_pytorch.py",
      "--model", "resnet50",
      "--dataset", "imagenet",
      "--epochs", "90",
      "--batch-size", "256",
      "--lr", "0.1",
      "--optimizer", "sgd",
      "--momentum", "0.9",
      "--weight-decay", "1e-4"
    ],
    "schedule": "0 2 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/pytorch-resnet"
  }'
```

#### Example 8: PyTorch Distributed Training (Multi-GPU)

**What it does:** Trains a transformer model using PyTorch DDP (DistributedDataParallel)

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pytorch-ddp-transformer",
    "image": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
    "command": [
      "torchrun", 
      "--nproc_per_node=4",
      "--nnodes=1",
      "train_distributed.py",
      "--model", "transformer",
      "--dataset", "wikitext-103",
      "--epochs", "20",
      "--batch-size", "32",
      "--backend", "nccl"
    ],
    "schedule": "0 1 * * 0",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/pytorch-ddp"
  }'
```

**Note:** This uses 4 GPUs on a single node

#### Example 9: PyTorch Lightning Training

**What it does:** Trains using PyTorch Lightning for cleaner training loops

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pytorch-lightning-vae",
    "image": "pytorchlightning/pytorch_lightning:latest",
    "command": [
      "python", "train_lightning.py",
      "--model", "vae",
      "--dataset", "celeba",
      "--max-epochs", "50",
      "--batch-size", "128",
      "--gpus", "2",
      "--precision", "16",
      "--strategy", "ddp"
    ],
    "schedule": "0 3 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/lightning-vae"
  }'
```

---

### TensorFlow Jobs

#### Example 10: TensorFlow Keras Model Training

**What it does:** Trains a CNN using TensorFlow/Keras

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tensorflow-cnn-training",
    "image": "tensorflow/tensorflow:2.14.0-gpu",
    "command": [
      "python", "train_tensorflow.py",
      "--model", "mobilenet_v2",
      "--dataset", "cifar10",
      "--epochs", "100",
      "--batch-size", "64",
      "--optimizer", "adam",
      "--learning-rate", "0.001",
      "--mixed-precision"
    ],
    "schedule": "0 4 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/tf-cnn"
  }'
```

#### Example 11: TensorFlow Distributed Training

**What it does:** Multi-GPU training with TensorFlow MirroredStrategy

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tensorflow-distributed-bert",
    "image": "tensorflow/tensorflow:2.14.0-gpu",
    "command": [
      "python", "train_distributed_tf.py",
      "--model", "bert-base",
      "--dataset", "glue/sst2",
      "--epochs", "5",
      "--batch-size", "32",
      "--strategy", "mirrored",
      "--num-gpus", "4"
    ],
    "schedule": "0 0 * * 1",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/tf-bert-distributed"
  }'
```

#### Example 12: TensorFlow Custom Training Loop

**What it does:** Advanced custom training with tf.GradientTape

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tensorflow-custom-gan",
    "image": "tensorflow/tensorflow:2.14.0-gpu",
    "command": [
      "python", "train_gan.py",
      "--generator", "unet",
      "--discriminator", "patchgan",
      "--dataset", "edges2shoes",
      "--epochs", "200",
      "--batch-size", "16",
      "--g-lr", "0.0002",
      "--d-lr", "0.0002",
      "--beta1", "0.5"
    ],
    "schedule": "0 23 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/tf-gan"
  }'
```

---

### JAX Jobs

#### Example 13: JAX Neural Network Training

**What it does:** Trains a neural network using JAX and Flax

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jax-flax-resnet",
    "image": "gcr.io/my-project/jax-trainer:latest",
    "command": [
      "python", "train_jax.py",
      "--model", "resnet50",
      "--dataset", "imagenet",
      "--epochs", "90",
      "--batch-size", "256",
      "--learning-rate", "0.1",
      "--warmup-epochs", "5"
    ],
    "schedule": "0 5 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/jax-resnet"
  }'
```

#### Example 14: JAX with pmap (Multi-Device Training)

**What it does:** Distributed training across multiple devices using JAX pmap

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jax-pmap-transformer",
    "image": "gcr.io/my-project/jax-trainer:latest",
    "command": [
      "python", "train_jax_pmap.py",
      "--model", "transformer",
      "--dataset", "wmt14-en-de",
      "--epochs", "30",
      "--batch-size", "64",
      "--devices", "8",
      "--optimizer", "adamw",
      "--lr-schedule", "cosine"
    ],
    "schedule": "0 2 * * 0",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/jax-transformer-pmap"
  }'
```

**Note:** JAX automatically parallelizes across 8 devices using pmap

#### Example 15: JAX Reinforcement Learning

**What it does:** Trains RL agent using JAX and Haiku

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jax-ppo-training",
    "image": "gcr.io/my-project/jax-rl:latest",
    "command": [
      "python", "train_ppo.py",
      "--env", "CartPole-v1",
      "--algorithm", "ppo",
      "--num-steps", "1000000",
      "--num-envs", "16",
      "--learning-rate", "3e-4",
      "--clip-eps", "0.2",
      "--entropy-coef", "0.01"
    ],
    "schedule": "0 6 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/jax-ppo"
  }'
```

---

### scikit-learn Jobs

#### Example 16: scikit-learn Classification Pipeline

**What it does:** Trains multiple classification models with cross-validation

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sklearn-classification-pipeline",
    "image": "python:3.11-slim",
    "command": [
      "python", "train_sklearn.py",
      "--task", "classification",
      "--dataset", "breast-cancer",
      "--models", "logistic,rf,xgboost,svm",
      "--cv-folds", "5",
      "--scale-features",
      "--feature-selection"
    ],
    "schedule": "0 7 * * *",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/sklearn-classification"
  }'
```

#### Example 17: scikit-learn Hyperparameter Tuning

**What it does:** Grid search for optimal hyperparameters

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sklearn-grid-search",
    "image": "python:3.11-slim",
    "command": [
      "python", "tune_sklearn.py",
      "--model", "random-forest",
      "--dataset", "boston-housing",
      "--search-type", "grid",
      "--param-grid", "n_estimators:50,100,200;max_depth:5,10,20",
      "--cv-folds", "10",
      "--scoring", "neg_mean_squared_error",
      "--n-jobs", "-1"
    ],
    "schedule": "0 8 * * 0",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/sklearn-gridsearch"
  }'
```

**Note:** Runs weekly on Sundays at 8 AM

#### Example 18: scikit-learn Clustering Pipeline

**What it does:** Trains and evaluates clustering models

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sklearn-clustering-analysis",
    "image": "python:3.11-slim",
    "command": [
      "python", "cluster_sklearn.py",
      "--dataset", "customer-segmentation",
      "--algorithms", "kmeans,dbscan,hierarchical",
      "--n-clusters", "5",
      "--metrics", "silhouette,calinski,davies-bouldin",
      "--pca-components", "2",
      "--save-plots"
    ],
    "schedule": "0 9 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/sklearn-clustering"
  }'
```

#### Example 19: scikit-learn Ensemble Models

**What it does:** Trains stacking and voting ensemble models

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sklearn-ensemble-models",
    "image": "python:3.11-slim",
    "command": [
      "python", "train_ensemble.py",
      "--base-models", "logistic,rf,xgboost,lightgbm",
      "--ensemble-type", "stacking",
      "--meta-learner", "logistic",
      "--dataset", "credit-default",
      "--cv-folds", "5",
      "--calibrate-probabilities"
    ],
    "schedule": "0 10 * * *",
    "max_retries": 2,
    "checkpoint_path": "/checkpoints/sklearn-ensemble"
  }'
```

#### Example 20: scikit-learn Time Series with AutoML

**What it does:** Automated feature engineering and model selection for time series

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sklearn-timeseries-automl",
    "image": "python:3.11-slim",
    "command": [
      "python", "train_timeseries.py",
      "--dataset", "stock-prices",
      "--target", "close_price",
      "--lag-features", "7,14,30",
      "--rolling-windows", "7,30,90",
      "--models", "lasso,ridge,rf,xgboost",
      "--auto-feature-engineering",
      "--test-size", "0.2"
    ],
    "schedule": "0 11 * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/sklearn-timeseries"
  }'
```

---

## 🎮 Learning Exercises

### Exercise 1: Create, Monitor, and Delete a Job

**Goal:** Learn the complete job lifecycle

**Step 1:** Create a test job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-test-job",
    "image": "python:3.11-slim",
    "command": ["python", "-c", "print(\"Hello from training!\")"],
    "schedule": "*/5 * * * *",
    "max_retries": 1,
    "checkpoint_path": "/checkpoints/test"
  }'
```

**Note:** `*/5 * * * *` means run every 5 minutes (good for testing!)

**Step 2:** Get the job ID from the response, then check its status
```bash
# Replace {job_id} with your actual job ID
curl http://localhost:8000/jobs/{job_id}
```

**Step 3:** Wait 5 minutes, then check if it ran
```bash
curl http://localhost:8000/jobs/{job_id}
# Look for "status": "running" or "completed"
```

**Step 4:** Delete the job
```bash
curl -X DELETE http://localhost:8000/jobs/{job_id}
```

**Step 5:** Verify it's gone
```bash
curl http://localhost:8000/jobs
# Your job should no longer appear in the list
```

---

### Exercise 2: Create Jobs with Different Schedules

**Goal:** Understand cron scheduling

```bash
# Run every hour
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hourly-job",
    "image": "python:3.11-slim",
    "command": ["echo", "Running hourly"],
    "schedule": "0 * * * *",
    "max_retries": 1
  }'

# Run every day at 9 AM
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "morning-job",
    "image": "python:3.11-slim",
    "command": ["echo", "Good morning!"],
    "schedule": "0 9 * * *",
    "max_retries": 1
  }'

# Run every Monday at 8 PM
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weekly-job",
    "image": "python:3.11-slim",
    "command": ["echo", "Weekly report"],
    "schedule": "0 20 * * 1",
    "max_retries": 1
  }'

# Run on the 1st of every month at midnight
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "monthly-job",
    "image": "python:3.11-slim",
    "command": ["echo", "Monthly summary"],
    "schedule": "0 0 1 * *",
    "max_retries": 1
  }'
```

**Cron Schedule Format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 or 7 = Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

---

### Exercise 3: Test Failure and Retry

**Goal:** See how automatic retry works

**Step 1:** Create a job that fails
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "failing-job-test",
    "image": "python:3.11-slim",
    "command": ["python", "-c", "raise Exception(\"Test failure\")"],
    "schedule": "*/2 * * * *",
    "max_retries": 3,
    "checkpoint_path": "/checkpoints/failing"
  }'
```

**Step 2:** Monitor retry behavior
```bash
# Check status every 2 minutes
watch -n 120 "curl -s http://localhost:8000/jobs | grep failing-job-test"
```

**Step 3:** Check retry count
```bash
curl http://localhost:8000/jobs/{job_id}
# Look at "retry_count" - it should increment with each failure
```

**Step 4:** Check notifications
- You should receive Slack/Email notifications about retries
- After 3 failed attempts, you'll get a final failure notification

**Step 5:** Clean up
```bash
curl -X DELETE http://localhost:8000/jobs/{job_id}
```

---

### Exercise 4: Update a Job's Schedule

**Goal:** Learn to modify existing jobs

**Step 1:** Create a job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "updateable-job",
    "image": "python:3.11-slim",
    "command": ["echo", "Hello"],
    "schedule": "0 10 * * *",
    "max_retries": 2
  }'
```

**Step 2:** Update the schedule to run at 2 PM instead
```bash
curl -X PUT http://localhost:8000/jobs/{job_id} \
  -H "Content-Type: application/json" \
  -d '{
    "schedule": "0 14 * * *"
  }'
```

**Step 3:** Update max retries
```bash
curl -X PUT http://localhost:8000/jobs/{job_id} \
  -H "Content-Type: application/json" \
  -d '{
    "max_retries": 5
  }'
```

**Step 4:** Verify changes
```bash
curl http://localhost:8000/jobs/{job_id}
```

---

## 📊 Job Management Examples

### View All Jobs

```bash
# All jobs
curl http://localhost:8000/jobs

# Pretty print (if you have jq installed)
curl http://localhost:8000/jobs | jq

# Filter by status
curl "http://localhost:8000/jobs?status_filter=completed"
curl "http://localhost:8000/jobs?status_filter=pending"
curl "http://localhost:8000/jobs?status_filter=failed"

# Pagination (show 10 jobs per page)
curl "http://localhost:8000/jobs?page=1&page_size=10"
curl "http://localhost:8000/jobs?page=2&page_size=10"
```

### Get System Statistics

```bash
# Overall stats
curl http://localhost:8000/stats

# Pretty print
curl http://localhost:8000/stats | jq
```

**Example Response:**
```json
{
  "total_jobs": 15,
  "pending": 5,
  "running": 2,
  "completed": 6,
  "failed": 1,
  "retrying": 1
}
```

### Check Orchestrator Status

```bash
# Orchestrator health
curl http://localhost:8080/health

# Jobs currently being scheduled
curl http://localhost:8080/status
```

### Retry a Failed Job

```bash
# Manually retry a failed job
curl -X POST http://localhost:8000/jobs/{job_id}/retry

# This resets the job to pending and clears errors
```

### Delete Multiple Jobs

```bash
# Get all pending jobs
curl http://localhost:8000/jobs?status_filter=pending | jq -r '.jobs[].job_id'

# Delete each one (replace IDs)
curl -X DELETE http://localhost:8000/jobs/train-abc123
curl -X DELETE http://localhost:8000/jobs/train-def456
```

---

## 🔧 Troubleshooting Examples

### Example 1: Job Not Starting

**Symptoms:** Job status stays "pending" forever

**Check:**
```bash
# 1. Verify orchestrator is running
curl http://localhost:8080/health

# 2. Check orchestrator logs
docker-compose logs orchestrator | grep -i "scheduling\|error"

# 3. Verify job is in database
curl http://localhost:8000/jobs/{job_id}

# 4. Wait 60 seconds (orchestrator checks every minute)
sleep 60
curl http://localhost:8080/status
```

### Example 2: Job Keeps Failing

**Symptoms:** Retry count keeps increasing

**Investigate:**
```bash
# 1. Get job details with error message
curl http://localhost:8000/jobs/{job_id} | jq '.error_message'

# 2. Check orchestrator logs for details
docker-compose logs orchestrator | grep {job_id}

# 3. Check if image exists and is accessible
docker pull {your_image_name}

# 4. Verify command syntax is correct
curl http://localhost:8000/jobs/{job_id} | jq '.command'
```

### Example 3: Can't Delete a Job

**Symptoms:** DELETE returns 409 Conflict

**Solution:**
```bash
# You can't delete running jobs
# Wait for it to finish, or check status:
curl http://localhost:8000/jobs/{job_id}

# If it's stuck in "running" state, restart orchestrator
docker-compose restart orchestrator

# Then try deleting again
curl -X DELETE http://localhost:8000/jobs/{job_id}
```

---

## 🎓 Advanced Learning Projects

### Project 1: Hyperparameter Sweep

Create multiple jobs with different hyperparameters:

```bash
# Learning rate sweep
for lr in 0.001 0.01 0.1; do
  curl -X POST http://localhost:8000/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"resnet-lr-${lr}\",
      \"image\": \"gcr.io/my-project/trainer:latest\",
      \"command\": [\"python\", \"train.py\", \"--lr\", \"${lr}\"],
      \"schedule\": \"0 2 * * *\",
      \"max_retries\": 2
    }"
done
```

### Project 2: A/B Testing Models

```bash
# Model A: ResNet50
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "model-a-resnet50",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py", "--model", "resnet50"],
    "schedule": "0 2 * * *",
    "max_retries": 3
  }'

# Model B: EfficientNet
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "model-b-efficientnet",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py", "--model", "efficientnet"],
    "schedule": "0 2 * * *",
    "max_retries": 3
  }'

# Compare results after both complete
curl http://localhost:8000/jobs | grep -E "model-a|model-b"
```

### Project 3: Multi-Stage Training Pipeline

```bash
# Stage 1: Data preprocessing (runs at 1 AM)
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stage-1-preprocessing",
    "image": "gcr.io/my-project/data-processor:latest",
    "command": ["python", "preprocess.py"],
    "schedule": "0 1 * * *",
    "max_retries": 2
  }'

# Stage 2: Model training (runs at 2 AM)
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stage-2-training",
    "image": "gcr.io/my-project/trainer:latest",
    "command": ["python", "train.py"],
    "schedule": "0 2 * * *",
    "max_retries": 3
  }'

# Stage 3: Model evaluation (runs at 6 AM)
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "stage-3-evaluation",
    "image": "gcr.io/my-project/evaluator:latest",
    "command": ["python", "evaluate.py"],
    "schedule": "0 6 * * *",
    "max_retries": 2
  }'
```

---

## 📚 Quick Reference

### Most Common Commands

```bash
# Create job
curl -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d '{...}'

# List all jobs
curl http://localhost:8000/jobs

# Get job details
curl http://localhost:8000/jobs/{job_id}

# Delete job
curl -X DELETE http://localhost:8000/jobs/{job_id}

# Get statistics
curl http://localhost:8000/stats

# Check health
curl http://localhost:8000/health
curl http://localhost:8080/health
```

### Job Status Values

- **pending**: Job created, waiting to be scheduled
- **running**: Job is currently executing
- **completed**: Job finished successfully
- **failed**: Job failed after all retries
- **retrying**: Job failed, will retry soon

---

## 🎯 Next Steps

1. **Try Exercise 1** - Create your first test job
2. **Explore `/docs`** - Open http://localhost:8000/docs in browser
3. **Create real jobs** - Adapt examples to your actual training needs
4. **Monitor notifications** - Check Slack/Email for job updates
5. **Scale up** - Create multiple jobs for different models

---

## 💡 Tips

- Use `*/5 * * * *` schedule for testing (runs every 5 minutes)
- Always set reasonable `max_retries` (2-3 is usually good)
- Use descriptive job names (e.g., `resnet50-imagenet-v2`)
- Check `/docs` page for interactive API exploration
- Monitor logs: `docker-compose logs -f orchestrator`

---

**Happy Training! 🚀**

For more help, see:
- [API_GUIDE.md](API_GUIDE.md) - Complete API reference
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Troubleshooting
- Interactive docs: http://localhost:8000/docs
