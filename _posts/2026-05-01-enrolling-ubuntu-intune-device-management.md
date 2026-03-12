---
categories:
- Linux
- Microsoft
- Technology
date: '2026-05-01'
status: draft
tags:
- Ubuntu
- Intune
- Linux
- Entra ID
- MDM
- Compliance
title: 'Enrolling Ubuntu 24.04 LTS in Microsoft Intune for Device Management'
seo_title: 'Ubuntu 24.04 LTS Intune Enrollment: Full Guide'
meta_description: 'Enroll Ubuntu 24.04 LTS in Microsoft Intune for enterprise device management. Covers prerequisites, compliance policies, and troubleshooting.'
focus_keyphrase: 'Ubuntu 24.04 Intune enrollment'
---

## Introduction to Intune Enrollment

This article covers **Ubuntu 24.04 Intune enrollment** for enterprise device management.

> **Note:** This guide focuses exclusively on **Intune enrollment and device management**. For Entra ID authentication setup using AuthD, see [Entra ID Authentication with AuthD on Ubuntu 24.04 LTS](https://jensdufour.be/2026/02/04/entra-id-authentication-with-authd/). For a fully automated zero-touch deployment, see [Automating Ubuntu Entra ID Authentication](https://jensdufour.be/2026/01/02/zero-touch-ubuntu-entra-id-autoinstall/).

**Intune enrollment** brings enterprise device management to Linux workstations. As organizations increasingly adopt Ubuntu for development, data science, and general productivity, there is a need for centralized device management.

Consequently, Microsoft Intune provides the ideal solution, allowing IT administrators to manage Ubuntu devices alongside Windows, macOS, iOS, and Android devices, although this Linux management is still rather limited.

<!-- TODO: Add image - Ubuntu desktop with Intune enrollment status -->
*Figure 1: Ubuntu 24.04 LTS showing successful Intune enrollment status*

Traditionally, Linux management often relied on custom scripts, configuration management tools like Ansible or Puppet, or simply trusting users to maintain their own devices. With **Intune enrollment**, you can achieve:

* First, **centralized device inventory** across all platforms
* Second, **compliance policy enforcement** for security requirements
* Third, **Conditional Access integration** to protect corporate resources
* Also, **consistent management experience** for IT administrators
* Finally, **self-service enrollment** for end users

Specifically, in this guide, you’ll learn how to:

* First, configure Azure and Intune for Linux enrollment
* Second, install the required Microsoft packages on Ubuntu
* Third, complete the device enrollment process
* Finally, verify compliance and troubleshoot common issues

Whether you’re adding a few developer workstations or rolling out Ubuntu across your organization, this comprehensive guide provides everything you need for successful **Intune enrollment**.

---

## Understanding Intune Enrollment Components

Before configuring **Intune enrollment**, it’s essential to first understand the components involved and how they work together.

### Microsoft Intune for Linux

First, let’s examine Microsoft Intune, which extends its device management capabilities to Linux distributions, focusing on Ubuntu. As a result, you can manage Ubuntu devices alongside your existing devices.

Key capabilities include:

| Capability | Description |
| --- | --- |
| **Device Enrollment** | Register Ubuntu devices with your organization |
| **Compliance Policies** | Enforce security requirements (encryption, password policies) |
| **Device Inventory** | Track hardware and software information |
| **Conditional Access** | Control access to resources based on device compliance |
| **Device Actions** | Remote wipe, retire, and other management actions |

Currently, the supported Ubuntu versions are:

* Ubuntu Desktop 22.04 LTS (earlier version)
* Ubuntu Desktop 24.04 LTS (recommended)

### Microsoft Edge for Linux

Notably, Microsoft Edge serves as a critical component for **Intune enrollment**. Specifically, it provides:

* First, the authentication flow for device enrollment
* Second, a secure browser for accessing organizational resources
* Third, integration with Conditional Access policies
* Lastly, support for enterprise authentication scenarios

### Architecture Overview

To better understand the process, the following diagram illustrates how **Intune enrollment** works:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Ubuntu 24.04 LTS                            │
│                                                                     │
│  ┌──────────────────────────────────────────┐                       │
│  │     Microsoft Intune Portal App          │                       │
│  │     (Device Enrollment & Compliance)     │                       │
│  └──────────────────────────────────────────┘                       │
│                        │                                            │
│  ┌──────────────────────────────────────────┐                       │
│  │     Microsoft Edge Browser               │                       │
│  │     (Authentication & Web Access)        │                       │
│  └──────────────────────────────────────────┘                       │
│                        │                                            │
└────────────────────────│────────────────────────────────────────────┘
                         │
                         ▼
              ┌────────────────────────────────────────────┐
              │           Microsoft Entra ID               │
              │      (Authentication & Authorization)      │
              └────────────────────────────────────────────┘
                                    │
                                    ▼
              ┌────────────────────────────────────────────┐
              │           Microsoft Intune                 │
              │     (Device Management & Compliance)       │
              └────────────────────────────────────────────┘
```

The **Intune enrollment** flow works as follows:

1. First, the user launches the Intune Portal app on Ubuntu
2. Then, the app redirects to Microsoft Edge for authentication
3. Next, the user signs in with their Entra ID credentials
4. Subsequently, Intune evaluates the device against compliance policies
5. Finally, the device is enrolled and compliance status is reported

---

## Prerequisites for Intune Enrollment

Before implementing **Intune enrollment**, you must ensure all prerequisites are met. Accordingly, this section covers licensing, technical requirements, and network considerations.

### Licensing Requirements

First and foremost, users enrolling Ubuntu devices need the following licenses:

| License | Purpose | Minimum Required |
| --- | --- | --- |
| **Microsoft Intune** | Device enrollment and compliance | Required |
| **Microsoft Entra ID P1** | Conditional Access (optional but recommended) | Recommended |
| **Microsoft 365 E3/E5** | Includes both Intune and Entra ID P1 | Alternative |

### Technical Prerequisites

In addition to licensing, ensure these technical requirements are met.

**Ubuntu System Requirements:**

* Ubuntu Desktop 24.04 LTS (or alternatively, 22.04 LTS)
* GNOME desktop environment (included by default)
* Specifically, amd64 architecture
* Network connectivity to Microsoft services
* Also, a local administrator account for initial setup

**Additionally, Azure Requirements:**

* Intune Administrator role for device management
* Furthermore, permission to configure enrollment restrictions
* Also, access to Intune Admin Center

### Network Requirements

Furthermore, ensure the following endpoints are accessible from your Ubuntu systems:

| Endpoint | Purpose |
| --- | --- |
| `login.microsoftonline.com` | Entra ID authentication |
| `*.manage.microsoft.com` | Intune management |
| `graph.microsoft.com` | Microsoft Graph API |
| `*.blob.core.windows.net` | Configuration downloads |
| `packages.microsoft.com` | Microsoft package repository |



---

## Azure Configuration for Intune Enrollment

Now that you understand the prerequisites, the next step is to configure Intune to accept Linux enrollment and create appropriate compliance policies.

### Step 1: Enable Linux Enrollment

By default, Linux enrollment may be restricted. Therefore, you need to enable it in Intune:

1. **Navigate to Intune Admin Center**
   * First, go to [intune.microsoft.com](https://intune.microsoft.com/)
   * Then, sign in with your administrator credentials
2. **Configure Enrollment Restrictions**
   * Navigate to **Devices** > **Enrollment** > **Enrollment device platform restrictions**
   * Next, click on the default policy (or create a new one)
   * Under **Linux**, set to **Allow**
   * Finally, save your changes

<!-- TODO: Add image - Intune enrollment restrictions showing Linux enabled -->
*Figure 2: Intune enrollment restrictions configuration for Linux*

### Step 2: Create Compliance Policy for Linux

After enabling enrollment, create a compliance policy to enforce security requirements on Ubuntu devices:

1. **Navigate to Compliance Policies**
   * First, go to **Devices** > **Compliance** > **Policies**
   * Then, click **Create policy**
2. **Configure Policy Settings**
   * For Platform, select: **Linux**
   * For Profile type, choose: **Linux compliance policy**
3. **Configure Compliance Settings**
   * **Require encryption**: Yes
   * **Minimum password length**: 8 characters
   * **Required distributions**: Ubuntu 24.04 LTS
   * **Allowed OS versions**: 24.04 and later
4. **Configure Actions for Noncompliance**
   * Mark device noncompliant: Immediately
   * Optionally, send email to user
   * Additionally, retire device: After 90 days (optional)
5. **Assign the Policy**
   * Assign to a group containing Linux users
   * Alternatively, assign to all users if appropriate

### Step 3: Configure Conditional Access (Optional)

Moreover, for enhanced security, you can create a Conditional Access policy for Linux devices:

1. **Navigate to Conditional Access**
   * First, go to **Microsoft Entra ID** > **Security** > **Conditional Access**
   * Then, click **Create new policy**
2. **Configure Policy**
   * **Name**: Require compliant Linux devices
   * **Users**: Select your Linux users group
   * **Cloud apps**: Select target applications
   * **Conditions**:
     + **Device platforms**: Linux
   * **Grant:** Require device to be marked as compliant
3. **Enable the Policy**
   * Importantly, set to **On** only after testing in report-only mode

### Step 4: Create User Group for Linux Users

Finally, create a dedicated security group for Linux users.

1. **Create Security Group**
   * Navigate to **Microsoft Entra ID** > **Groups** > **New group**
   * Set Group type: Security
   * Specify Group name: `Linux Workstation Users`
   * Then, add members who will use Linux workstations
2. **Assign Licenses**
   * Ensure all group members have Intune licenses assigned
   * Afterward, verify license assignment in user properties

---

## Ubuntu Configuration: Installing Microsoft Packages

With Azure configured for **Intune enrollment**, you can now proceed to install the required Microsoft packages on Ubuntu.

### Step 1: Update System Packages

To begin, start with a fresh system update:

```
# Update package lists and upgrade existing packages
sudo apt update
sudo apt upgrade -y

# Install required utilities
sudo apt install -y curl gpg software-properties-common
```

### Step 2: Add Microsoft GPG Key

Next, add the Microsoft signing key to verify package authenticity:

```
# Download and install Microsoft GPG key
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/
rm microsoft.gpg
```

### Step 3: Add Microsoft Edge Repository

Since Microsoft Edge is required for the enrollment authentication flow, add its repository:

```
# Add Microsoft Edge repository
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list'

# Update package list
sudo apt update

# Install Microsoft Edge
sudo apt install -y microsoft-edge-stable
```

<!-- TODO: Add image - Terminal showing Microsoft Edge installation -->
*Figure 3: Installing Microsoft Edge on Ubuntu*

### Step 4: Add Microsoft Intune Repository

Similarly, add the repository for the Intune Portal app:

```
# Get Ubuntu version information
UBUNTU_VERSION=$(lsb_release -rs)
UBUNTU_CODENAME=$(lsb_release -cs)

# Add Microsoft Intune repository
sudo sh -c "echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/${UBUNTU_VERSION}/prod ${UBUNTU_CODENAME} main\" > /etc/apt/sources.list.d/microsoft-ubuntu-${UBUNTU_CODENAME}-prod.list"

# Update package list
sudo apt update
```

### Step 5: Install Intune Portal

Once the repositories are configured, install the Microsoft Intune Portal application:

```
# Install Intune Portal
sudo apt install -y intune-portal

# Verify installation
dpkg -l | grep intune-portal
```

### Step 6: Reboot System

Lastly, reboot the system to ensure all changes take effect:

```
# Reboot the system
sudo reboot
```

---

## Completing Intune Enrollment

At this point, with all packages installed, you’re ready to complete the **Intune enrollment** process.

### Step 1: Launch Intune Portal

1. **Open the Intune App**
   * First, click Activities (top-left corner)
   * Next, search for “Intune” or “Company Portal”
   * Then, click the Intune Portal app iconAlternatively, launch from terminal:`intune-portal`

<!-- TODO: Add image - Intune Portal app in Ubuntu Activities -->
*Figure 4: Launching Intune Portal from Ubuntu Activities*

### Step 2: Sign In

1. **Click Sign In**
   * The app will automatically open Microsoft Edge for authentication
2. **Enter Credentials**
   * Enter your organizational email address
   * Provide your password when prompted
   * Additionally, complete MFA if required
3. **Accept Permissions**
   * Carefully review the permissions requested
   * Then, accept the organization’s terms of use

### Step 3: Complete Enrollment

1. **Device Registration**
   * The app will automatically register your device with Intune
   * Typically, this process takes 1-2 minutes
2. **Compliance Check**
   * Subsequently, Intune evaluates your device against compliance policies
   * If needed, address any compliance issues flagged
3. **Enrollment Confirmation**
   * Upon completion, the app shows “Your device is enrolled”
   * Consequently, the device appears in Intune Admin Center

### Step 4: Verify Enrollment Status

To confirm successful enrollment, verify the status from both sides.

**First, on the Ubuntu Device:**

```
# Check Intune enrollment status
intune-portal --status

# View detailed device information
intune-portal --info
```

**Second, in Intune Admin Center:**

1. First, navigate to **Devices** > **All devices**
2. Then, locate your Linux device in the list
3. Finally, verify the following:
   * **Managed by**: Intune
   * **Compliance**: Compliant (or pending)
   * **OS**: Linux (Ubuntu)

<!-- TODO: Add image - Intune Admin Center showing enrolled Ubuntu device -->
*Figure 5: Ubuntu device visible in Intune Admin Center*

---

## Automation Script for Intune Enrollment

To streamline consistent deployments of **Intune enrollment**, consider using this automation script:

```
#!/bin/bash
#===============================================================================
# Script Name: setup-intune-ubuntu.sh
# Description: Automated setup of Microsoft Intune on Ubuntu 24.04 LTS
# Author: Enterprise IT
# Version: 1.0
#===============================================================================

set -e  # Exit on error

# Logging
LOG_FILE="/var/log/intune-setup.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

# Check Ubuntu version
if ! grep -q "24.04\|22.04" /etc/lsb-release; then
    error "This script is designed for Ubuntu 22.04 or 24.04 LTS"
fi

log "Starting Intune setup for Ubuntu..."

#===============================================================================
# PHASE 1: Install Prerequisites
#===============================================================================

log "Phase 1: Installing prerequisites..."

apt update
apt install -y curl gpg software-properties-common

log "Prerequisites installed"

#===============================================================================
# PHASE 2: Add Microsoft GPG Key
#===============================================================================

log "Phase 2: Adding Microsoft GPG key..."

if [ ! -f /usr/share/keyrings/microsoft.gpg ]; then
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /tmp/microsoft.gpg
    install -o root -g root -m 644 /tmp/microsoft.gpg /usr/share/keyrings/
    rm /tmp/microsoft.gpg
    log "Microsoft GPG key installed"
else
    log "Microsoft GPG key already exists"
fi

#===============================================================================
# PHASE 3: Add Microsoft Repositories
#===============================================================================

log "Phase 3: Adding Microsoft repositories..."

# Add Microsoft Edge repository
if [ ! -f /etc/apt/sources.list.d/microsoft-edge.list ]; then
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list
    log "Microsoft Edge repository added"
else
    log "Microsoft Edge repository already exists"
fi

# Add Microsoft Intune repository
UBUNTU_VERSION=$(lsb_release -rs)
UBUNTU_CODENAME=$(lsb_release -cs)
INTUNE_REPO_FILE="/etc/apt/sources.list.d/microsoft-ubuntu-${UBUNTU_CODENAME}-prod.list"

if [ ! -f "$INTUNE_REPO_FILE" ]; then
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/${UBUNTU_VERSION}/prod ${UBUNTU_CODENAME} main" > "$INTUNE_REPO_FILE"
    log "Microsoft Intune repository added"
else
    log "Microsoft Intune repository already exists"
fi

#===============================================================================
# PHASE 4: Install Microsoft Packages
#===============================================================================

log "Phase 4: Installing Microsoft packages..."

apt update
apt install -y microsoft-edge-stable intune-portal

log "Microsoft Edge and Intune Portal installed"

#===============================================================================
# COMPLETION
#===============================================================================

log "=============================================="
log "Setup completed successfully!"
log "=============================================="
log ""
log "Next steps:"
log "1. Reboot the system"
log "2. Launch the Intune Portal app"
log "3. Sign in with your organizational account"
log "4. Complete device enrollment"
log ""
log "Log file: ${LOG_FILE}"

echo ""
echo "Reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    reboot
fi
```

### Using the Automation Script

To use this script, follow these steps:

1. **Save the script** as `setup-intune-ubuntu.sh`
2. **Run the script**:`chmod +x setup-intune-ubuntu.sh sudo ./setup-intune-ubuntu.sh`
3. **Complete post-script steps**:
   * First, reboot the system
   * Next, launch Intune Portal
   * Finally, complete enrollment with your organizational account

---

## Troubleshooting Intune Enrollment Issues

Although the process is straightforward, when implementing **Intune enrollment**, you may occasionally encounter issues. This section provides solutions for common problems.

### Enrollment Failures

Below are common enrollment failures and their solutions:

| Issue | Cause | Solution |
| --- | --- | --- |
| “Unable to enroll” | Network connectivity | Check firewall allows Microsoft endpoints |
| “License not found” | Missing Intune license | Assign license in Entra admin center |
| App crashes on launch | Missing dependencies | Reinstall with `sudo apt install --reinstall intune-portal` |
| Browser redirect fails | Edge not default | Set Edge as default browser |
| “Platform not supported” | Wrong Ubuntu version | Verify Ubuntu 22.04 or 24.04 LTS |

### Compliance Issues

Similarly, here are typical compliance issues you might encounter:

| Issue | Cause | Solution |
| --- | --- | --- |
| “Encryption required” | Disk not encrypted | Enable LUKS encryption or adjust policy |
| “OS version too old” | Outdated Ubuntu | Update to supported version |
| “Password policy” | Weak password | Update password to meet requirements |
| Status stuck on “Evaluating” | Sync delay | Wait or force sync via Intune Portal |

### Common Commands for Troubleshooting

When diagnosing issues, these commands are particularly useful:

```
# Check Intune Portal version
dpkg -l | grep intune-portal

# View Intune Portal logs
journalctl -u intune-portal

# Force re-enrollment (remove and re-enroll)
intune-portal --unenroll
intune-portal

# Check network connectivity to Microsoft
curl -I https://login.microsoftonline.com
curl -I https://manage.microsoft.com

# Reinstall Intune Portal
sudo apt install --reinstall intune-portal
```

### Setting Microsoft Edge as Default Browser

In particular, if browser redirects fail during enrollment, try these commands:

```
# Set Microsoft Edge as default browser
xdg-settings set default-web-browser microsoft-edge.desktop

# Verify default browser
xdg-settings get default-web-browser
```

---

## Best Practices for Intune Enrollment

Now that you understand the technical implementation, follow these best practices to ensure your **Intune enrollment** deployment is successful and maintainable.

### Deployment Recommendations

For a smooth rollout, consider these deployment practices:

| Practice | Description |
| --- | --- |
| **Staged rollout** | Start with IT team, then early adopters, then full deployment |
| **Document the process** | Create user-facing documentation with screenshots |
| **Pre-enrollment checklist** | Verify prerequisites before starting enrollment |
| **Test compliance policies** | Validate policies don’t block legitimate use cases |
| **Plan for updates** | Schedule regular package updates for security |

### Security Recommendations

Equally important, implement these security measures:

| Practice | Description |
| --- | --- |
| **Enable disk encryption** | Use LUKS during Ubuntu installation |
| **Configure automatic updates** | Enable unattended-upgrades for security patches |
| **Implement Conditional Access** | Require compliant devices for sensitive apps |
| **Regular compliance reviews** | Check device compliance weekly |
| **Monitor enrollment status** | Set up alerts for failed enrollments |

### Operational Best Practices

In terms of day-to-day operations, focus on these areas:

1. **User Communication**
   * Provide clear enrollment instructions
   * Additionally, explain what compliance requirements mean
   * Furthermore, establish support channels for issues
2. **Inventory Management**
   * Use Intune device groups for organization
   * Also, tag devices by department or location
   * Moreover, review device inventory monthly
3. **Policy Management**
   * Start with minimal compliance requirements
   * Subsequently, gradually increase requirements as users adapt
   * Above all, test policy changes before deployment

### Monitoring Commands

For ongoing monitoring, use these commands regularly:

```
# Check Intune enrollment status
intune-portal --status

# View device compliance details
intune-portal --compliance

# Check for available updates
sudo apt update
apt list --upgradable
```

---

## Conclusion: Embracing Intune Enrollment

Implementing **Intune enrollment** brings Linux workstations into your unified device management strategy. As a result, organizations achieve the following benefits:

* First, **consistent management** across all device platforms
* Second, **enhanced security** through compliance enforcement
* Third, **visibility** into device inventory and status
* Additionally, **Conditional Access** integration for resource protection
* Finally, **simplified IT operations** with centralized management

Overall, this **Intune enrollment** solution represents a significant step forward for organizations using Linux alongside Windows and macOS. With Microsoft continuing to invest in Linux support, you can expect additional capabilities and deeper integration in future releases.

**Ready to implement Intune enrollment?** To get started, use the automation script provided, enroll a test device, validate your compliance policies, and then scale your deployment with confidence.

---

## Additional Resources

### External Documentation

For further reading, consult these official resources:

* First, [Microsoft Intune Linux Enrollment](https://learn.microsoft.com/en-us/intune/intune-service/user-help/enroll-device-linux)
* Second, [Intune Compliance Policies for Linux](https://learn.microsoft.com/en-us/intune/intune-service/protect/compliance-policy-create-linux)
* Third, [Microsoft Entra ID Documentation](https://learn.microsoft.com/en-us/entra/)
* Lastly, [Ubuntu Enterprise Desktop](https://ubuntu.com/desktop/organisations)

### Related Articles

In addition, you may find these related articles helpful:

* [Entra ID Authentication with AuthD on Ubuntu 24.04 LTS](https://jensdufour.be/2026/02/04/entra-id-authentication-with-authd/) – Enable cloud identity login on Ubuntu using AuthD
* [Automating Ubuntu Entra ID Authentication](https://jensdufour.be/2026/01/02/zero-touch-ubuntu-entra-id-autoinstall/) – Zero-touch deployment with autoinstall and cloud-init

---

*Have questions about implementing **Intune enrollment**? Share your experience in the comments below or reach out for assistance!*