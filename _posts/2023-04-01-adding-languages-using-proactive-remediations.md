---
categories:
- Microsoft
- Technology
date: '2023-04-01T12:00:00'
status: publish
tags:
- Intune
- Proactive Remediations
- PowerShell
- Windows
- Language Packs
title: Adding a language pack using Proactive remediations
seo_title: 'Adding Language Packs Using Intune Proactive Remediations'
meta_description: 'Learn how to add language packs to Windows devices using Intune Proactive Remediations. Step-by-step guide with detection and installation scripts.'
focus_keyphrase: 'proactive remediations language pack'
---

One of the features of Intune is Proactive Remediation. This allows administrators to create scripts that automatically fix issues on devices before users even notice them. Adding a language pack using Proactive Remediation script is a straightforward process. I will guide you through the steps in this article.

I have been using this method to add additional language packs to my Windows 365 deployments. This is from great use to organizations that are multi-geographical.

## Creating the scripts

First, we will create a language pack installation script. This is split into two parts. One should be designed to detect the language currently in use on the device. The other installs the appropriate language pack.

The first script here uses some basic PowerShell to detect what languages are installed on a system and verifies if the one required is installed.

```
$OSInfo = Get-WmiObject -Class Win32_OperatingSystem
$languagePacks = $OSInfo.MUILanguages

if ($languagePacks -contains "de-DE")
    {
    write-output "Installed"
     Exit 0
    }
    else
    {
    write-output "Not installed"
     Exit 1
    }
```

We will leverage the [LanguagePackManagement](https://learn.microsoft.com/en-us/powershell/module/languagepackmanagement/?view=windowsserver2022-ps) Module to install the required languages. This downloads and installs the language components for the specified language.

```
Install-Language de-DE
```

Additionally, you have the option to directly enable the new language pack by using the following command:

```
Install-Language de-DE -CopyToSettings
```

**Warning! Please verify that these scripts we created earlier are saved in UTF-8 encoding.**

## Creating the script package

After we created the language pack installation script , we should create the Proactive Remediation script in Microsoft Intune. To do this, log in to the Intune portal and navigate to Reports. Click on “Endpoint Analytics” and select “Proactive remediations”.

After clicking on “Create script package”, give the script a name and a description and Publisher.

The next step is to select the installation script that we created in the initial step. We do this for both the “Detection script file” and the “Remediation script file”.

Make sure to set the slider for “Run script in 64-bit PowerShell” to “Yes”.

Finally, we should assign the policy. To do this, navigate to the Assignments section of the policy and select the group that the policy should apply to.

Additionally, you can also change the schedule and filter for specific devices.

## Conclusion

Adding a language pack using a Proactive Remediation script is a straightforward process that can save administrators time and ensure that devices are always running in the correct language.

By following the steps outlined in this article, administrators can easily create a language pack installation script and create a Proactive Remediation script to automate the installation process.