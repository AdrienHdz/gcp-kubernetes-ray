# Kubernetes, Ray, and GCP Setup Guide

In this repository, we're delving into the application of cutting-edge technologies like Kubernetes, GCP, and Ray for effective distributed computing. These tools are instrumental in enhancing AI capabilities, enabling large-scale training of machine learning models, thereby resulting in improved predictions and faster data processing. They help tackle computational challenges, facilitate AI experimentation, speed up the deployment of solutions, and provide a competitive advantage.

## Prerequisites
Ensure you have the following tools and dependencies installed:
- Google Cloud SDK
- kubectl
- heml

## 1: Set up a Kubernetes cluster on GCP
First, let's create a node pool for a CPU-only head with the command:
```sh
gcloud container clusters create my-gke-cluster --num-nodes=1 --min-nodes 0 --max-nodes 1 --enable-autoscaling --zone=northamerica-northeast1-c --machine-type e2-standard-8 --workload-pool=kubernetes-ai.svc.id.goog
```

Next, create a node pool for GPU. The node is for a GPU Ray worker with 2 GPUs:
```sh
gcloud container node-pools create gpu-node-pool --accelerator type=nvidia-tesla-t4,count=4 --zone=northamerica-northeast1-c --cluster my-gke-cluster --num-nodes 1 --min-nodes 0 --max-nodes 1 --enable-autoscaling --machine-type n1-standard-8 --workload-metadata=GKE_METADATA
```
Note: GCP may inform you that the cluster cannot be created because you reached your quotas. If this occures, consider increasing your quote but be mindful of the costs.

## 2: Install NVIDIA GPU device driver
To install the NVIDIA GPU device driver, apply the yaml configuration from the URL below:
```sh
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

## 3: Deploy a ray cluster on Kubernetes with KubeRay operator
Ensure you're connected to your kubernetes cluster.

First, install both CRDs and KubeRay operator v0.5.0:
```sh
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm install kuberay-operator kuberay/kuberay-operator --version 0.5.0
```

Next, create a Ray cluster:
```sh
kubectl apply -f ray-cluster.gpu.yaml
```
Make sure to modify the YAMl file (ray-cluster.gpu.yaml) based on your needs.

You can then user post forwarding to map port 8625 of the ray-had pod to 127.0.0.1:8625
```sh
kubectl port-forward --address 0.0.0.0 services/raycluster-head-svc 8265:8265
```

## 4: Train the ML models 

Submit the training job to your ray cluster:
```sh
python3 pytorch_training_e2e_submit.py
```

## 5: Access the pods to get the model's results
To view the results of the model, we first list all pods:
```sh
kubectl get pods
```

You can then access a pod using the following command:
```sh
kubectl exec -ti pod-id -- bash
```
Inside the pod, you can list files, among other actions.

If your the docker image doesn't come with GCP sdk installed, you can installed it by running the following command:
```sh
RUN apt-get update -qq && apt-get install -y curl gnupg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update -qq && apt-get install -y google-cloud-sdk
```

If you correctly followed the Workload Identity setup instructions written above, you should be able to reach your google cloud storage bucket from your kubernetes pod, and therefore, should have the necessary permissions to perform this action:
```sh
gsutil cp <your-model-results-file> gs://<your-bucket>
```

## 6: Clean-up
When done, the Ray cluster and KubeRay can be removed with these commands:
```sh
kubectl delete raycluster raycluster
helm uninstall kuberay-operator
```

## Advanced Configuration: Workload Identity Setup
Workload Identity is the clean way of securely connecting to other Google Cloud services from within Kubernetes pods.
This is done by binding a Google Cloud service account to a Kubernetes service account, with creates a secure authentication process without the need for keys. 
## 1: Create a Kubernetes service account
```sh
kubectl create serviceaccount gke-training
```
This command creates a Kubernetes service account named "gke-training" in the current namespace. Service accounts provide an identity for processes that run in a pod.

## 2: Create a Google Cloud service account
```sh
gcloud iam service-accounts create gke-training-wli --project=kubernetes-ai
```
This command creates a Google Cloud service account named "gke-training-wli" within a Google Cloud project named "kubernetes-ai". Google cloud accounts are used by applications to authenticate to other Google Cloud services.

## 3: Assign roles to the service account
```sh
gcloud storage buckets add-iam-policy-binding gs://gke-model-results --member "serviceAccount:gke-training-wli@kubernetes-ai.iam.gserviceaccount.com" --role "roles/storage.admin"
```
Here, we assign the "storage.admin" role to the Google Cloud service account for the "gke-model-results" bucket. This role has permissions that allow it to perform administrative actions on the specified bucket.

## 4: Allows Kubernetes service account to impersonate GCP service account
```sh
gcloud iam service-accounts add-iam-policy-binding gke-training-wli[@kubernetes-ai.iam.gserviceaccount.com](mailto:web-wli@magic-cropping-tool.iam.gserviceaccount.com) --role roles/iam.workloadIdentityUser --member "serviceAccount:kubernetes-ai.svc.id.goog[default/gke-training]"
```
This commands allows the Kubernetes service account "gke-training" to impersonate the Google Cloud service account "gke-training-wli". The "iam.workloadIdentityUser" rose is added to the Google Cloud service account, which allows the service account to be impersonated by the specified member.

## 5: Annotate the service account to Kubernetes
```sh
kubectl annotate serviceaccount gke-training [iam.gke.io/gcp-service-account=gke-training-wli@kubernetes-ai.iam.gserviceaccount.com](http://iam.gke.io/gcp-service-account=web-wli@magic-cropping-tool.iam.gserviceaccount.com)
```
Now, we can apply an annotation to the Kubernetes service account that links to the Google Cloud service account. This allows the Kubernetes service account to authenticate as the Google Cloud service account when accessing Google Cloud services.

In the config file, we now need to add "serviceAccoutnName: gke-trianing" under the spec field. This ensures that pods created from this configuration will be associated with the "gke-training" service account, and thus have the ability to authenticate as the linked Google Cloud service account.

