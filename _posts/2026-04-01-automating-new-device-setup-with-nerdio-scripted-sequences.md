---
title: 'Automating New Device Setup with Nerdio Scripted Sequences'
date: '2026-04-01'
status: draft
seo_title: 'Nerdio Scripted Sequences: Automate Device Setup'
meta_description: 'Use Nerdio Scripted Sequences to automate multi-step device setup on Windows 365 and Intune devices. Includes a real-world developer onboarding demo.'
focus_keyphrase: 'Nerdio Scripted Sequences'
categories:
- Microsoft
- Technology
tags:
- Nerdio
- NME
- Scripted Sequences
- Windows 365
- Intune
- Automation
---

## Introduction

Setting up a new device for a developer usually means installing tools, cloning repositories, and applying configurations, all in a specific order. [Microsoft Intune](https://learn.microsoft.com/en-us/intune/intune-service/fundamentals/what-is-intune) handles app and script deployment well, but it does not guarantee execution order. A Git install that finishes after the script that clones your repos is a problem.

**Nerdio Scripted Sequences** solve this. Introduced in [Nerdio Manager for Enterprise](https://getnerdio.com/) (NME) v7.5.1 as a Public Preview, Scripted Sequences let you define complex, multi-step task workflows with a guaranteed order of operations. They target Intune-managed devices, including [Windows 365](https://learn.microsoft.com/en-us/windows-365/overview) Cloud PCs, and execute tasks sequentially through the Nerdio Endpoint Worker.

In this post we will build a real-world **developer workstation onboarding sequence** that installs Git, Visual Studio Code, clones team repositories, and confirms completion, all in the right order, every time.

> **Note:** Scripted Sequences are in Public Preview. Feature scope and limitations may change in future NME releases.

## What Are Scripted Sequences?

Scripted Sequences are an automation feature in NME that lets you create ordered, multi-step task workflows deployed to Intune-managed devices. Think of them as a lightweight task sequencer built into the Nerdio console.

Key characteristics:

| Aspect | Detail |
|---|---|
| **Introduced in** | NME v7.5.1 (December 2025) |
| **Current status** | Public Preview |
| **Supported targets** | Intune-managed devices, including Windows 365 Cloud PCs |
| **Execution engine** | Nerdio Endpoint Worker (deployed via Intune platform script) |
| **Concurrency limit** | 100 concurrent tasks per sequence |
| **Task types** | PowerShell scripts, Winget installs, and other Intune-deliverable actions |

Sequences respect the defined order of operations: Task 2 will not start until Task 1 completes successfully. Tasks can be grouped into **Task Groups** for logical organization, and since NME v7.6.0 you can **clone** sequences, groups, and individual tasks for faster iteration.

## Prerequisites

Before building your first sequence, make sure you have:

| Requirement | Detail |
|---|---|
| **NME version** | v7.6.0 or later recommended |
| **Intune integration** | Enabled in NME under **Settings > Integrations > Intune** |
| **Target device** | A Windows 365 Cloud PC or Intune-managed Windows device |
| **Nerdio Endpoint Worker** | Deployed to the target device (covered in Step 1) |
| **Permissions** | NME admin role with access to the Automation module |

## The Demo Scenario

We will automate day-one setup for a developer joining the team. The sequence installs prerequisites first, then tools, then runs a configuration script, in that exact order.

| Order | Task | Purpose |
|---|---|---|
| 1 | Set PowerShell Execution Policy | Allow scripts to run (RemoteSigned) |
| 2 | Install Git | Version control tooling |
| 3 | Install Visual Studio Code | Code editor |
| 4 | Clone repos and configure VS Code | Pull team repos and install extensions |
| 5 | Log completion | Confirm the sequence finished |

Let's build it.

## Step 1: Deploy the Nerdio Endpoint Worker

The Endpoint Worker is a lightweight agent that NME deploys via an Intune platform script. It handles task execution on the device.

1. Navigate to **NME** > **Settings** > **Integrations** > **Intune**.
2. Ensure the Intune integration is enabled and the Endpoint Worker deployment is active.
3. Verify that the target device shows the worker as installed under **Automation** > **Scripted Sequences** > **Endpoints**.

> **Note:** The initial Endpoint Worker deployment is controlled by Intune platform script delivery and may take some time. Subsequent tasks to the same device execute within a 15 to 30 minute window.

![Nerdio Endpoint Worker deployment status in the NME console.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-01.webp)

## Step 2: Create the Scripted Sequence

1. Navigate to **NME** > **Automation** > **Scripted Sequences**.
2. Click **Add sequence**.
3. Name the sequence `Developer Onboarding - Day One`.
4. Optionally add a description: *Installs developer tools and configures the workstation on first login.*

![Creating a new Scripted Sequence in the NME console.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-02.webp)

## Step 3: Add a Task Group

Task Groups let you organize related tasks. We will create one group for this sequence.

1. Inside the sequence, click **Add task group**.
2. Name the group `Developer Tooling`.

![Adding a Task Group to the sequence.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-03.webp)

## Step 4: Define the Tasks

Add the following five tasks inside the **Developer Tooling** group. The order you add them is the order they will execute.

### Task 1: Set PowerShell Execution Policy

This ensures all subsequent PowerShell-based tasks can run.

- **Task name:** `Set Execution Policy`
- **Type:** PowerShell script
- **Script:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
```

### Task 2: Install Git

- **Task name:** `Install Git`
- **Type:** PowerShell script
- **Script:**

```powershell
winget install --id Git.Git --accept-source-agreements --accept-package-agreements --silent
```

### Task 3: Install Visual Studio Code

- **Task name:** `Install VS Code`
- **Type:** PowerShell script
- **Script:**

```powershell
winget install --id Microsoft.VisualStudioCode --accept-source-agreements --accept-package-agreements --silent
```

### Task 4: Clone Repos and Configure VS Code

This script clones the team repository and installs essential VS Code extensions. Adjust the repository URL and extension list to match your environment.

- **Task name:** `Configure Workstation`
- **Type:** PowerShell script
- **Script:**

```powershell
# Refresh PATH so git and code are available
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Clone team repository
$repoPath = "$env:USERPROFILE\Source\Repos"
New-Item -ItemType Directory -Path $repoPath -Force | Out-Null
git clone https://dev.azure.com/contoso/project/_git/main-repo "$repoPath\main-repo"

# Install VS Code extensions
code --install-extension ms-vscode.powershell
code --install-extension ms-python.python
code --install-extension hashicorp.terraform
```

### Task 5: Log Completion

A simple confirmation entry in the Windows Event Log so you can validate remotely.

- **Task name:** `Log Completion`
- **Type:** PowerShell script
- **Script:**

```powershell
New-EventLog -LogName Application -Source "NerdioSequence" -ErrorAction SilentlyContinue
Write-EventLog -LogName Application -Source "NerdioSequence" -EventId 1000 -EntryType Information -Message "Developer onboarding sequence completed successfully."
```

![All five tasks configured inside the Developer Tooling task group.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-04.webp)

## Step 5: Clone Tasks for Quick Iteration

Need a second sequence for designers with different tools? Since NME v7.6.0, you can **clone** the entire sequence or individual task groups and tasks.

1. On the **Scripted Sequences** page, select the `Developer Onboarding - Day One` sequence.
2. Click **Clone**.
3. Rename the cloned sequence and swap Git/VS Code for the tools your designers need.

This saves significant time compared to rebuilding sequences from scratch.

## Step 6: Target Devices and Execute

1. Open the `Developer Onboarding - Day One` sequence.
2. Click **Run sequence**.
3. Select the target Windows 365 Cloud PC or Intune device.
4. Confirm execution.

NME will push the tasks to the Nerdio Endpoint Worker on the device. Each task runs in order. Task 2 only starts after Task 1 reports success.

![Targeting a Windows 365 Cloud PC for sequence execution.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-05.webp)

> **Tip:** Monitor progress in **NME** > **Logs**. Enhanced task logging in v7.6.0 provides better visibility into each step.

## Step 7: Validate on the Device

Log into the target Cloud PC and verify:

1. **Git** is installed. Open a terminal and run `git --version`.
2. **VS Code** is installed. Launch it from the Start menu.
3. **Repos** are cloned. Check `%USERPROFILE%\Source\Repos\main-repo`.
4. **Extensions** are present. Open VS Code and navigate to the Extensions panel.
5. **Event log** entry exists. Open Event Viewer > Application and look for Event ID 1000 from source `NerdioSequence`.

![Validation of the completed sequence on the Cloud PC.](../media/automating-new-device-setup-with-nerdio-scripted-sequences/automating-new-device-setup-with-nerdio-scripted-sequences-06.webp)

## Current Limitations

Scripted Sequences are still in Public Preview. Keep these constraints in mind:

| Limitation | Detail |
|---|---|
| **Concurrency** | Maximum 100 concurrent tasks per sequence |
| **Device scope** | Intune-managed devices only (AVD support planned for a future release) |
| **Targeting** | Manual device selection required; automated assignment to new devices is planned |
| **Initial deployment** | The Endpoint Worker relies on Intune platform script delivery, which can take time on first deploy |
| **Cross-tenant** | Running sequences against secondary tenant Windows 365 devices is not yet supported |

## Conclusion

**Nerdio Scripted Sequences** bring deterministic, ordered task execution to Intune-managed devices. This is something native Intune cannot guarantee today. By combining simple PowerShell scripts in a defined sequence, you can automate complex onboarding workflows and ensure every new device is configured consistently.

As the feature moves toward general availability, expect expanded scope including AVD session host support, automated targeting of new devices, and deeper integration with NME's Unified Application Management. For now, it is already a practical tool for any organization managing Windows 365 Cloud PCs or physical Intune endpoints at scale.
