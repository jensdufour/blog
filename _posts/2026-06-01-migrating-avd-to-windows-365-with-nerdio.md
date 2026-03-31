---
categories:
- Microsoft
- Technology
date: '2026-06-01'
status: draft
tags:
- Nerdio
- NME
- Windows 365
- Cloud PC
- Azure Virtual Desktop
- AVD
- Migration
title: 'Migrating from Azure Virtual Desktop to Windows 365 Cloud PCs Using Nerdio Manager'
seo_title: 'Migrate AVD to Windows 365 Cloud PCs with Nerdio Manager'
meta_description: 'Learn how to migrate from Azure Virtual Desktop to Windows 365 Cloud PCs using Nerdio Manager. Step-by-step guide with prerequisites, demo walkthrough and tips.'
focus_keyphrase: 'migrate AVD to Windows 365'
---

## Introduction

The cloud desktop landscape is evolving rapidly, and organizations are constantly evaluating which solutions best fit their operational needs. For many enterprises that adopted Azure Virtual Desktop (AVD) in recent years, a new question has emerged: should we migrate to Windows 365 Cloud PCs?

Microsoft's introduction of Windows 365 brought a simplified, SaaS-based approach to cloud desktops that appeals to organizations seeking predictable costs and reduced infrastructure management. While AVD remains an excellent choice for complex scenarios requiring granular control, Windows 365 offers a streamlined experience that can significantly reduce IT overhead for personal desktop use cases.

<!-- TODO: Add image - Nerdio Manager migration feature overview -->
*Figure 1: Nerdio Manager for Enterprise migration dashboard*

Enter **Nerdio Manager for Enterprise**, a powerful management platform that not only simplifies AVD administration but now enables seamless migration from AVD personal hosts to Windows 365 Cloud PCs. This feature eliminates the complexity traditionally associated with such migrations, allowing IT teams to transition users with minimal disruption.

In this guide, you'll learn:

* The key differences between AVD and Windows 365
* When migration makes strategic sense
* Prerequisites and preparation requirements
* Step-by-step migration instructions using Nerdio Manager
* Best practices for a smooth transition
* How to troubleshoot common issues

Whether you're considering a full migration or a hybrid approach, this article provides everything you need to make informed decisions and execute successfully.

---

## Understanding the Difference: AVD vs Windows 365

Before diving into migration, it's essential to understand what sets these two cloud desktop solutions apart.

### Azure Virtual Desktop (AVD)

Azure Virtual Desktop is an **Infrastructure-as-a-Service (IaaS)** solution that gives organizations complete control over their virtual desktop infrastructure:

| Aspect | Description |
|--------|-------------|
| **Infrastructure** | You manage VMs, storage, networking, and scaling |
| **Pricing Model** | Pay-as-you-go based on compute, storage, and network consumption |
| **Session Types** | Supports both single-session (personal) and multi-session (pooled) desktops |
| **Customization** | Full control over VM sizes, regions, images, and configurations |
| **Networking** | Direct control over VNet configuration, peering, and connectivity |
| **Best For** | Cost optimization experts, multi-session scenarios, complex networking requirements |

### Windows 365 Cloud PC

Windows 365 is a **Software-as-a-Service (SaaS)** solution that simplifies cloud desktop delivery:

| Aspect | Description |
|--------|-------------|
| **Infrastructure** | Microsoft manages all underlying infrastructure |
| **Pricing Model** | Fixed per-user, per-month licensing |
| **Session Types** | Personal desktops only (dedicated Cloud PCs per user) |
| **Customization** | Select from predefined SKUs and configurations |
| **Networking** | Microsoft-managed or Azure Network Connection for hybrid scenarios |
| **Best For** | Predictable budgeting, simplified management, rapid deployment |

### Quick Comparison

| Feature | Azure Virtual Desktop | Windows 365 |
|---------|----------------------|-------------|
| Management Complexity | Higher | Lower |
| Cost Predictability | Variable | Fixed |
| Multi-session Support | Yes | No |
| Infrastructure Control | Full | Limited |
| Scaling Flexibility | High | Moderate |
| Setup Time | Days/Weeks | Hours |
| Licensing | Per-user + Infrastructure | Per-user all-inclusive |

<!-- TODO: Add image - AVD vs Windows 365 comparison diagram -->
*Figure 2: Visual comparison of AVD and Windows 365 architectures*

