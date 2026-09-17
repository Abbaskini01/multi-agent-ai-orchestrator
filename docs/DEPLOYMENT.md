```markdown
# 🚀 Neural Glass — Deployment & Operations Guide (v1.0.0)

> Operational instructions for deploying Neural Glass in local, containerized Docker, and Kubernetes sandbox environments.

---

## 1. Environment Configuration

Neural Glass requires environment configuration via root `.env` or system environment variables:

```env
# Mandatory API Keys
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...

# Operational Mode
ENVIRONMENT=production
LOG_LEVEL=INFO

# Server Binding
HOST=127.0.0.1
PORT=8000


2. Deploying via Docker Sandbox
Build Docker Image
Bash
docker build -t neural-glass:1.0.0 .

Run Container
Bash
docker run -d \
  --name neural-glass-app \
  -p 8000:8000 \
  -e GROQ_API_KEY="your_groq_key" \
  -e GEMINI_API_KEY="your_gemini_key" \
  neural-glass:1.0.0

  3. Kubernetes Sandbox Execution (core/sandbox.py)
Neural Glass includes a dual-mode execution strategy for code sandboxing:

Primary Track: Attempts to launch an ephemeral K8s Pod inside the active cluster namespace using the kubernetes Python client.

Graceful Fallback: If a cluster context is unreachable or missing, the execution engine seamlessly degrades to an isolated local subprocess sandbox within workspace_sandbox/.

Deployment Manifest (k8s-deployment.yml)
YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neural-glass-orchestrator
  labels:
    app: neural-glass
spec:
  replicas: 1
  selector:
    matchLabels:
      app: neural-glass
  template:
    metadata:
      labels:
        app: neural-glass
    spec:
      containers:
      - name: neural-glass
        image: neural-glass:1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: neural-glass-secrets
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

4. Verification & Post-Deploy Smoke Check
After starting the application instance, execute a smoke test against the automated verification endpoint:
PowerShell
Invoke-RestMethod -Uri "[http://127.0.0.1:8000/api/cicd/deploy-verify](http://127.0.0.1:8000/api/cicd/deploy-verify)" -Method Post -Body '{"target_url": "[http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)"}' -ContentType "application/json"
Expected Response:
{
  "target_url": "[http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz)",
  "status_code": 200,
  "healthy": true,
  "action": "maintain",
  "notes": "Deployment healthy"
}