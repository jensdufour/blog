---
title: 'Managing Windows 365 Cloud Apps with Nerdio Manager for Enterprise'
date: '2026-05-01'
status: draft
seo_title: 'Windows 365 Cloud Apps with Nerdio: Setup and Management'
meta_description: 'Manage Windows 365 Frontline Cloud Apps through Nerdio Manager for Enterprise. Stream individual apps from shared Cloud PCs without provisioning a full desktop per user.'
focus_keyphrase: 'Windows 365 Cloud Apps Nerdio'
categories:
- Microsoft
- Technology
tags:
- Nerdio
- NME
- Windows 365
- Windows 365 Frontline
- Cloud Apps
- Intune
- Automation
---

## Introduction

[Windows 365 Cloud Apps](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps) let users stream individual applications from a shared Cloud PC without opening a full desktop session. Instead of provisioning a dedicated Cloud PC per user, administrators publish specific applications that users launch directly from the [Windows App](https://learn.microsoft.com/en-us/windows-app/overview), as if they were installed locally. The compute runs on a non-persistent Frontline Cloud PC in Shared mode in the background.

This is useful when users only need a handful of specific applications and do not require a full, persistent desktop. Think of a customer-facing worker who needs access to a single line-of-business app for short sessions, or an external contractor who only needs one tool to complete a task.

[Nerdio Manager for Enterprise](https://getnerdio.com/) (NME) adds a management layer on top of this. Through NME, administrators can configure, deploy, and monitor Cloud Apps alongside their existing Windows 365 environment.

In this post we will walk through **what Cloud Apps are**, how they differ from a full Cloud PC desktop experience, and how to **manage them through NME**.

> **Important:** Windows 365 Cloud Apps require **Windows 365 Frontline** licenses and run on Frontline Cloud PCs in **Shared mode** (non-persistent, multi-user). They are *not* delivered from a user's dedicated Windows 365 Enterprise Cloud PC.

> **Note:** Windows 365 Cloud Apps support in Nerdio Manager is currently in **Public Preview** (per Nerdio's [Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339564063373-Windows-365-Cloud-Apps) KB article). Feature scope and UI may evolve in upcoming releases.

## What Are Windows 365 Cloud Apps?

Windows 365 Cloud Apps deliver individual applications from a shared Cloud PC to the user's local device through the [Windows App](https://learn.microsoft.com/en-us/windows-app/overview). Rather than streaming the entire desktop, only the application window is rendered remotely and displayed locally.

Key characteristics:

| Aspect | Detail |
|---|---|
| **Delivery method** | App streaming via Windows App |
| **User experience** | App appears as a local window, no full desktop session required |
| **Backend** | Runs on a [Windows 365 Frontline Cloud PC in Shared mode](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline#windows-365-frontline-in-shared-mode) (non-persistent) |
| **Data persistence** | User data is deleted after each session. Optional [User Experience Sync (UES)](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline) persists app data and Windows settings to the cloud |
| **Concurrency** | Max active sessions per provisioning policy = number of Frontline licenses assigned to that policy |
| **Management** | Configurable through Microsoft Intune and Nerdio Manager |
| **Requirements** | [Windows 365 Frontline license](https://learn.microsoft.com/en-us/windows-365/enterprise/frontline-license), Windows App on the local device |

From the user's perspective, a Cloud App appears in the [Windows App](https://learn.microsoft.com/en-us/windows-365/end-user-access-cloud-pc) as a standalone connection — Nerdio's documentation describes it as "similar to AVD instances." Behind the scenes, each session runs on a fresh, non-persistent Cloud PC drawn from a shared pool, and the Cloud PC is reset for the next user when the current user signs out. Published apps can also launch *other* apps installed on the Cloud PC (for example, Outlook opening links in Edge), so use [Application Control for Windows](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/appcontrol) if you need to restrict which apps can run.

## Prerequisites

Before configuring Cloud Apps through NME, ensure you have the following in place. Items marked ✨ come from Nerdio's [Manage and publish Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339575273997-Manage-and-publish-Windows-365-Cloud-Apps) KB article.

| Requirement | Detail |
|---|---|
| **NME subscription** | AVD Core, AVD Premium, Windows 365, or Unified Endpoint Management plan, with Windows 365 management enabled ✨ |
| **Windows 365 Frontline licenses** | Enough Frontline licenses to cover concurrent users — if concurrent connections exceed available licenses, additional users are denied access until a session frees up ✨ |
| **Supported region** | Frontline Shared mode requires a single specific Azure region (multi-region selection is not supported for this SKU) and is currently Azure Global Cloud only — see [supported regions](https://learn.microsoft.com/en-us/windows-365/enterprise/requirements?tabs=enterprise%2Cent#supported-azure-regions-for-cloud-pc-provisioning) |
| **Image with target apps** | At least one Windows 365 image (Managed Image, Microsoft Gallery Image, or custom image uploaded to Endpoint Manager) containing the apps you want to publish ✨ |
| **Windows App** | Installed on the user's local device |
| **Intune integration** | Intune and Windows 365 management enabled in NME (Windows 365 set to **Manage** under *Configurable Features* or *Delegated User Features* — see [Enable and configure Intune](https://nmehelp.getnerdio.com/hc/en-us/articles/25499415681933-Enable-and-configure-Intune)) ✨ |
| **NME role** | Built-in **Admin** role, or a custom role with **Full access** to **Intune > Windows 365** ✨ |
| **App service Graph permissions** | `CloudPC.Read.All`, `DeviceManagementScripts.Read.All`, `DeviceManagementManagedDevices.Read.All` — already granted if NME is managing Windows 365 ✨ |

<!-- TODO: Add screenshot - NME Cloud Apps prerequisites -->

## How Cloud Apps Differ from a Full Cloud PC

Cloud Apps and a full Windows 365 Enterprise Cloud PC are different products targeting different scenarios. They use different licenses and have different persistence models.

| Scenario | Windows 365 Enterprise (full desktop) | Windows 365 Frontline Cloud Apps |
|---|---|---|
| **License** | Windows 365 Enterprise | Windows 365 Frontline |
| **Cloud PC mode** | Dedicated, persistent, 1:1 | Shared, non-persistent, pooled |
| **User data** | Persists between sessions | Wiped after sign-out (UES can persist settings only) |
| **Concurrency model** | One Cloud PC per assigned user | Active sessions limited by Frontline licenses on the policy |
| **Best for** | Knowledge workers needing a full, always-available workstation | Customer-facing staff, external contractors, short-task workers |
| **Provisioning experience** | "Windows desktop" | "Access only apps" |

Cloud Apps are not a replacement for a full Cloud PC, and they are not a feature you bolt on top of an existing Enterprise Cloud PC. They are a separate, lighter delivery model for organizations that want to give users access to specific applications without provisioning (and licensing) a dedicated Cloud PC per user.

A simple sizing rule: **the maximum number of concurrent Cloud App sessions for a provisioning policy equals the number of Frontline licenses you assign to that policy.** For example, 10 Frontline licenses on a policy = up to 10 concurrent app sessions; users beyond that are queued (denied with an error message) until a session frees up. There is no concurrency buffer in Shared mode.

## Configuring Cloud Apps in NME

### Step 1: Prepare the Image

Cloud Apps are discovered by scanning the Start Menu on the underlying Cloud PC image, so the apps you want to publish must already be installed on the image you select in the provisioning policy. NME accepts three image sources:

* A **Managed Image** created in NME under *Windows 365 > Desktop Images*.
* A **Microsoft Gallery Image**.
* Any **custom image** uploaded to Endpoint Manager directly.

If you use a custom image, ensure it is a [supported image](https://learn.microsoft.com/en-us/windows-365/enterprise/add-device-images) and that no tenant security policy blocks the PowerShell script Windows 365 uses to scan the Start Menu — otherwise app discovery will fail. Note also that APPX/MSIX apps are not shown in the in-policy image preview; they appear in the Cloud Apps list after provisioning, and adding APPX/MSIX support to an existing policy requires reprovisioning.

<!-- TODO: Add screenshot - Image selection in NME -->

### Step 2: Create a Cloud Apps Provisioning Policy

In NME, Cloud Apps use a dedicated provisioning policy with the **Cloud App** experience type (this is what Microsoft Intune calls *"Access only apps"*). Per Nerdio's KB:

1. Navigate to **Endpoints > Windows 365 > Provisioning Policies**.
2. Select **+ New policy**.
3. Enter a **name** and **description**.
4. In the **License type** dropdown, select **Frontline**.
5. In the dropdown directly below, select **Shared Mode**.
6. In the **Experience** dropdown, select **Cloud App**.
7. In the **Cloud PC image** dropdown, select your prepared image (Managed Image, Microsoft Gallery Image, or custom).
8. Select the **language**, **region**, and **network connection** to use. (Frontline Shared mode requires a single specific region.)
9. Under **Manual Entra ID group assignments**, for each Entra ID group:
   * Pick the **Group**.
   * Choose the **Cloud PC size**.
   * Type an **assignment name**.
   * Enter the **number of Cloud PCs** to assign to the policy (this number drives concurrent session capacity for the group).
   * Select **Assign**.
10. Select **Save**.

After saving, the policy is applied to your Azure tenant and Frontline Cloud PCs in Shared mode begin provisioning. Nerdio explicitly notes that the available Cloud Apps list "will populate after a short interval" — if it is empty immediately after creating the policy, that is normal, not a misconfiguration.

Optionally, on the configuration step you can attach an [Autopilot Device Preparation policy](https://learn.microsoft.com/en-us/windows-365/enterprise/autopilot-device-preparation) (still in **public preview** for Cloud Apps as of April 2026) and enable **User Experience Sync** to persist app settings between sessions. If you use Autopilot Device Preparation, also check **"Prevent users from connecting to Cloud PC upon installation failure or timeout"** so that Intune apps reliably appear in the Cloud Apps list.

<!-- TODO: Add screenshot - Cloud Apps provisioning policy in NME -->

### Step 3: Publish Apps

Once the first Cloud PC has provisioned, discovered apps appear under **Endpoints > Windows 365 > Cloud Apps** with status **Ready**.

1. Navigate to **Endpoints > Windows 365 > Cloud Apps**.
2. Locate the app(s) showing **Ready** in the Status column.
3. Click the **publish** icon, or open the row's context menu and select **Publish**. Status moves through *Publishing* → *Published*.
4. If a previously published app shows an error, open the context menu and select **Reset & Publish** to retry.
5. To remove an app from the Windows App feed, click the **unpublish** icon (or context menu → **Unpublish**); status returns to *Ready*.

Individual Cloud App details — display name, description, command line, icon path, icon index — can be edited per app. Scope tags and assignments are inherited from the provisioning policy and cannot be overridden per app. Edits are pushed immediately to the Windows App feed.

To delete Cloud Apps entirely, delete the Cloud App provisioning policy assignment or the assigned Entra ID group — there is no per-app delete.

<!-- TODO: Add screenshot - Cloud Apps publishing in NME -->

### Step 4: Validate from the End-User Device

1. On a test user's local device, sign in to the **Windows App** with a user that has a Frontline license and is in the assigned group.
2. Verify the published Cloud Apps appear in the app feed (they show as standalone connections, similar to AVD).
3. Launch a Cloud App and confirm it streams correctly from a shared Cloud PC.
4. Sign out and confirm a fresh session starts on next launch (data is wiped unless UES is enabled).

<!-- TODO: Add screenshot - Cloud App running on local device -->

## Troubleshooting

The most common issues, sourced from Microsoft's [Cloud Apps troubleshooting guidance](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps#troubleshooting):

| Symptom | What to check |
|---|---|
| Cloud PCs fail to provision | [Troubleshoot provisioning errors](https://learn.microsoft.com/en-us/troubleshoot/windows-365/provisioning-errors) |
| Autopilot Device Preparation fails to install apps | [Autopilot device preparation monitoring](https://learn.microsoft.com/en-us/autopilot/device-preparation/tutorial/automatic/automatic-monitor) and [known issues](https://learn.microsoft.com/en-us/autopilot/device-preparation/known-issues) |
| Cloud PC provisions and Autopilot succeeds, but Intune apps don't appear in Cloud Apps | Confirm **"Prevent users from connecting to Cloud PC upon installation failure or timeout"** is enabled on the provisioning policy |
| Cloud App stuck in **Preparing** | Bulk reprovision the policy; if that fails, delete and re-create the Cloud App policy assignment |
| Custom image apps not discovered | Verify the image is [supported](https://learn.microsoft.com/en-us/windows-365/enterprise/add-device-images) and that tenant security policies do not block the PowerShell discovery script |
| User denied access with a licensing error | Concurrent sessions exceed the Frontline licenses assigned to the policy — wait for a session to free up or add licenses |
| Cloud App shows **Failed** in NME | Open the context menu and select **Reset & Publish** |

## Monitoring Cloud Apps

Cloud App sessions are subject to the same management and monitoring as any Frontline Shared Cloud PC. The primary place to watch concurrency is Microsoft's [Connected Frontline Cloud PCs report](https://learn.microsoft.com/en-us/windows-365/enterprise/report-connected-frontline-cloud-pcs); RDP redirections and idle-timeout settings applied to the underlying Frontline Cloud PCs also apply to Cloud Apps (see [redirections](https://learn.microsoft.com/en-us/windows-365/enterprise/manage-rdp-device-redirections) and [session time limits](https://learn.microsoft.com/en-us/windows-365/enterprise/frontline-cloud-pc-session-time-limits)).

Key metrics to track:

| Metric | Why It Matters |
|---|---|
| **App launch success rate** | Identifies configuration, image, or app discovery issues |
| **Session latency** | Affects user experience for interactive apps |
| **Concurrent sessions vs. licenses** | Frontline Shared has no concurrency buffer — once licenses are saturated, new users cannot connect |
| **User adoption** | Tracks rollout progress |

<!-- TODO: Add a screenshot of the Connected Frontline Cloud PCs report in Intune and the matching NME monitoring view. -->

## Current Limitations

As with any new feature, there are boundaries to be aware of:

| Limitation | Detail |
|---|---|
| **Preview status (NME)** | Cloud Apps support in Nerdio Manager is in **Public Preview** at time of writing |
| **Preview status (Microsoft)** | Autopilot Device Preparation support for Cloud Apps and the [RemoteApp UX enhancements](https://learn.microsoft.com/en-us/azure/virtual-desktop/remoteapp-enhancements) are in public preview |
| **License type** | Requires Windows 365 Frontline; Enterprise licenses cannot be used for Cloud Apps |
| **Region availability** | Frontline Shared mode requires a single specific Azure region (no multi-region selection) and is not available for [Windows 365 Government](https://learn.microsoft.com/en-us/windows-365/public-preview) |
| **Persistence** | Sessions are non-persistent; UES is required to retain user settings between sessions |
| **No concurrency buffer** | Unlike Frontline dedicated mode, Shared mode has no overflow capacity |
| **App discovery** | Apps must be installed on the image and discoverable from the Start Menu via PowerShell; APPX/MSIX support requires reprovisioning |
| **App compatibility** | Not all applications work well in streamed RemoteApp mode |
| **Platform support** | Windows App required on the local device |
| **Network dependency** | Performance depends on connection quality between local device and Cloud PC |

## Conclusion

Windows 365 Cloud Apps deliver individual applications from non-persistent, shared Frontline Cloud PCs — without giving each user a dedicated desktop. For scenarios where users only need specific tools (customer-facing staff, contractors, task workers), Cloud Apps cost less and deploy faster than a full Cloud PC per user.

Nerdio Manager for Enterprise wraps the Intune *Access only apps* provisioning flow into a single, opinionated UI under **Endpoints > Windows 365**, so the same admin who manages your Cloud PCs can stand up a Cloud Apps policy, publish apps, and re-publish failed ones without leaving NME. The feature is in Public Preview today; expect refinements as it moves to GA.

## References

* [Windows 365 Cloud Apps](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps) — Microsoft documentation
* [What is Windows 365 Frontline?](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline) — Dedicated and Shared mode overview
* [Windows 365 Frontline licensing](https://learn.microsoft.com/en-us/windows-365/enterprise/frontline-license) — License requirements for Cloud Apps
* [Connected Frontline Cloud PCs report](https://learn.microsoft.com/en-us/windows-365/enterprise/report-connected-frontline-cloud-pcs) — Concurrency monitoring
* [Windows App](https://learn.microsoft.com/en-us/windows-app/overview) — Client application for accessing Cloud PCs and Cloud Apps
* [Nerdio: Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339564063373-Windows-365-Cloud-Apps) — NME feature overview, RBAC, and required Graph permissions
* [Nerdio: Manage and publish Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339575273997-Manage-and-publish-Windows-365-Cloud-Apps) — Step-by-step provisioning and publishing
* [Automating New Device Setup with Nerdio Scripted Sequences](https://jensdufour.be/2026/04/01/automating-new-device-setup-with-nerdio-scripted-sequences/) — Related NME walkthrough
