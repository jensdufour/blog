---
categories:
- Linux
- Microsoft
- Technology
date: '2024-01-30T14:08:32'
status: publish
tags:
- '2024'
- Intune
- MDM
- Microsoft
- Modern Device Management
title: 'Entra ID: The Magic Wand for Ubuntu 23.04 Authentication'
---

## Introduction

Welcome to this article about Entra ID authentication for Ubuntu devices. Entra ID authentication is a powerful way to authenticate on your devices. Additionally, you will learn how to enroll your Ubuntu device in Intune, a cloud-based service that helps you manage and secure your devices. By the end of this article, you will be able to use your Entra ID credentials to log in to your Ubuntu device. You will need some basic knowledge of Ubuntu, Microsoft Entra, and Microsoft Intune to follow along. I hope you enjoy this article and find it useful. Let’s get started!

## Setting up an Entra ID Application

We start with the beginning! Using the Entra ID authentication with Ubuntu requires the creation of a Microsoft Entra application. This application needs to be able to retrieve the tenant ID and application ID required for the authentication.

### Creating an Entra ID Application

We will create the application through the [Entra portal](https://entra.microsoft.com). Going through the “Identity > Applications > App registrations” where we will select “New registration”. We will name the application “Ubuntu Entra ID Authentication”, so the purpose of the application within our tenant is clear. The remaining options you can leave as default and click “Register” at the bottom of the page. This will give you the “Application ID”. Together with the “Tenant ID” this forms the basis for the Entra ID authentication.

## Using a Script to Get the Ubuntu Device to Use Entra ID Authentication

The first thing we got to do before enrolling the device to Microsoft Intune is to enable the authentication with Microsoft Entra ID. Unfortunately, this is something we still have to do manually, as for today there is no zero-touch provisioning with Microsoft Intune for Linux nor Ubuntu devices. However, as any good system administrator would do, we put this in a script.

### Using a script to enable the authentication

Although support for Linux is still fairly limited at this point in time, we can already use the script we created to prepare everything for the Entra ID authentication.

The script can be seen below in its entirety. Make sure to adapt the Tenant ID and App ID.

```
#!/bin/bash

# Replace these two variables with your relevant Tenant ID and Client Secret Value
tenant_id="<tenant-id>"
app_id="<app-id>"

# Check if the script has already run
if [ -f /var/run/aad_ubuntu.lock ]; then
    echo "Script has already run. Exiting..."
    exit 0
fi

# Create lock file to indicate that the script has run
sudo touch /var/run/aad_ubuntu.lock

# Check Ubuntu version
if [[ $(lsb_release -sr 2>/dev/null) == "23.04" || $(lsb_release -sr 2>/dev/null) == "23.10" ]]; then
    echo "Ubuntu version is supported."
else
    echo "Unsupported Ubuntu version."
    exit 1
fi

# Install required packages
sudo apt-get update
sudo apt-get install -y libpam-aad libnss-aad aad-cli

# Configure Azure Active Directory Authentication
echo "auth [success=1 default=ignore] pam_aad.so" | sudo tee -a /etc/pam.d/common-auth

# Enable home directory creation on login
sudo pam-auth-update --enable mkhomedir

# Add your tenant details to the configuration file
sudo truncate -s 0 /etc/aad.conf
echo "tenant_id = $tenant_id" | sudo tee -a /etc/aad.conf
echo "app_id = $app_id" | sudo tee -a /etc/aad.conf
echo "[cetsjdf.be]" | sudo tee -a /etc/aad.conf
echo "offline_credentials_expiration = 30" | sudo tee -a /etc/aad.conf
echo "homedir = /home/cetsjdf.be/%u" | sudo tee -a /etc/aad.conf
echo "shell = /bin/zsh" | sudo tee -a /etc/aad.conf

# Restart services
sudo systemctl restart systemd-logind.service
echo "Entra ID Authentication setup complete."
exit 0
```

After getting the successful prompt “Entra ID Authentication setup complete”, we can be certain that it is enabled. Or can we, as you can see below, we try to login with a user before enrolling the device, as that user in Microsoft Intune. This will be vital to further manage the device.

### Testing the Entra ID Authentication

We are at the end of our journey! Great! But for the most important part, will it work? Testing it is easy, after rebooting the Ubuntu device, try to login with any user from your Entra ID tenant. If everything goes well, it should look something like below.

## Enrolling an Ubuntu Device in Intune

The main question you can ask yourself here is “Why should we enroll a device to Microsoft Intune?”. Fairly simple, we will use Intune to further configure the device so that the local account created during the installation of Ubuntu is no longer to be used. Now there are a couple of things we have to do beforehand, which you can find in the prerequisites below.

### Prerequisites

First of all, your device should be at least Ubuntu 22.04 or 20.04 LTS, with the GNOME graphical desktop environment. Be aware that all Ubuntu devices enrolled with Intune are considered corporate-owned devices.

Furthermore, the Microsoft Edge browser and Microsoft Intune app should be installed to the device. This you can do yourself or you can utilize the script that I have created below. All these scripts can also be found on my Github.

```
#!/bin/bash

# Check if the script has already run
if [ -f /var/run/aad_ubuntu_prereq.lock ]; then
    echo "Script has already run. Exiting..."
    exit 0
fi

# Create lock file to indicate that the script has run
sudo touch /var/run/aad_ubuntu_prereq.lock

# Check Ubuntu version
if [[ $(lsb_release -sr 2>/dev/null) == "23.04" || $(lsb_release -sr 2>/dev/null) == "23.10" ]]; then
    echo "Ubuntu version is supported."
else
    echo "Unsupported Ubuntu version."
    exit 1
fi

# Install the Microsoft GPG key
wget -O - https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/microsoft-ubuntu-jammy-prod.list'
sudo sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list'
sudo rm microsoft.gpg
sudo apt update

# Update Java for Microsoft Intune
sudo apt install -y openjdk-11-jre

# Install Microsoft Edge
sudo apt install -y microsoft-edge-stable

# Install Microsoft Intune
sudo apt install -y intune-portal

echo "Installation complete."
```

It might be useful to know that I always include lock files in my scripts to make sure I don’t run them twice. This is not always necessary but is a precaution I take myself. You should end up with an “Installation complete.”-message, as you can see.

### Enrolling the device in Microsoft Intune

This is a process we call user-driven enrollment into Microsoft Intune. The process is fairly simple, once the prerequisites are implemented. We will begin by opening Microsoft Edge and logging in.

It is easier to start with logging into Microsoft Edge, this is not a requirement, but it makes our lives easier in the long run.

Afterwards, we continue with the Intune enrollment. The user will need to sign-in and afterwards there will be an additional authentication prompt to apply the configuration.

## Conclusion

In this post, I showed you how to set up Entra ID authentication for your Ubuntu 23.04 device, and how to enroll it in Microsoft Intune for further management. Entra ID is a powerful and secure way to authenticate your Linux device with your Microsoft account, and Intune is a cloud-based service that allows you to configure and monitor your device remotely.

By following the steps in this post, you can leverage the benefits of both Entra ID and Intune for your Ubuntu device.

If you have any questions or feedback, please leave a comment below. And if you found this post helpful, don’t forget to share it with your friends and colleagues who might be interested in Entra ID authentication for Ubuntu. Thank you for reading!