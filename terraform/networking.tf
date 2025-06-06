# ------------------------------------------------------------------------------
# VPC Network for Project Noah MVP
# ------------------------------------------------------------------------------
resource "google_compute_network" "noah_mvp_vpc" {
  project                 = google_project.noah_mvp_project.project_id
  name                    = "vpc-noah-mvp"
  auto_create_subnetworks = false      # Custom mode VPC
  mtu                     = 1460       # Standard MTU
  routing_mode            = "REGIONAL" # For Cloud NAT, regional routing is common. Can be GLOBAL if needed.
}

# ------------------------------------------------------------------------------
# Subnetwork for primary region
# ------------------------------------------------------------------------------
resource "google_compute_subnetwork" "noah_mvp_subnet_primary" {
  project                  = google_project.noah_mvp_project.project_id
  name                     = "subnet-noah-mvp-primary-${var.gcp_region}"
  ip_cidr_range            = "10.10.10.0/24" # Example range, ensure it doesn't overlap with other networks
  region                   = var.gcp_region
  network                  = google_compute_network.noah_mvp_vpc.id
  private_ip_google_access = true # Enable Private Google Access for this subnet

  log_config { # Optional: Enable VPC Flow Logs for the subnet for audit/troubleshooting
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5 # Sample 50% of packets
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# ------------------------------------------------------------------------------
# Cloud Router for NAT
# ------------------------------------------------------------------------------
resource "google_compute_router" "noah_mvp_router_nat" {
  project = google_project.noah_mvp_project.project_id
  name    = "router-noah-mvp-nat-${var.gcp_region}"
  region  = var.gcp_region
  network = google_compute_network.noah_mvp_vpc.id
}

# ------------------------------------------------------------------------------
# Cloud NAT Gateway for the primary subnet
# Allows resources in the subnet (e.g., Cloud Run via VPC connector) to securely
# access the internet for non-Google APIs or external services.
# ------------------------------------------------------------------------------
resource "google_compute_router_nat" "noah_mvp_nat_gateway" {
  project                            = google_project.noah_mvp_project.project_id
  name                               = "nat-noah-mvp-${var.gcp_region}"
  router                             = google_compute_router.noah_mvp_router_nat.name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS" # Required setting for this option

  subnetwork {
    name                    = google_compute_subnetwork.noah_mvp_subnet_primary.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"] # NAT all IP ranges in the subnet
  }

  log_config { # Optional: Enable NAT logging for audit/troubleshooting
    enable = true
    filter = "ALL" # Log all NAT events, can be "ERRORS_ONLY" or "TRANSLATIONS_ONLY"
  }

  # Define minimum and maximum number of ports per VM (or per Serverless VPC Connector)
  # Defaults are usually fine for MVP.
  # min_ports_per_vm = 64
  # max_ports_per_vm = 65536
}

# ------------------------------------------------------------------------------
# Firewall Rules
# For MVP with serverless (Cloud Run) focus, VPC firewall rules are minimal.
# Cloud Run ingress is managed by its service settings (e.g., "Allow all traffic").
# Egress from Cloud Run (via Serverless VPC Access connector) to Google APIs
# is handled by Private Google Access. Egress to other internet addresses is
# handled by the Cloud NAT gateway.
# ------------------------------------------------------------------------------

resource "google_compute_firewall" "fw_allow_internal_traffic_primary_subnet" {
  project   = google_project.noah_mvp_project.project_id
  name      = "fw-noah-allow-internal-primary"
  network   = google_compute_network.noah_mvp_vpc.id
  direction = "INGRESS"
  priority  = 1000 # Default priority

  allow {
    protocol = "all" # Allows all protocols (tcp, udp, icmp)
    # For stricter control, specify ports: e.g., ["tcp:80", "tcp:443", "tcp:8080"]
  }

  source_ranges = [google_compute_subnetwork.noah_mvp_subnet_primary.ip_cidr_range]
  # target_tags = ["noah-internal-service"] # Optional: Apply to specific resources via network tags

  description = "Allows all internal traffic originating from and targeting the primary subnet. Useful for inter-service communication within the VPC."
}

# Note on Egress:
# By default, VPC networks allow all egress traffic.
# For a stricter setup, a high-priority "deny all egress" rule could be added,
# followed by specific lower-priority "allow" rules for necessary outbound traffic
# (e.g., DNS, NTP, specific external APIs).
# For MVP simplicity and alignment with TA_Noah_MVP_v1.1 (minimal segmentation),
# we rely on the default allow egress, with PGA and NAT controlling paths for key services.
