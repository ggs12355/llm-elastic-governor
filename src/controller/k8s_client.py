from __future__ import annotations


class KubernetesScaleClient:
    def __init__(self, namespace: str, deployment: str):
        self.namespace = namespace
        self.deployment = deployment
        self._apps_api = None

    def _client(self):
        if self._apps_api is not None:
            return self._apps_api
        from kubernetes import client, config

        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()
        self._apps_api = client.AppsV1Api()
        return self._apps_api

    def get_replicas(self) -> int:
        deployment = self._client().read_namespaced_deployment(self.deployment, self.namespace)
        return int(deployment.spec.replicas or 1)

    def patch_replicas(self, replicas: int) -> None:
        body = {"spec": {"replicas": int(replicas)}}
        self._client().patch_namespaced_deployment_scale(self.deployment, self.namespace, body)

