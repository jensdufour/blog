---
categories:
- Microsoft
- Technology
date: '2025-12-12T13:28:42'
status: publish
tags:
- Adaptive Cards
- EPM
- Intune Suite
- Logic Apps
- Teams
title: 'EPM Approval Workflow: Adaptive Cards and Logic Apps'
seo_title: 'EPM Approval via Adaptive Cards in Teams'
meta_description: 'Automate EPM approval in Microsoft Teams with Adaptive Cards and Azure Logic Apps. Approve or deny elevation requests without leaving Teams.'
focus_keyphrase: 'EPM approval Adaptive Cards Teams'
---

## Introduction

**EPM automation with Adaptive Cards** transforms how IT teams handle elevation requests in [Microsoft Intune](https://learn.microsoft.com/en-us/intune/intune-service/fundamentals/what-is-intune). By combining [Azure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/) with Teams [Adaptive Cards](https://learn.microsoft.com/en-us/adaptive-cards/), you can automate the entire [Endpoint Privilege Management](https://learn.microsoft.com/en-us/intune/intune-service/protect/epm-overview) (EPM) approval workflow, allowing approvers to act on requests without leaving Microsoft Teams. This EPM automation solution eliminates the need to constantly monitor the Intune portal.

![EPM automation Adaptive Cards showing an approved elevation request in Microsoft Teams.](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-01.webp)

## What Is Endpoint Privilege Management?

**Endpoint Privilege Management (EPM)** is a feature in the [Microsoft Intune Suite](https://learn.microsoft.com/en-us/intune/intune-service/fundamentals/intune-add-ons) that allows organizations to manage and control local administrator rights on Windows devices --- without granting permanent admin access. It enables rule-based and Just-In-Time (JIT) elevation, ensuring users can perform privileged tasks only when necessary, and only under defined conditions.

### Rules-Based Elevation: Three Options

EPM supports three types of elevation rules:

1. **Automatic Elevation** --- The application is elevated silently without user interaction, based on predefined rules.
2. **User-Confirmed Elevation** --- The user is prompted to confirm the elevation request, typically with a business justification and/or Windows authentication.
3. **Support-Approved Elevation** --- The user submits a request that must be approved by IT or support staff before elevation is granted. This is the model we focus on in this post, as it allows integration with Microsoft Teams for real-time approvals.

### Just-In-Time Elevation with Support Approval

Support-approved elevation is ideal for organizations that want to maintain strict control over admin rights while still enabling flexibility for end users. When a user requests elevation, the request is logged and routed for approval. By integrating this process with Microsoft Teams using Azure Logic Apps, IT teams can receive instant notifications and respond quickly --- without switching tools or missing critical requests.

Currently, when approved, these requests remain valid for 24 hours.

### Benefits of Using EPM

Implementing Endpoint Privilege Management offers several key advantages:

* **User Empowerment**: Allows users to perform necessary tasks without waiting for manual intervention --- when policies allow it.
* **Improved Security**: Reduces the attack surface by eliminating standing admin rights.
* **Operational Efficiency**: Automates elevation workflows and reduces helpdesk overhead.
* **Compliance and Auditing**: Provides detailed logs of elevation activity for auditing and compliance reporting.

## The Challenge with Manual EPM Approvals

When EPM is configured in Microsoft Intune, end users can request elevation to run applications requiring administrator privileges. However, the traditional approval workflow requires IT administrators to:

1. Navigate to the Intune portal
2. Find the pending elevation request
3. Review the request details
4. Approve or deny the request

This process, while secure, creates friction, especially when approvers are busy with other tasks or aren't actively monitoring the Intune console.

The result?

Delayed approvals and frustrated users waiting for elevated access.

## Configuring EPM in Microsoft Intune

Before setting up the automation, you need an EPM elevation rules policy. In this example we enable the "Mark 8 Project Team" to request elevation for Wireshark. I am assuming here that EPM was already enabled in your tenant.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-03.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-04.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-05.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-06.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-07.webp)

Start in [Microsoft Intune](https://intune.microsoft.com/) and navigate to the **Endpoint security** blade. Under **Endpoint Privilege Management** go to **Policies** and create a new **Elevation rules policy**.

After going through the basics, fill in the detailed information about the application you are adding to the rule. This information can be collected using the `EpmTools.dll`.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-08.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-09.webp)

Using this tool you can even extract publisher certificates from the file. These can be added to the reusable library.

Finally, fill in all the necessary details about the file.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-10.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-11.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-12.webp)

