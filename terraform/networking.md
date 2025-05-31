# GCP Networking Configuration Details (terraform/networking.tf)

This document provides details on the Google Cloud Platform (GCP) Virtual Private Cloud (VPC) network configuration defined in `terraform/networking.tf` for Project Noah MVP V1.0.

## 1. Overview

The networking setup for Project Noah MVP establishes a secure and private communication environment for its cloud resources. It utilizes a custom VPC network, a dedicated subnet with Private Google Access, a Cloud NAT gateway for controlled internet egress, and minimal firewall rules tailored for a serverless architecture (primarily Cloud Run).

## 2. Network Topology Components

### 2.1. Custom VPC Network (`google_compute_network.noah_mvp_vpc`)

*   **Name:** `vpc-noah-mvp`
*   **Mode:** Custom (<code>auto_create_subnetworks = false</code>). This provides greater control over network topology compared to the default auto-mode VPC.
*   **Routing Mode:** Regional. Appropriate for setups using regional resources like Cloud NAT.
*   **MTU:** Standard 1460.
*   **Purpose:** Serves as the primary isolated network for all Project Noah MVP resources.

### 2.2. Primary Subnetwork (`google_compute_subnetwork.noah_mvp_subnet_primary`)

*   **Name:** `subnet-noah-mvp-primary-${var.gcp_region}` (e.g., `subnet-noah-mvp-primary-us-central1`)
*   **Region:** Dynamically set by the `var.gcp_region` variable (default `us-central1`).
*   **IP CIDR Range:** `10.10.10.0/24` (example). This range provides up to 254 usable IP addresses for resources within the subnet, such as Serverless VPC Access connectors.
*   **Private Google Access (PGA):** Enabled (`private_ip_google_access = true`).
    *   **Purpose:** Allows resources within this subnet (e.g., Cloud Run services connected via a Serverless VPC Access connector) to reach Google APIs and services (like Vertex AI, Firestore, Cloud Storage, Speech-to-Text) using Google's private network, without requiring public IP addresses or traversing the public internet. This enhances security and can reduce latency. It uses the `private.googleapis.com` domain.
*   **VPC Flow Logs:** Optionally enabled for this subnet to log IP traffic. This is useful for network monitoring, forensics, and security analysis. Logs are aggregated every 10 minutes with 50% sampling.

### 2.3. Cloud Router (`google_compute_router.noah_mvp_router_nat`)

*   **Name:** `router-noah-mvp-nat-${var.gcp_region}`
*   **Region:** Matches the primary subnet's region.
*   **Purpose:** Required component for the Cloud NAT service. It manages BGP sessions for dynamic routing but is used here primarily to enable NAT.

### 2.4. Cloud NAT Gateway (`google_compute_router_nat.noah_mvp_nat_gateway`)

*   **Name:** `nat-noah-mvp-${var.gcp_region}`
*   **Associated Router:** `router-noah-mvp-nat-${var.gcp_region}`.
*   **NAT Configuration:**
    *   Applies to all IP ranges within `subnet-noah-mvp-primary`.
    *   `nat_ip_allocate_option = "AUTO_ONLY"`: Google Cloud automatically allocates regional external IP addresses for NAT.
*   **Purpose:** Enables resources within the `subnet-noah-mvp-primary` that do not have public IP addresses (e.g., Cloud Run services connected via a Serverless VPC Access connector) to initiate outbound connections to the internet (for non-Google APIs or external services). This provides a secure and controlled way for VPC-internal resources to access external endpoints.
*   **NAT Logging:** Optionally enabled to log all NAT events, aiding in troubleshooting and auditing outbound connections.

## 3. Firewall Rules

For the Project Noah MVP, which primarily uses serverless services like Cloud Run, the VPC firewall strategy is kept minimal to align with `TA_Noah_MVP_v1.1` (minimal segmentation and complexity).

*   **Implicit Rules:** GCP VPCs have an implicit "deny all ingress" and "allow all egress" rule if no other rules match.
*   **Cloud Run Ingress:** Ingress traffic to Cloud Run services is primarily managed by the Cloud Run service's own settings (e.g., "Allow all traffic" or "Allow internal traffic and Cloud Load Balancing"), not by VPC firewall rules directly targeting the Cloud Run instances. Access is via public URLs provided by Cloud Run.

### 3.1. `fw_allow_internal_traffic_primary_subnet`

*   **Name:** `fw-noah-allow-internal-primary`
*   **Direction:** INGRESS
*   **Action:** ALLOW
*   **Protocols:** `all` (TCP, UDP, ICMP).
*   **Source Ranges:** `10.10.10.0/24` (the IP range of `subnet-noah-mvp-primary`).
*   **Purpose:** Allows resources within the primary subnet to freely communicate with each other. This rule is proactive for future needs, such as when multiple services (e.g., a Cloud Run service and a Cloud SQL database) are deployed within the same subnet and need to communicate over their private IPs. For the initial MVP with Cloud Run accessing managed Google services (Firestore, Vertex AI via PGA), this rule has limited immediate impact but provides foundational internal connectivity.
*   **Targeting:** Applies to all instances in the VPC. Could be further restricted using `target_tags` if specific resources need this rule.

### 3.2. Egress Traffic Considerations

*   The MVP setup relies on the **default "allow all egress"** behavior of GCP VPCs.
*   Outbound connections from Cloud Run (via a Serverless VPC Access connector if used to reach VPC resources or for NAT) to **Google APIs** are preferentially routed through **Private Google Access**.
*   Outbound connections from Cloud Run (via connector) to the **public internet** (for non-Google services) are routed through the **Cloud NAT Gateway**.
*   This approach simplifies management for the MVP. A stricter production environment might implement a default "deny all egress" firewall rule and explicitly allow only necessary outbound connections.

## 4. `dynamous.ai` Contributions to Network Design

*   **Custom VPC:** Advocating for a custom mode VPC instead of default for granular control from the start.
*   **Private Google Access by Default:** Ensuring PGA is enabled on the primary subnet is a security best practice, minimizing public internet exposure for Google API traffic.
*   **Controlled Egress via NAT:** Implementing Cloud NAT ensures that any outbound internet traffic from VPC resources (like connected Cloud Run services) is managed, source-NATed, and can be logged.
*   **Simplified Firewall for MVP:** The firewall strategy is intentionally kept minimal for the serverless-first MVP, focusing on foundational internal connectivity while relying on service-level controls for Cloud Run and PGA/NAT for secure egress paths. This aligns with the MVP principle of radical velocity without compromising core security for the chosen architecture.
*   **Consideration for Observability:** Suggesting enabling VPC Flow Logs and NAT logging for enhanced visibility and troubleshooting capabilities.

This networking configuration provides a secure, private, and scalable foundation for the Project Noah MVP application services.
