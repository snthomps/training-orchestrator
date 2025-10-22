#!/bin/bash
# deploy.sh - Main deployment script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${K8S_NAMESPACE:-training}
IMAGE_TAG=${IMAGE_TAG:-latest}
REGISTRY=${REGISTRY:-gcr.io/my-project}

echo -e "${GREEN}Training Job Orchestrator Deployment${NC}"
echo "==========================================="

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    commands=("kubectl" "docker")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}Error: $cmd is not installed${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "\n${YELLOW}Building Docker image...${NC}"
    
    docker build -t ${REGISTRY}/training-orchestrator:${IMAGE_TAG} .
    
    echo -e "${GREEN}✓ Image built successfully${NC}"
}

# Function to push image
push_image() {
    echo -e "\n${YELLOW}Pushing image to registry...${NC}"
    
    docker push ${REGISTRY}/training-orchestrator:${IMAGE_TAG}
    
    echo -e "${GREEN}✓ Image pushed successfully${NC}"
}

# Function to create namespace
create_namespace() {
    echo -e "\n${YELLOW}Creating namespace...${NC}"
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        echo -e "${YELLOW}Namespace $NAMESPACE already exists${NC}"
    else
        kubectl create namespace $NAMESPACE
        echo -e "${GREEN}✓ Namespace created${NC}"
    fi
}

# Function to create secrets
create_secrets() {
    echo -e "\n${YELLOW}Setting up secrets...${NC}"
    
    if [ ! -f .env ]; then
        echo -e "${RED}Error: .env file not found${NC}"
        echo "Please create .env file with required variables"
        exit 1
    fi
    
    source .env
    
    kubectl create secret generic orchestrator-secrets \
        --from-literal=SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}" \
        --from-literal=SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}" \
        --from-literal=SMTP_PORT="${SMTP_PORT:-587}" \
        --from-literal=SENDER_EMAIL="${SENDER_EMAIL}" \
        --from-literal=SENDER_PASSWORD="${SENDER_PASSWORD}" \
        --from-literal=RECIPIENT_EMAILS="${RECIPIENT_EMAILS}" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✓ Secrets configured${NC}"
}

# Function to deploy Kubernetes resources
deploy_k8s() {
    echo -e "\n${YELLOW}Deploying Kubernetes resources...${NC}"
    
    # Update image tag in deployment
    sed -i.bak "s|image:.*training-orchestrator:.*|image: ${REGISTRY}/training-orchestrator:${IMAGE_TAG}|g" k8s/orchestrator-deployment.yaml
    
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/persistent-volume.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/service-account.yaml
    kubectl apply -f k8s/rbac.yaml
    kubectl apply -f k8s/orchestrator-deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    # Restore original file
    mv k8s/orchestrator-deployment.yaml.bak k8s/orchestrator-deployment.yaml
    
    echo -e "${GREEN}✓ Kubernetes resources deployed${NC}"
}

# Function to wait for deployment
wait_for_deployment() {
    echo -e "\n${YELLOW}Waiting for deployment to be ready...${NC}"
    
    kubectl wait --for=condition=available --timeout=300s \
        deployment/training-orchestrator -n $NAMESPACE
    
    echo -e "${GREEN}✓ Deployment is ready${NC}"
}

# Function to show deployment status
show_status() {
    echo -e "\n${YELLOW}Deployment Status:${NC}"
    echo "===================="
    
    kubectl get pods -n $NAMESPACE
    echo ""
    kubectl get svc -n $NAMESPACE
    
    echo -e "\n${GREEN}Access the API:${NC}"
    echo "kubectl port-forward -n $NAMESPACE svc/training-orchestrator 8080:8080"
}

# Function to run tests
run_tests() {
    echo -e "\n${YELLOW}Running tests...${NC}"
    
    pytest tests/ -v --cov=orchestrator
    
    echo -e "${GREEN}✓ Tests passed${NC}"
}

# Function to delete deployment
delete_deployment() {
    echo -e "\n${YELLOW}Deleting deployment...${NC}"
    
    kubectl delete -f k8s/ --ignore-not-found=true
    
    echo -e "${GREEN}✓ Deployment deleted${NC}"
}

# Function to show logs
show_logs() {
    echo -e "\n${YELLOW}Showing logs...${NC}"
    
    kubectl logs -n $NAMESPACE -l app=training-orchestrator --tail=100 -f
}

# Main deployment flow
main() {
    case "${1:-all}" in
        build)
            check_prerequisites
            build_image
            ;;
        push)
            push_image
            ;;
        deploy)
            check_prerequisites
            create_namespace
            create_secrets
            deploy_k8s
            wait_for_deployment
            show_status
            ;;
        test)
            run_tests
            ;;
        delete)
            delete_deployment
            ;;
        logs)
            show_logs
            ;;
        all)
            check_prerequisites
            run_tests
            build_image
            push_image
            create_namespace
            create_secrets
            deploy_k8s
            wait_for_deployment
            show_status
            ;;
        *)
            echo "Usage: $0 {build|push|deploy|test|delete|logs|all}"
            echo ""
            echo "Commands:"
            echo "  build   - Build Docker image"
            echo "  push    - Push image to registry"
            echo "  deploy  - Deploy to Kubernetes"
            echo "  test    - Run tests"
            echo "  delete  - Delete deployment"
            echo "  logs    - Show logs"
            echo "  all     - Run everything (test, build, push, deploy)"
            exit 1
            ;;
    esac
}

main "$@"