Verify the configuration from a demo device. From the end-user perspective the **Run with elevated access** option should be visible, and the elevation request dialog should open.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-13.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-14.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-15.webp)
![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-16.webp)

For the Intune administrator, the request should appear in the **Elevation requests** tab almost immediately.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-17.webp)

### Verifying the Graph API Data

Before building the Logic App, confirm that elevation requests are visible through the [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/use-the-api). Open the [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) and query `deviceManagement/elevationRequests`.

![](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-18.webp)

Make sure you are using the **beta** version of the API and that the `DeviceManagementConfiguration.Read.All` permission has been granted. Otherwise, the query returns a permission error.

## How EPM Automation with Adaptive Cards Works

Our EPM automation solution bridges Microsoft Intune and Microsoft Teams by creating an automated workflow that:

* **Polls for pending requests** every 5 minutes using Microsoft Graph API
* **Posts Adaptive Cards** to a designated Teams channel with all request details
* **Enables one-click approval or denial** directly from Teams
* **Updates the Adaptive Card** to show the final decision and who made it

![EPM automation Adaptive Cards displaying a denied elevation request with reviewer details](../media/epm-approval-workflow-adaptive-cards-logic-apps/epm-approval-workflow-adaptive-cards-logic-apps-02.webp)

### Architecture for EPM Automation

```
1. Logic App (Recurrence Trigger - every 5 minutes)
        │
        ├──> GET Microsoft Graph API
        │    /deviceManagement/elevationRequests
        │
        ├──> Filter requests with status = "pending"
        │
        ├──> For each pending request:
        │    └──> Post Adaptive Card to Teams channel
        │         ├──> Approve button
        │         └──> Deny button
        │
        └──> When button clicked:
             └──> POST approval/denial via Graph API
             └──> Update Adaptive Card with decision
```

## Key Components of the EPM Automation Solution

### Azure Logic App for EPM Automation

The Logic App serves as the orchestration engine for EPM automation. Using a recurrence trigger, it periodically queries the Microsoft Graph API for pending EPM elevation requests and processes each one by posting an interactive Adaptive Card to Teams.

### Adaptive Cards for Approval Actions

The Adaptive Cards display comprehensive request information:

* **Requester** – Who’s requesting elevation
* **Device Name** – Which device the request originates from
* **Application** – The executable requesting elevation
* **File Path** – Where the application is located
* **Publisher** – The application’s publisher
* **Justification** – Why the user needs elevation

The card includes two action buttons: **Approve** (green) and **Deny** (red). Once clicked, the Adaptive Card updates to reflect the decision.

### Managed Identity for Secure EPM Automation

Security is paramount. Instead of storing credentials or secrets, the EPM automation solution uses an **Azure Managed Identity** to authenticate to Microsoft Graph API. This eliminates secret management overhead and follows security best practices.

### Microsoft Graph API Integration

The solution leverages the Graph API beta endpoint for EPM operations:

* `GET /deviceManagement/elevationRequests` – Retrieve pending requests
* `POST /deviceManagement/elevationRequests/{id}/approve` – Approve a request
* `POST /deviceManagement/elevationRequests/{id}/deny` – Deny a request

## Infrastructure as Code with Bicep