---

## When to Consider Migration

Migration from AVD to Windows 365 isn't right for every organization. Here's how to evaluate if it makes sense for your environment.

### Scenarios Favoring Migration

**1. Simplifying IT Operations**
If your IT team spends significant time managing AVD infrastructure, scaling hosts, managing images, troubleshooting VM issues, Windows 365's managed approach can free up resources for more strategic initiatives.

**2. Predictable Budgeting Requirements**
Organizations that struggle with variable AVD costs or need fixed monthly expenses for cloud desktops benefit from Windows 365's per-user licensing model.

**3. Personal Desktop Use Cases**
If you're primarily using AVD personal host pools (rather than multi-session), Windows 365 provides equivalent functionality with less management overhead.

**4. Rapid Onboarding Needs**
When you need to quickly provision desktops for new employees or contractors without infrastructure setup delays.

### Scenarios Where AVD Remains Better

* **Multi-session requirements**: Windows 365 doesn't support shared desktop scenarios
* **Complex networking**: Organizations with intricate network topologies and compliance requirements
* **Cost-sensitive variable workloads**: Environments where VMs can be deallocated during off-hours
* **Specialized GPU requirements**: Some GPU scenarios are better served by AVD

---

## Prerequisites and Preparation

Successful migration requires proper preparation. Ensure the following prerequisites are met before starting.

### Licensing Requirements

**Windows 365 License Types:**

* **Windows 365 Enterprise**: Requires Microsoft Intune and Entra ID P1 (included in Microsoft 365 E3/E5)
* **Windows 365 Business**: Standalone option for smaller organizations
* **Windows 365 Frontline**: For shift workers who share Cloud PCs

In Nerdio Manager, you'll configure **License Groups** that map to your Windows 365 licenses. Ensure you have sufficient licenses for all users being migrated.

### Technical Prerequisites

| Requirement | Description |
|-------------|-------------|
| **Nerdio Manager for Enterprise** | Deployed and configured with appropriate permissions |
| **Azure Network Connection** | Configured if hybrid-joined Cloud PCs are needed |
| **Microsoft Entra ID** | Users must exist in Entra ID |
| **Intune Enrollment** | Required for Enterprise Cloud PCs |
| **AVD Personal Host Pools** | Migration is supported for personal hosts only |

### Nerdio Manager Permissions

Ensure Nerdio Manager has the following permissions:

* Microsoft.DesktopVirtualization (AVD management)
* Windows 365 Cloud PC administration
* Microsoft Graph API access for user and license management
* Intune policy management (if using Enterprise Cloud PCs)

### Planning Considerations

**User Communication**

* Notify users about migration timeline and expected changes
* Provide training on accessing Windows 365 Cloud PCs
* Set expectations for any downtime during transition

**Migration Windows**

* Schedule migrations during low-usage periods
* Consider time zones for global organizations
* Plan for staged rollouts rather than big-bang migrations

**Rollback Planning**

* Keep AVD resources available until migration is validated
* Use Nerdio's cleanup scheduling to delay AVD resource deletion
* Document rollback procedures before starting

---

## Migration Options in Nerdio Manager

Nerdio Manager provides flexible migration options to suit different scenarios:

### Individual Host Pool Migration

Migrate an entire host pool at once. Best for:

* Dedicated pools for specific departments
* Smaller environments
* Controlled, phased migrations

### Bulk Host Pool Migration

Migrate multiple host pools simultaneously. Best for:

* Large-scale migrations
* Environments with many similar pools
* Accelerated timelines

### Individual Host Migration

Migrate specific hosts within a pool. Best for:

* Pilot migrations
* Testing with select users
* Granular control

### Bulk Host Migration

Migrate multiple hosts from a pool at once. Best for:

* Team-based migrations
* Phased user group rollouts
* Hybrid AVD/Windows 365 scenarios

---

## Step-by-Step Migration Guide

Follow these detailed steps to migrate from AVD to Windows 365 Cloud PCs using Nerdio Manager.

### Step 1: Access the Migration Wizard

