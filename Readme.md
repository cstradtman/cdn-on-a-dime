# CDN on a Dime - Demo Project

This repository demonstrates a cost-effective CDN (Content Delivery Network) solution built using Kubernetes, Traefik, gstreamer, and whoami. An overlay network provided by ZeroTier is integrated into the system to securely route traffic between Traefik proxies, the upstream router, and your cloud environment.

## Table of Contents

- [CDN on a Dime - Demo Project](#cdn-on-a-dime---demo-project)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Architecture Overview](#architecture-overview)
  - [Repository Structure](#repository-structure)
  - [Deployment Overview](#deployment-overview)
  - [Dependencies \& Prerequisites](#dependencies--prerequisites)


## Project Overview

This demo project illustrates how to build a lightweight, cost-effective CDN by integrating multiple components:

- **gstreamer Service:** Streams video content; an init container waits for nginx to be available before launching the main container.
- **nginx Deployments & Services:** Serve as the web server and content aggregator, with a persistent volume for live data.
- **Traefik Dynamic Configuration:** A dedicated service (powered by `dynamic_config.py`) that reads Kubernetes ConfigMaps and dynamically configures Traefik proxies.
- **Traefik Proxies:** Handle routing and caching (using a plugin like `plugin-simplecache`).
- **whoami Service:** A simple demonstration service from [containous/whoami](https://hub.docker.com/r/containous/whoami) to show external exposure.
- **ExternalDNS & MetalLB:** Automate DNS records and allocate external IPs for services.
- **ZeroTier Overlay Network:** Each Traefik proxy is assigned a ZeroTier address. An upstream router, also running ZeroTier, routes both the load balancer and node traffic to these proxies in Vultr.

## Architecture Overview

The architecture (illustrated in the [Mermaid diagram](./docs/diagram.mermaid) and [diagram image](./docs/diagram.png)) consists of the following key elements:

- **gstreamer Deployment:**  
  - An **init container** (using BusyBox) waits for the nginx service (TCP probe on port 8080).
  - The **main gstreamer container** streams video data to nginx.

- **nginx Deployment & Service:**  
  - The nginx container (deployed via Kubernetes) aggregates the video stream and serves content.
  - A persistent volume (`live-storage`) is mounted.
  - The service has external DNS annotations and load-balancer settings (HTTP 8080 / RTSP 1935).

- **Traefik Dynamic Configuration:**  
  - A dynamic configuration service (`dynamic_config.py`) updates Traefik settings based on Kubernetes ConfigMaps.
  - Traefik proxies are deployed to route and optimize traffic, including caching via a simple cache plugin.

- **ZeroTier Integration:**  
  - Each Traefik proxy is assigned a unique ZeroTier address.
  - An upstream router (running ZeroTier) provides routes to both the load balancer and node address ranges.
  - This ensures that traffic from external clients is securely routed over the overlay network to the proxies hosted on Vultr.

- **whoami Service:**  
  - Deploys a simple container demonstrating web accessibility.
  - Exposed via ExternalDNS and MetalLB for external access.

## Repository Structure

.
├── ansible/                 # Ansible playbooks for automation and configuration
│   └── playbooks/
│       ├── configure_traefik_podman.yml
│       ├── configure_zerotier.yml
│       └── traefik.toml
├── docs/                    # Documentation and architectural diagrams
│   ├── diagram.mermaid
│   └── diagram.png
├── dynamic_config/          # Dynamic configuration service for Traefik
│   ├── Dockerfile
│   ├── dynamic_config.py
│   └── k8s/                 # Kubernetes manifests for traefik-config service
│       ├── rbac-traefik-config.yaml
│       ├── traefik-config-deployment.yaml
│       └── traefik-config-service.yaml
├── kubernetes/              # Shared Kubernetes manifests
│   └── configmaps_and_services/
│       ├── traefik-video-config-cm.yaml
│       └── traefik-whoami-config-cm.yaml
└── workloads/               # Workload definitions
    ├── gstreamer-service/   # Deployments for gstreamer and nginx with services
    │   ├── gstreamer-deployment.yml
    │   ├── nginx-deployment.yml
    │   └── service.yml
    └── whoami-service/      # Deployment and service for whoami
        ├── deployment.yml
        └── service.yml


## Deployment Overview

1. **Apply Shared Configurations:**  
   - Deploy ConfigMaps and ExternalName services from the `kubernetes/configmaps_and_services/` directory.

2. **Deploy Dynamic Config Service:**  
   - Build and deploy the `dynamic_config` service in Kubernetes via manifests in `dynamic_config/k8s/`.

3. **Deploy Workloads:**  
   - Deploy the gstreamer and nginx stacks from `workloads/gstreamer-service/`.
   - Deploy the whoami service from `workloads/whoami-service/`.

4. **Run Ansible Playbooks:**  
   - Use Ansible playbooks in `ansible/playbooks/` to configure the Podman-based Traefik deployment and set up ZeroTier on the relevant nodes.

5. **ZeroTier & DNS Setup:**  
   - Ensure each Traefik proxy is assigned a ZeroTier IP.
   - The upstream router must route both the load balancer and node address ranges to the proxies.
   - Confirm that ExternalDNS is correctly updating DNS with the right hostnames.

## Dependencies & Prerequisites

- **Kubernetes Cluster:** Local development (Minikube, k3s) or a managed cluster.
- **Container Runtime:** Podman or Docker for building images.
- **Ansible:** To run automation playbooks.
- **ExternalDNS & MetalLB:** Must be configured in your cluster.
- **ZeroTier:** Installed and configured on:
  - Each node (or container) requiring overlay-network access.
  - The upstream router to route both load balancer and node ranges.
- **Vultr DNS:** Used for external routing if deploying in a cloud environment.

