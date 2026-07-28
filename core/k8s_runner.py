"""
Neural Glass AI Orchestrator — Kubernetes Ephemeral Sandbox Engine
"""

import time
import asyncio
from typing import Tuple, Optional
from core.logger import log_event

try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class K8sSandboxRunner:
    """Manages ephemeral Kubernetes Jobs for isolated cloud execution."""

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.initialized = False
        if K8S_AVAILABLE:
            try:
                # Attempt to load in-cluster config or local kubeconfig (~/.kube/config)
                try:
                    config.load_incluster_config()
                except Exception:
                    config.load_kube_config()
                self.batch_v1 = client.BatchV1Api()
                self.core_v1 = client.CoreV1Api()
                self.initialized = True
                log_event("k8s_client_initialized", namespace=self.namespace)
            except Exception as e:
                log_event("k8s_config_failed", error=str(e), level="warning")

    async def run_ephemeral_job(
        self,
        command: str,
        image: str = "python:3.11-slim",
        timeout_seconds: int = 30
    ) -> Tuple[int, str, str]:
        """
        Spawns an ephemeral Kubernetes Job to run an isolated command and returns (exit_code, stdout, stderr).
        """
        if not K8S_AVAILABLE or not self.initialized:
            return 1, "", "Kubernetes client not initialized or kubeconfig unavailable."

        job_name = f"neural-glass-job-{int(time.time() * 1000)}"
        
        # Define Container Spec
        container = client.V1Container(
            name="sandbox-runner",
            image=image,
            command=["/bin/sh", "-c", command],
            working_dir="/workspace"
        )

        # Define Pod Spec
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": "neural-glass-sandbox"}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container])
        )

        # Define Job Spec
        job_spec = client.V1JobSpec(
            template=template,
            backoff_limit=0,
            active_deadline_seconds=timeout_seconds
        )

        # Create Job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name),
            spec=job_spec
        )

        try:
            # Dispatch Job to Cluster
            self.batch_v1.create_namespaced_job(namespace=self.namespace, body=job)
            log_event("k8s_job_created", job_name=job_name)

            # Wait for Pod Completion asynchronously
            start_t = time.time()
            while time.time() - start_t < timeout_seconds:
                await asyncio.sleep(1)
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=f"job-name={job_name}"
                )
                if pods.items:
                    pod = pods.items[0]
                    pod_phase = pod.status.phase
                    if pod_phase in ["Succeeded", "Failed"]:
                        logs = self.core_v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=self.namespace
                        )
                        exit_code = 0 if pod_phase == "Succeeded" else 1
                        
                        # Clean up Job
                        self.batch_v1.delete_namespaced_job(
                            name=job_name,
                            namespace=self.namespace,
                            body=client.V1DeleteOptions(propagation_policy="Background")
                        )
                        return exit_code, logs, ""

            return 124, "", f"Kubernetes job timed out after {timeout_seconds} seconds."

        except Exception as e:
            log_event("k8s_job_execution_failed", error=str(e), level="error")
            return 1, "", f"K8s Execution Error: {str(e)}"


k8s_runner = K8sSandboxRunner()