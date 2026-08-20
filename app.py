from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder="static", static_url_path="")

K8S_API = "https://kubernetes.default.svc"
TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
NAMESPACE = "web"
DEPLOYMENT_NAME = "lucky-dashboard"
INGRESS_NAME = "lucky-dashboard-ingress"
CERTIFICATE_NAME = "lucky-dashboard-tls"
ARGOCD_APP_NAME = "lucky-dashboard"


def k8s_get(path):
    """Appelle l'API Kubernetes avec le token du ServiceAccount monté dans le pod."""
    try:
        with open(TOKEN_PATH) as f:
            token = f.read().strip()
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{K8S_API}{path}", headers=headers, verify=CA_PATH, timeout=3)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


@app.route("/api/status")
def status():
    result = {
        "replicas": {"ready": 0, "desired": 0},
        "ingress": {"active": False},
        "certificate": {"ready": False},
        "argocd": {"sync": "Unknown", "health": "Unknown"},
    }

    dep = k8s_get(f"/apis/apps/v1/namespaces/{NAMESPACE}/deployments/{DEPLOYMENT_NAME}")
    if dep:
        result["replicas"]["ready"] = dep.get("status", {}).get("readyReplicas") or 0
        result["replicas"]["desired"] = dep.get("spec", {}).get("replicas") or 0

    ing = k8s_get(f"/apis/networking.k8s.io/v1/namespaces/{NAMESPACE}/ingresses/{INGRESS_NAME}")
    if ing:
        result["ingress"]["active"] = True

    cert = k8s_get(f"/apis/cert-manager.io/v1/namespaces/{NAMESPACE}/certificates/{CERTIFICATE_NAME}")
    if cert:
        conditions = cert.get("status", {}).get("conditions", [])
        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), None)
        result["certificate"]["ready"] = bool(ready_cond and ready_cond.get("status") == "True")

    app_cr = k8s_get(f"/apis/argoproj.io/v1alpha1/namespaces/argocd/applications/{ARGOCD_APP_NAME}")
    if app_cr:
        result["argocd"]["sync"] = app_cr.get("status", {}).get("sync", {}).get("status", "Unknown")
        result["argocd"]["health"] = app_cr.get("status", {}).get("health", {}).get("status", "Unknown")

    return jsonify(result)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