1. Log in to **Nerdio Manager for Enterprise**
2. Navigate to **Workspaces** in the left navigation
3. Select the workspace containing your target host pool(s)
4. Choose your migration approach:

   **For Individual Host Pool:**
   * Locate the host pool
   * Click the **more options menu**
   * Select **Hosts > Migrate to Windows 365**

   **For Bulk Host Pools:**
   * Select multiple host pools using checkboxes
   * From **Select bulk action**, choose **Migrate to Windows 365 for selected**

   **For Individual or Bulk Hosts:**
   * Navigate into the host pool
   * Select the specific host(s)
   * Use the more options menu or bulk action menu accordingly

<!-- TODO: Add image - Nerdio Manager migration wizard entry point -->
*Figure 3: Accessing the migration wizard in Nerdio Manager*

### Step 2: Assign Users to Hosts

The first tab of the migration wizard configures user assignments:

| Setting | Description | Recommendation |
|---------|-------------|----------------|
| **Group Name** | Name for the migration group | Use descriptive names (e.g., "Finance-Team-Migration") |
| **License Group** | Windows 365 license group to assign | Select the appropriate license tier for your users |

<!-- TODO: Add screenshot - User assignment tab in migration wizard -->
*Figure 4: Assigning users and license groups in the migration wizard*

Click **Next** to proceed.

### Step 3: Configure Provisioning Policy

The provisioning policy defines how Cloud PCs are created. Choose between creating a new policy or selecting an existing one.

**Creating a New Provisioning Policy:**

| Setting | Description | Recommendation |
|---------|-------------|----------------|
| **Name** | Unique policy name | Use consistent naming conventions |
| **Description** | Policy description | Document purpose and scope |
| **Language and Region** | Default language setting | Match user preferences or organizational standards |
| **Default Cloud PC Image** | Image used for provisioning and resets | Select a pre-configured image or gallery image |
| **Network Connection** | Azure Network Connection | Select existing or create new with same subnet |
| **Single Sign-On** | Enable Entra SSO | **Recommended**: Enable for seamless user experience |

> **Pro Tip**: If you want Cloud PCs to use the same subnet as your AVD hosts, select **"Create new network connection with the same subnet"** option.

Click **Next** to continue.

<!-- TODO: Add image - Provisioning policy configuration screen -->
*Figure 5: Configuring the provisioning policy for Windows 365*

### Step 4: Configure User Settings

User settings control the Cloud PC experience for end users:

| Setting | Description | Recommendation |
|---------|-------------|----------------|
| **Name** | User settings policy name | Descriptive name aligned with user group |
| **Local Admin Enabled** | Grant local admin rights | Based on organizational policy |
| **Allow Restore** | Enable user-initiated restore | **Recommended**: Enable for self-service recovery |
| **Backup Frequency** | Snapshot interval (hours) | 4-12 hours typical; balance protection vs. storage |
| **Provisioning Source Type** | Image or Snapshot-based | **Image**: Fresh provisioning / **Snapshot**: Preserve current state |

> **Important**: Choose **Snapshot** as the provisioning source if you want to migrate the current state of users' AVD desktops, including installed applications and settings.

<!-- TODO: Add screenshot - User settings configuration in migration wizard -->
*Figure 6: Configuring user settings and provisioning source type*

Click **Next** to proceed.

### Step 5: Schedule the Migration

Configure when the migration should occur:

**Enable Scheduling:**

1. Toggle the schedule from **Disabled** to **Enabled**
2. Configure the following:

| Setting | Description |
|---------|-------------|
| **Name** | Schedule name |
| **Description** | Schedule description |
| **Start Date** | When migration begins |
| **Time Zone** | Applicable time zone |
| **Start Time** | Hour and minute to begin |

**Configure End-User Messaging:**

1. Toggle messaging from **Disabled** to **Enabled**
2. Set the **Delay** (time between message and migration start)
3. Customize the **Message** users will see

<!-- TODO: Add screenshot - Migration schedule and end-user messaging configuration -->
*Figure 7: Schedule and end-user messaging configuration*

Click **Next** to continue.

### Step 6: Configure Cleanup

Cleanup settings manage AVD resource removal after migration:

1. Toggle cleanup from **Disabled** to **Enabled**
2. Configure:

| Setting | Description | Recommendation |
|---------|-------------|----------------|
| **Time Zone** | Applicable time zone | Match your operational time zone |
| **Deletion Date** | When to delete AVD resources | **Minimum 7 days** after migration for validation |
| **Deletion Time** | Specific time for deletion | Schedule during maintenance windows |

