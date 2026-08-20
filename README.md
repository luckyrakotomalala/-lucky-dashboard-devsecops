# Projet DevSecOps — Dashboard nginx sécurisé sur Kubernetes (GitOps / ArgoCD)

## Architecture

```
GitHub (manifests/*.yaml)  --->  ArgoCD  --->  Kubernetes
```

1. Le code du site (`html/`) est packagé dans une image Docker nginx (`Dockerfile`).
2. Les manifests Kubernetes sont versionnés dans ce dépôt GitHub (dossier `manifests/`).
3. ArgoCD surveille ce dépôt (`Application` ArgoCD, cf. `05-argocd-application.yaml`)
   et synchronise automatiquement le cluster avec l'état déclaré dans Git.
4. Le Deployment tourne avec **4 pods (replicas)**, avec probes et limites de ressources.
5. Le Service expose les pods en interne (ClusterIP).
6. L'Ingress Controller (nginx-ingress) expose le Service vers l'extérieur et termine le TLS
   avec un certificat généré par **cert-manager** (auto-signé par défaut, adaptable en
   Let's Encrypt pour un vrai domaine).

## Fichiers

| Fichier | Rôle |
|---|---|
| `Dockerfile` | Image nginx qui sert le dashboard (`html/index.html`) |
| `html/index.html` | Le dashboard servi par nginx |
| `manifests/00-namespace.yaml` | Namespace `web` |
| `manifests/01-deployment.yaml` | Deployment nginx, 4 replicas, probes, resources |
| `manifests/02-service.yaml` | Service ClusterIP |
| `manifests/03-clusterissuer.yaml` | ClusterIssuer cert-manager (self-signed par défaut) |
| `manifests/04-ingress.yaml` | Ingress HTTPS |
| `manifests/05-argocd-application.yaml` | Application ArgoCD |

## Étapes

### 1. Builder et pousser l'image

```bash
docker build -t <votre-dockerhub-user>/lucky-dashboard:v1 .
docker push <votre-dockerhub-user>/lucky-dashboard:v1
```

Puis mettre à jour l'image dans `manifests/01-deployment.yaml` avec votre vrai identifiant.

### 2. Prérequis sur le cluster (une seule fois)

```bash
# Ingress Controller nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace

# cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 3. Déployer via GitOps

1. Poussez ce projet dans votre dépôt GitHub.
2. Dans `manifests/05-argocd-application.yaml`, remplacez `repoURL` par l'URL de votre dépôt.
3. Créez l'Application ArgoCD :
   ```bash
   kubectl apply -f manifests/05-argocd-application.yaml
   ```
4. ArgoCD déploie et maintient ensuite automatiquement tous les autres manifests.

### 4. Vérification

```bash
kubectl get pods -n web              # 4 pods Running
kubectl get svc -n web
kubectl get ingress -n web
kubectl get certificate -n web       # READY=True
kubectl get application -n argocd    # Synced / Healthy
```

Pour tester en local sans domaine public, ajoutez à `/etc/hosts` :
```
127.0.0.1 lucky-dashboard.local
```
