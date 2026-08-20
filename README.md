# Projet DevSecOps — Dashboard nginx sécurisé, connecté en direct au cluster (v2)

## Ce qui change par rapport à la v1

La v1 servait une page HTML statique (contenu décoratif, pas connecté au cluster).
Cette v2 remplace nginx par un petit backend **Python/Flask** qui :

1. Sert la même page (dossier `html/`)
2. Expose une API `/api/status` qui interroge en direct l'API Kubernetes pour lire :
   - le nombre de replicas prêts / désirés (Deployment)
   - la présence de l'Ingress
   - l'état du certificat SSL (cert-manager)
   - le statut de sync ArgoCD (Application)
3. La page rafraîchit ces données toutes les 5 secondes via JavaScript (`fetch`)

Pour que ça fonctionne, le pod a besoin de la permission de lire ces ressources : c'est
le rôle de `manifests/01-rbac.yaml` (ServiceAccount + Role + RoleBinding, en lecture seule).

## Fichiers

| Fichier | Rôle |
|---|---|
| `app.py` | Backend Flask : sert la page + l'API `/api/status` |
| `requirements.txt` | Dépendances Python (flask, requests) |
| `Dockerfile` | Image basée sur `python:3.12-alpine` |
| `html/index.html` | Dashboard avec JavaScript qui appelle `/api/status` |
| `manifests/00-namespace.yaml` | Namespace `web` |
| `manifests/01-rbac.yaml` | ServiceAccount + permissions lecture seule (namespace `web` ET `argocd`) |
| `manifests/02-deployment.yaml` | Deployment, 4 replicas, utilise le ServiceAccount |
| `manifests/03-clusterissuer.yaml` | ClusterIssuer cert-manager |
| `manifests/04-ingress.yaml` | Ingress HTTPS |
| `manifests/05-service.yaml` | Service ClusterIP |
| `manifests/06-argocd-application.yaml` | Application ArgoCD |

## Étapes (test local avec minikube, comme pour la v1)

```bash
# 1. Builder la nouvelle image (tag v2, différent de la v1)
docker build -t lucky-dashboard:v2 .

# 2. La charger dans minikube
minikube image load lucky-dashboard:v2

# 3. Appliquer les manifests (dans l'ordre, ou tout le dossier d'un coup)
kubectl apply -f manifests/00-namespace.yaml
kubectl apply -f manifests/01-rbac.yaml
kubectl apply -f manifests/02-deployment.yaml
kubectl apply -f manifests/03-clusterissuer.yaml
kubectl apply -f manifests/04-ingress.yaml
kubectl apply -f manifests/05-service.yaml
```

Puis rouvre `https://lucky-dashboard.local` : cette fois, le "X / Y Running" et les
statuts Ingress / Certificat / ArgoCD reflètent l'état réel du cluster.

## Le vérifier

Change le nombre de replicas et regarde le dashboard se mettre à jour tout seul en
quelques secondes, sans recharger la page :

```bash
kubectl scale deployment lucky-dashboard -n web --replicas=6
```

## Pour la suite en GitOps (comme la v1)

Une fois que ça fonctionne en local, pousse ce dossier sur ton dépôt GitHub (à la
place du contenu de la v1), et applique `manifests/06-argocd-application.yaml` avec
la bonne URL de dépôt — ArgoCD prendra le relais comme avant.