The entire EPM automation solution is defined using **Azure Bicep**, making it reproducible and version-controllable. Here’s a simplified look at the main resources:

```
// Managed Identity for secure Graph API access
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${logicAppName}-identity'
  location: location
  tags: tags
}

// Teams API Connection
resource teamsConnection 'Microsoft.Web/connections@2016-06-01' = {
  name: 'teams-connection'
  location: location
  properties: {
    displayName: 'Teams Connection for EPM Approval'
    api: {
      id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'teams')
    }
  }
}

// Logic App with workflow definition
resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: logicAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    definition: loadJsonContent('workflow.json').definition
    // ... parameters
  }
}
```

## Deploying Your EPM Automation with Adaptive Cards

A PowerShell deployment script automates the entire setup process:

```
# Deploy with default settings
.\deploy.ps1

# Or customize the deployment
.\deploy.ps1 -ResourceGroupName "rg-epm-approval" -Location "westeurope"

# Preview changes first
.\deploy.ps1 -WhatIf
```

The script handles:

* Prerequisites validation (Azure CLI, Bicep, login status)
* Resource group creation
* Bicep template deployment
* Graph API permission assignment via Microsoft Graph PowerShell
* Teams connection authorization prompt

### Required Graph API Permissions

The Managed Identity needs the following application permissions:

| Permission | Purpose |
| --- | --- |
| `DeviceManagementConfiguration.ReadWrite.All` | Read and update EPM elevation requests |
| `DeviceManagementManagedDevices.Read.All` | Read device information |

## Cost of EPM Automation

One of the best aspects of this EPM automation solution is its cost-effectiveness:

| Resource | Estimated Monthly Cost |
| --- | --- |
| Logic App (Consumption) | ~$0.50 |
| Managed Identity | Free |
| Teams API Connection | Free |
| Log Analytics (optional) | ~$2-5 |

**Total: ~$2-6/month** depending on the number of requests processed.

## Security Best Practices

The EPM automation solution follows security best practices:

* **No secrets stored** – Managed Identity handles authentication
* **Least privilege** – Only required Graph permissions are assigned
* **Audit trail** – All decisions are logged in both Intune and Logic App run history
* **Secure outputs** – Sensitive data is protected in Logic App runs

## Extending the EPM Automation Solution

The modular design allows for easy extensions:

* **Email notifications** – Add email alerts for high-priority requests
* **ServiceNow integration** – Create tickets for tracking purposes
* **Conditional logic** – Auto-approve requests from specific applications
* **Escalation workflows** – Escalate unanswered requests after a timeout

## Conclusion

**EPM automation with Adaptive Cards** transforms the approval experience from a portal-centric task into a seamless Teams-based workflow. Approvers can now handle elevation requests without context-switching, leading to faster response times and improved user satisfaction.

The solution is cost-effective (under $10/month), secure (no secrets, managed identity), and easy to deploy (Infrastructure as Code with automated deployment scripts).

Ready to implement EPM automation with Adaptive Cards in your environment? Check out the full source code and detailed deployment instructions on [GitHub](https://github.com/jensdufour/PUB-EPM-Teams-Integration)!

## Sources

* [Endpoint Privilege Management overview | Microsoft Learn](https://learn.microsoft.com/en-us/intune/intune-service/protect/epm-overview)
* [Azure Logic Apps documentation | Microsoft Learn](https://learn.microsoft.com/en-us/azure/logic-apps/)
* [Adaptive Cards documentation | Microsoft Learn](https://learn.microsoft.com/en-us/adaptive-cards/)
* [Microsoft Teams Connectors | Microsoft Learn](https://learn.microsoft.com/en-us/connectors/teams/?tabs=text1%2Cdotnet)
* [Microsoft Graph API | Microsoft Learn](https://learn.microsoft.com/en-us/graph/use-the-api)
* [Azure Managed Identities | Microsoft Learn](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)
* [Azure Bicep documentation | Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)