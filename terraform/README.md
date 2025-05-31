# Terraform Configuration for Project Noah MVP V1.0 - GCP Infrastructure

This directory contains Terraform scripts to define and manage the Google Cloud Platform (GCP) infrastructure for Project Noah MVP V1.0.

## Overview

The primary goal of this Terraform setup is to provision the necessary GCP resources in an automated and repeatable manner, adhering to Infrastructure as Code (IaC) best practices. This includes project setup, IAM configurations, networking, secrets management, and service-specific resources.

## Files

*   `variables.tf`: Defines input variables for customizing the deployment (e.g., project ID, organization ID, billing account).
*   `project_iam.tf`: Configures the GCP project, enables necessary APIs, defines service accounts, and sets up initial IAM policies.
*   `networking.tf`: Defines VPC networks, subnets, firewall rules, etc.
*   `secrets.tf`: Configures Google Cloud Secret Manager placeholders.
*   `monitoring_logging.tf`: Sets up Cloud Logging exports and basic Cloud Monitoring dashboards.
*   `database.tf`: (To be added in Task 1.4 or if a central DB is provisioned earlier) Defines database instances (e.g., Cloud SQL for PostgreSQL for RAG).
*   `outputs.tf`: Defines outputs from the Terraform configuration (e.g., project ID, service account emails).
*   `README.md`: This file. Provides an overview and instructions.
*   `project_iam.md`: Detailed documentation for IAM resources created by `project_iam.tf`.
*   `networking.md`: Detailed documentation for networking resources.
*   `secrets.md`: Detailed documentation for secrets management.
*   `monitoring_logging.md`: Detailed documentation for logging and monitoring setup.

## Prerequisites

1.  **Terraform Installed:** Ensure Terraform (v1.x or later) is installed on your local machine or CI/CD environment.
2.  **Google Cloud SDK (gcloud CLI) Installed & Authenticated:**
    *   Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
    *   Authenticate with GCP: `gcloud auth login`
    *   Set up Application Default Credentials: `gcloud auth application-default login`
3.  **Permissions:** The user or service account executing Terraform needs sufficient permissions to create projects, manage IAM, and enable billing for the target organization. Typically, roles like `roles/resourcemanager.projectCreator`, `roles/billing.user`, and `roles/orgpolicy.policyAdmin` (or higher) at the organization level might be required.
4.  **Required Variables:** You will need to provide values for the following variables, typically through a `terraform.tfvars` file or environment variables:
    *   `gcp_project_id`: The globally unique ID for your new project.
    *   `gcp_project_name`: Display name for the project.
    *   `gcp_org_id`: Your Google Cloud Organization ID.
    *   `gcp_billing_account`: Your Google Cloud Billing Account ID.
    *   Optionally, `aem_developer_group_email` or `aem_developer_user_email` for granting project access.

    Example `terraform.tfvars` file:
    ```tfvars
    gcp_project_id      = "noah-genesis-mvp-xxxx" # Replace xxxx with unique suffix
    gcp_project_name    = "Project Noah Genesis MVP"
    gcp_org_id          = "your-organization-id"
    gcp_billing_account = "your-billing-account-id"
    gcp_region          = "us-central1"
    # aem_developer_user_email = "your-email@example.com"
    ```

## HIPAA Compliance & Business Associate Addendum (BAA)

**CRITICAL:** Project Noah MVP V1.0 is intended to handle data that may be subject to HIPAA regulations. It is imperative that a **Business Associate Addendum (BAA) is executed with Google Cloud** for the GCP project created and managed by these Terraform scripts.

*   The customer (entity deploying this project) is responsible for reviewing and accepting the Google Cloud BAA. This can typically be done through the Google Cloud Console IAM & Admin page or by contacting your Google Cloud account manager.
*   Ensure that all services used within this project that will handle Protected Health Information (PHI) are covered by the Google Cloud BAA.
*   Adherence to HIPAA is a shared responsibility. Google Cloud provides a compliant infrastructure, but the customer is responsible for configuring and using services in a HIPAA-compliant manner.

Refer to the [Google Cloud HIPAA Compliance documentation](https://cloud.google.com/security/compliance/hipaa) for more details.

## Usage

1.  **Initialize Terraform:**
    ```bash
    terraform init
    ```
2.  **Create a `terraform.tfvars` file** with the required variable values (see Prerequisites).
3.  **Plan the deployment:**
    ```bash
    terraform plan -out=tfplan
    ```
    Review the plan carefully to understand the resources that will be created.
4.  **Apply the configuration:**
    ```bash
    terraform apply tfplan
    ```
    Type `yes` when prompted to confirm.

## dynamous.ai Contributions

The Terraform configurations in this directory have been designed with input from `dynamous.ai` to incorporate best practices for GCP project security, IAM least-privilege principles, and considerations for applications with HIPAA requirements. This includes structuring service accounts for specific roles and ensuring only necessary APIs are enabled.
