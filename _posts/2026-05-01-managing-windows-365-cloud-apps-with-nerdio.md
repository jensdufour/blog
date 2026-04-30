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

[Windows 365 Cloud Apps](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps) let users stream individual applications from a [Windows 365 Frontline Cloud PC in Shared mode](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline#windows-365-frontline-in-shared-mode) without ever opening a full desktop session. Instead of giving every user their own Cloud PC, you publish specific applications that users launch from the [Windows App](https://learn.microsoft.com/en-us/windows-app/overview) as if they were installed locally. The compute runs on a Frontline Shared Cloud PC in the background.

This is useful when users only need a handful of specific applications. Think of a customer-facing worker who needs access to a single line-of-business app for short sessions, or an external contractor who only needs one tool to complete a task.

[Nerdio Manager for Enterprise](https://getnerdio.com/) (NME) adds a management layer on top of this, so the same admin who provisions your Cloud PCs can stand up Cloud Apps from the same UI. In this post we will walk through what Cloud Apps are, how they differ from a full Cloud PC desktop experience, and how to manage them through NME.

> **Important:** Cloud Apps are a Frontline Shared mode feature. They require Windows 365 Frontline licenses, and they are not delivered from a user's dedicated Windows 365 Enterprise Cloud PC.

> **Note:** Windows 365 Cloud Apps support in Nerdio Manager is currently in Public Preview (per Nerdio's [Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339564063373-Windows-365-Cloud-Apps) KB article). Feature scope and UI may evolve in upcoming releases.

## What Are Windows 365 Cloud Apps?

A Cloud App is an individual application delivered from a Frontline Shared Cloud PC to the user's local device through the [Windows App](https://learn.microsoft.com/en-us/windows-app/overview) client. Only the application window is rendered remotely and displayed locally, not the full desktop. To the end user, a Cloud App appears in the Windows App as a standalone connection (Nerdio's documentation describes it as similar to AVD instances), so it does not require any familiarity with a remote desktop session.

Because Frontline Shared mode is non-persistent, every session starts on a fresh Cloud PC drawn from a shared pool. When the user signs out, the Cloud PC is reset for the next user, and any data left behind is wiped. If you need user-specific app data and Windows settings to survive between sessions, enable [User Experience Sync (UES)](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline) on the provisioning policy. UES persists settings to the cloud, but it does not turn the Cloud PC into a persistent machine.

One subtlety worth flagging: a published Cloud App can launch other apps that happen to be installed on the same Cloud PC. The classic example is Microsoft Outlook opening links in Microsoft Edge even if Edge is not itself published. If you need to keep users strictly to the published app surface, use [Application Control for Windows](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/appcontrol) inside the image.

The licensing model is simple: the maximum number of concurrent Cloud App sessions for a provisioning policy equals the number of Frontline licenses you assign to that policy. Ten Frontline licenses on a policy means up to ten concurrent app sessions. Users who try to connect beyond that limit are denied with an error message until a session frees up. Frontline Shared mode has no concurrency buffer, unlike Frontline dedicated mode.

## Prerequisites

This post assumes NME is already managing your Windows 365 estate, so the heavy lifting (Intune integration enabled, Windows 365 set to **Manage** in NME, the app service Graph permissions `CloudPC.Read.All`, `DeviceManagementScripts.Read.All`, and `DeviceManagementManagedDevices.Read.All` already consented) is done.

What is specific to Cloud Apps:

* **Windows 365 Frontline licenses**, enough to cover concurrent users. Frontline licenses are separate from Windows 365 Enterprise licenses, and Enterprise licenses cannot be used here.
* **A supported region**. Frontline Shared mode requires a single specific Azure region (multi-region selection is not supported for this SKU). Check the current list under [supported Azure regions](https://learn.microsoft.com/en-us/windows-365/enterprise/requirements?tabs=enterprise%2Cent#supported-azure-regions-for-cloud-pc-provisioning).
* **An image containing the apps you want to publish**. NME accepts a Managed Image (created in NME under *Windows 365 > Desktop Images*), a Microsoft Gallery Image, or any custom image uploaded to Endpoint Manager directly.
* **Windows App** installed on the user's local device.
* **NME role** with at least **Full access** to the **Intune > Windows 365** module. The built-in **Admin** role works; otherwise create a custom role.

<!-- TODO: Add screenshot - NME Cloud Apps prerequisites -->

## How Cloud Apps Differ from a Full Cloud PC

Cloud Apps and a full Windows 365 Enterprise Cloud PC are different products targeting different scenarios, with different licenses and different persistence models. The comparison below is the one place a table genuinely helps, because it is an apples-to-apples reference.

| | Windows 365 Enterprise (full desktop) | Windows 365 Frontline Cloud Apps |
|---|---|---|
| **License** | Windows 365 Enterprise | Windows 365 Frontline |
| **Cloud PC mode** | Dedicated, persistent, 1:1 | Shared, non-persistent, pooled |
| **User data** | Persists between sessions | Wiped after sign-out (UES persists settings only) |
| **Concurrency** | One Cloud PC per assigned user | Active sessions limited by Frontline licenses on the policy |
| **Best for** | Knowledge workers needing a full, always-available workstation | Customer-facing staff, contractors, short-task workers |
| **Provisioning experience** | "Windows desktop" | "Access only apps" (Intune) / "Cloud App" (NME) |

Cloud Apps are not a replacement for a full Cloud PC, and they are not something you bolt on top of an existing Enterprise Cloud PC. They are a separate, lighter delivery model for organizations that want to give users access to specific applications without provisioning, and licensing, a dedicated Cloud PC per user.

## Configuring Cloud Apps in NME

### Step 1: Prepare the image

Cloud Apps are discovered by scanning the Start Menu on the underlying Cloud PC image, so the apps you want to publish must already be installed on the image you select in the provisioning policy.

If you go with a custom image, make sure it is a [supported image](https://learn.microsoft.com/en-us/windows-365/enterprise/add-device-images) and that no tenant security policy blocks the PowerShell script Windows 365 uses to scan the Start Menu. Otherwise app discovery will silently fail. APPX and MSIX apps have an extra wrinkle: they are not shown in the in-policy image preview during policy creation. They appear in the Cloud Apps list after provisioning, and adding APPX/MSIX support to an existing policy requires reprovisioning.

<!-- TODO: Add screenshot - Image selection in NME -->

### Step 2: Create a Cloud Apps provisioning policy

In NME, Cloud Apps use a dedicated provisioning policy with the **Cloud App** experience type, which is what Microsoft Intune calls "Access only apps".

1. Navigate to **Endpoints > Windows 365 > Provisioning Policies** and select **+ New policy**.
2. Enter a name and description.
3. In the **License type** dropdown, select **Frontline**, and in the dropdown directly below, select **Shared Mode**.
4. In the **Experience** dropdown, select **Cloud App**.
5. In the **Cloud PC image** dropdown, select your prepared image.
6. Pick the language, region, and network connection. Frontline Shared mode requires a single specific region, so this choice matters.
7. Under **Manual Entra ID group assignments**, for each Entra ID group select the group, choose a Cloud PC size, name the assignment, and enter the number of Cloud PCs to assign. That number drives concurrent session capacity for the group.
8. Select **Save**.

After saving, the policy is applied to your Azure tenant and Frontline Cloud PCs in Shared mode begin provisioning. Nerdio explicitly notes that the available Cloud Apps list "will populate after a short interval", so an empty list immediately after creating the policy is normal, not a misconfiguration.

Two configuration toggles are worth knowing about. You can attach an [Autopilot Device Preparation policy](https://learn.microsoft.com/en-us/windows-365/enterprise/autopilot-device-preparation), which is still in public preview for Cloud Apps as of April 2026. If you do, also enable **"Prevent users from connecting to Cloud PC upon installation failure or timeout"** so that Intune apps reliably appear in the Cloud Apps list. The second toggle is **User Experience Sync**, which persists app settings between sessions and is the only way to give Frontline Shared users any sense of continuity across logins.

<!-- TODO: Add screenshot - Cloud Apps provisioning policy in NME -->

### Step 3: Publish apps

Once the first Cloud PC has provisioned, discovered apps appear under **Endpoints > Windows 365 > Cloud Apps** with status **Ready**. Click the publish icon, or open the row's context menu and select **Publish**, to push an app to the Windows App feed. The status moves through *Publishing* to *Published*. If a previously published app shows an error, the **Reset & Publish** option in the context menu retries the operation. To remove an app from the Windows App feed, use the unpublish icon or context menu option, which returns the app to *Ready*.

You can edit a Cloud App's display name, description, command line, icon path, and icon index per app, and edits are pushed to the Windows App feed immediately. Scope tags and assignments are inherited from the provisioning policy, so they cannot be overridden per app. There is also no per-app delete: to remove Cloud Apps entirely, delete the Cloud App provisioning policy assignment or the assigned Entra ID group.

<!-- TODO: Add screenshot - Cloud Apps publishing in NME -->

### Step 4: Validate from the end-user device

Sign in to the Windows App on a test user's local device with a user that has a Frontline license and is in the assigned group. The published Cloud Apps should appear in the app feed as standalone connections. Launch one and confirm it streams from a shared Cloud PC. Sign out and re-launch to confirm a fresh session starts each time. Without UES enabled, anything left behind in the previous session is gone.

<!-- TODO: Add screenshot - Cloud App running on local device -->

## Troubleshooting

The most common Cloud Apps issues, drawn from Microsoft's [Cloud Apps troubleshooting guidance](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps#troubleshooting):

If Cloud PCs fail to provision in the first place, work through [Troubleshoot provisioning errors](https://learn.microsoft.com/en-us/troubleshoot/windows-365/provisioning-errors) before looking at Cloud Apps specifically. If Cloud PCs provision but Autopilot Device Preparation fails to install applications, check [Autopilot device preparation monitoring](https://learn.microsoft.com/en-us/autopilot/device-preparation/tutorial/automatic/automatic-monitor) and [known issues](https://learn.microsoft.com/en-us/autopilot/device-preparation/known-issues).

A more subtle case: Cloud PCs provision successfully, Autopilot Device Preparation succeeds, but Intune apps simply do not appear in the Cloud Apps list. The fix is to confirm that **"Prevent users from connecting to Cloud PC upon installation failure or timeout"** is enabled on the provisioning policy. Without it, Cloud PCs can be released to users before app installation finishes, and the Start Menu scan misses them.

If Cloud Apps stay stuck in *Preparing*, bulk reprovision the policy. If that does not unblock them, delete and recreate the Cloud App policy assignment. If apps from a custom image are not discovered at all, the image is either unsupported or the Start Menu PowerShell discovery script is being blocked by tenant security policy. If a user is denied access with a licensing error, concurrent sessions have exceeded the Frontline licenses assigned to the policy, so wait for a session to free up or add licenses. Finally, if a Cloud App shows *Failed* in NME, **Reset & Publish** from the context menu is the first thing to try.

## Monitoring Cloud Apps

Cloud App sessions are subject to the same management and monitoring as any Frontline Shared Cloud PC. The primary place to watch concurrency is Microsoft's [Connected Frontline Cloud PCs report](https://learn.microsoft.com/en-us/windows-365/enterprise/report-connected-frontline-cloud-pcs). RDP redirections and idle-timeout settings applied to the underlying Frontline Cloud PCs also apply to Cloud Apps (see [redirections](https://learn.microsoft.com/en-us/windows-365/enterprise/manage-rdp-device-redirections) and [session time limits](https://learn.microsoft.com/en-us/windows-365/enterprise/frontline-cloud-pc-session-time-limits)).

The metrics most worth watching are the app launch success rate, which tends to surface configuration, image, or app-discovery issues; session latency, which directly affects how usable interactive apps feel; and the ratio of concurrent sessions to assigned Frontline licenses. Frontline Shared has no concurrency buffer, so once licenses are saturated new users simply cannot connect. Tracking adoption alongside these tells you whether the rollout is actually landing with users.

<!-- TODO: Add a screenshot of the Connected Frontline Cloud PCs report in Intune and the matching NME monitoring view. -->

## Current Limitations

Cloud Apps support is in Public Preview in Nerdio Manager today, and a few of the underlying Microsoft features (Autopilot Device Preparation for Cloud Apps, the [RemoteApp UX enhancements](https://learn.microsoft.com/en-us/azure/virtual-desktop/remoteapp-enhancements)) are themselves in public preview. Expect changes as these move to GA.

The license boundary is hard: Cloud Apps need Windows 365 Frontline, and Enterprise licenses cannot be used. The region boundary is similarly hard: Frontline Shared mode requires a single specific Azure region, multi-region selection is not available for this SKU, and preview features are not available for [Windows 365 Government](https://learn.microsoft.com/en-us/windows-365/public-preview).

On the runtime side, sessions are non-persistent and UES is the only mechanism to retain user settings between sessions. There is no concurrency buffer in Shared mode, so capacity planning has to be exact. App discovery only finds apps that are present on the image and reachable from the Start Menu via PowerShell, and APPX/MSIX support requires reprovisioning. Not every application behaves well in streamed RemoteApp mode either, so plan a real validation pass before pushing line-of-business apps to users.

End users always need the Windows App on their local device, and the streaming experience depends on the network quality between that device and the Cloud PC.

## Conclusion

Windows 365 Cloud Apps deliver individual applications from non-persistent Frontline Shared Cloud PCs without giving each user a dedicated desktop. For scenarios where users only need specific tools (customer-facing staff, contractors, task workers), Cloud Apps cost less and deploy faster than a full Cloud PC per user.

Nerdio Manager for Enterprise wraps the Intune *Access only apps* provisioning flow into a single UI under **Endpoints > Windows 365**, so the admin who already manages your Cloud PCs can stand up a Cloud Apps policy, publish apps, and republish failed ones without leaving NME. The feature is in Public Preview today, so expect refinements as it moves to GA.

## References

* [Windows 365 Cloud Apps](https://learn.microsoft.com/en-us/windows-365/enterprise/cloud-apps), Microsoft documentation
* [What is Windows 365 Frontline?](https://learn.microsoft.com/en-us/windows-365/enterprise/introduction-windows-365-frontline), dedicated and Shared mode overview
* [Windows 365 Frontline licensing](https://learn.microsoft.com/en-us/windows-365/enterprise/frontline-license), license requirements for Cloud Apps
* [Connected Frontline Cloud PCs report](https://learn.microsoft.com/en-us/windows-365/enterprise/report-connected-frontline-cloud-pcs), concurrency monitoring
* [Windows App](https://learn.microsoft.com/en-us/windows-app/overview), client application for accessing Cloud PCs and Cloud Apps
* [Nerdio: Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339564063373-Windows-365-Cloud-Apps), NME feature overview, RBAC, and required Graph permissions
* [Nerdio: Manage and publish Windows 365 Cloud Apps](https://nmehelp.getnerdio.com/hc/en-us/articles/45339575273997-Manage-and-publish-Windows-365-Cloud-Apps), step-by-step provisioning and publishing
* [Automating New Device Setup with Nerdio Scripted Sequences](https://jensdufour.be/2026/04/01/automating-new-device-setup-with-nerdio-scripted-sequences/), related NME walkthrough