> **Warning**: Once cleanup runs, AVD resources are permanently deleted. Ensure thorough validation before the deletion date.

<!-- TODO: Add screenshot - Cleanup configuration with deletion date -->
*Figure 8: Cleanup configuration for AVD resource deletion*

Click **Next** to proceed.

### Step 7: Set Up Notifications

Configure email notifications to keep users informed:

1. Toggle notifications from **Disabled** to **Enabled**
2. Configure:

| Setting | Description |
|---------|-------------|
| **Send emails from** | Email address for notifications |
| **Message to end user** | Custom message content |

Click **Submit** to initiate the migration.

<!-- TODO: Add image - Migration summary before submission -->
*Figure 9: Review migration settings before submission*

---

## Post-Migration Best Practices

After migration completes, follow these best practices to ensure success:

### Immediate Verification (Day 1)

* Verify all Cloud PCs provisioned successfully in Nerdio Manager
* Confirm users can connect to their Cloud PCs
* Check application functionality on migrated desktops
* Validate network connectivity and access to resources
* Monitor Intune for successful enrollment

<!-- TODO: Add screenshot - Nerdio Manager showing successful Cloud PC provisioning -->
*Figure 10: Cloud PC provisioning status in Nerdio Manager*

### Short-Term Validation (Week 1)

* Gather user feedback on performance and experience
* Address any reported issues promptly
* Verify backup/restore functionality works correctly
* Confirm SSO is functioning as expected
* Review Windows 365 analytics for usage patterns

### Documentation Updates

* Update runbooks and operational procedures
* Revise user guides and training materials
* Document any customizations or configurations
* Update architecture diagrams and inventory

### AVD Decommissioning (After Validation Period)

* Confirm no users require AVD access
* Verify cleanup ran successfully or manually remove resources
* Update cost tracking and chargeback
* Archive any required logs or data

---

## Troubleshooting Common Issues

### Provisioning Failures

**Symptom**: Cloud PC fails to provision or stuck in "Provisioning" state

**Common Causes and Solutions**:

| Cause | Solution |
|-------|----------|
| Insufficient licenses | Verify license availability in Nerdio License Groups |
| Network connection issues | Check Azure Network Connection health in Intune |
| Image problems | Validate Cloud PC image is correctly configured |
| Entra ID sync delays | Wait for directory sync or force sync |

### Network Connectivity Issues

**Symptom**: Cloud PC can't reach on-premises resources

**Solutions**:

1. Verify Azure Network Connection is healthy
2. Check DNS resolution for internal resources
3. Confirm firewall rules allow Cloud PC traffic
4. Validate VPN or ExpressRoute connectivity

### License Assignment Problems

**Symptom**: Users receive "No license assigned" errors

**Solutions**:

1. Verify license group assignment in Nerdio
2. Check Microsoft 365 admin center for license availability
3. Ensure user is member of correct Entra ID group
4. Allow time for license propagation (up to 30 minutes)

### User Access Issues

**Symptom**: Users can't sign in to Cloud PC

**Solutions**:

1. Verify user exists in Entra ID
2. Check user is assigned to the Cloud PC
3. Validate SSO configuration if enabled
4. Confirm no Conditional Access policies blocking access

### Rollback Procedures

If migration issues require rollback:

1. Keep AVD hosts available until validation completes
2. Remove user from Windows 365 provisioning group
3. Re-enable AVD session host for the user
4. Document issues for future migration attempts

---

## Conclusion

Migrating from Azure Virtual Desktop to Windows 365 Cloud PCs represents a strategic shift toward simplified cloud desktop management. With Nerdio Manager for Enterprise, this transition becomes straightforward, enabling IT teams to move users from AVD personal hosts to Cloud PCs through an intuitive wizard-driven process.

**Key Benefits of Using Nerdio Manager for Migration:**

* **Unified Management**: Continue managing both AVD and Windows 365 from a single console
* **Automated Workflows**: Scheduling, user notification, and cleanup automation
* **Flexible Options**: Migrate individual hosts, entire pools, or bulk selections
* **Reduced Risk**: Built-in scheduling and validation periods

Whether you're migrating a handful of users as a pilot or transitioning your entire personal desktop fleet, Nerdio Manager provides the tools and automation to ensure success.
