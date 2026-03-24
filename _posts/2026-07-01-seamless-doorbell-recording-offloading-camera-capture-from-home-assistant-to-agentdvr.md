---
title: 'Seamless Doorbell Recording: Offloading Camera Capture from Home Assistant to AgentDVR'
date: '2026-07-01'
status: draft
seo_title: 'AgentDVR Doorbell Recording with Home Assistant Notifications'
meta_description: 'Offload doorbell camera recording from Home Assistant to AgentDVR with a 10-second pre-buffer, Samba-mounted playback, and seamless mobile notifications via MQTT.'
focus_keyphrase: 'AgentDVR doorbell recording Home Assistant'
categories:
- Home Automation
- Technology
tags:
- Home Assistant
- AgentDVR
- MQTT
- Proxmox
- Samba
- Camera
- Notifications
---

## Introduction

If you run [AgentDVR](https://www.ispyconnect.com/userguide-agent-dvr.aspx) as your camera platform and [Home Assistant](https://www.home-assistant.io/) as your smart home hub, you may have started with a setup where HA handles recording via the `camera.record` service. That approach works, but it introduces a round-trip delay that causes the first seconds of motion to be missed. AgentDVR detects motion, publishes an MQTT alert, HA receives it, then HA calls `camera.record` back to AgentDVR. By the time the recording starts, the visitor is already at the door.

In this post, I walk through how to offload recording entirely to AgentDVR with a configurable pre-buffer, share those recordings with HA over Samba, and build a notification pipeline where tapping the alert on your phone plays the video directly. No extra infrastructure exposed to the internet, no fixed delays, and no missed footage.

## The Problem with HA-Based Recording

The original automation looked roughly like this:

1. AgentDVR detects motion on the doorbell camera
2. AgentDVR publishes `agentdvr/cameras/doorbell/alert` to MQTT
3. HA receives the MQTT message and triggers an automation
4. The automation calls `camera.record` and `camera.snapshot` in parallel
5. HA sends a notification with the snapshot and a link to the video

The issue is step 4. By the time HA processes the trigger, calls the service, and AgentDVR starts writing the file, several seconds have passed. The `lookback` parameter on `camera.record` offers a small stream buffer (5 seconds in my case), but it is unreliable and depends on the stream being actively consumed by HA.

The result: notifications arrive with a snapshot, but the recording starts too late. The person who triggered the motion is already walking away or standing at the door, and the approach is not captured.

## Architecture Overview

The improved setup separates concerns cleanly:

| System | Responsibility |
|---|---|
| **AgentDVR** | Motion detection, video recording with pre-buffer, thumbnail generation |
| **MQTT** | Event bus between AgentDVR and HA |
| **Samba** | File sharing between the AgentDVR LXC and the HA VM |
| **Home Assistant** | Snapshot capture, mobile notifications, video serving |

The flow becomes:

1. AgentDVR detects motion and starts recording (with 10 seconds of pre-buffered footage already in memory)
2. AgentDVR publishes an MQTT **alert** message
3. HA triggers, takes a snapshot from the camera for the notification thumbnail
4. HA **waits** for AgentDVR to publish a **recording finished** MQTT message
5. HA copies the recording to a web-accessible path and sends the notification
6. Tapping the notification plays the video directly

No round-trip for recording. No fixed sleep. The wait is fully dynamic.

## Prerequisites

Before starting, make sure you have:

| Requirement | Detail |
|---|---|
| **AgentDVR** | Installed and running with a camera configured |
| **Home Assistant** | With the AgentDVR integration and MQTT configured |
| **MQTT broker** | Mosquitto or equivalent, reachable by both AgentDVR and HA |
| **Proxmox** (or similar) | Both AgentDVR and HA accessible on the same network |

In my environment, AgentDVR runs in an LXC container and HA runs as HAOS in a VM, both on the same Proxmox host. The steps apply to any setup where the two systems can reach each other over the network.

## Step 1: Configure AgentDVR for Alert-Based Recording

Open the AgentDVR web interface and navigate to your camera's **Recording** settings.

Change two values:

| Setting | Before | After |
|---|---|---|
| **Mode** | Disabled | Alert |
| **Buffer** | 0 seconds | 10 seconds |

**Mode: Alert** means AgentDVR will automatically start recording when a motion alert fires. **Buffer: 10** tells AgentDVR to keep a rolling 10-second buffer in memory. When recording starts, those 10 seconds are prepended to the file. This is the key improvement: the footage before the motion event is captured without any external trigger.

The remaining settings can stay at their defaults. For reference, these are the values I use:

| Setting | Value |
|---|---|
| Max Record Time | 900 seconds |
| Min Record Time | 15 seconds |
| Inactivity Timeout | 8 seconds |
| Max Framerate | 10 |
| Encoder | Encode (includes timestamp/overlays) |

## Step 2: Add an MQTT Action on Recording Finished

AgentDVR needs to tell HA when a recording is done. Navigate to your camera's **Actions** section and add a new action:

| Field | Value |
|---|---|
| If | Recording Finished |
| Task | MQTT |
| Topic | `agentdvr/cameras/doorbell/recording_stopped` |
| Payload | `{FILENAME}` |

The `{FILENAME}` variable is an AgentDVR placeholder that gets replaced with the full filesystem path of the completed recording. For example:

```
/opt/agentdvr/agent/Media/WebServerRoot/Media/video/AWKQL/1_2026-03-16_13-14-35_200.mp4
```

This allows HA to identify exactly which file was just written. The folder name (`AWKQL` in this case) is the camera-specific folder that AgentDVR creates automatically.

> **Tip:** You can verify the MQTT message is being sent by subscribing from the command line: `mosquitto_sub -t "agentdvr/cameras/doorbell/recording_stopped"`. Trigger a test recording and wait for it to finish. The full path should appear.

## Step 3: Share AgentDVR Recordings via Samba

HA needs access to the recording files. Since both systems run on the same Proxmox host, the simplest and most secure approach is a Samba share. No need to expose AgentDVR to the internet.

### Install Samba on the AgentDVR LXC

SSH into your Proxmox host and exec into the AgentDVR container:

```bash
pct exec <CTID> -- bash
apt update && apt install -y samba
```

### Create a Samba User

Create a dedicated user for HA with no shell access:

```bash
useradd -M -s /usr/sbin/nologin haos
smbpasswd -a haos
```

Set a strong password when prompted. You will need this password when configuring the mount in HA.

### Configure the Share

Edit `/etc/samba/smb.conf` and add the following at the bottom:

```ini
[doorbell]
   path = /opt/agentdvr/agent/Media/WebServerRoot/Media/video
   browseable = yes
   read only = yes
   guest ok = no
   valid users = haos
```

The path points to the `video` directory, which contains the camera-specific subfolder with the actual recordings.

> **Note:** Find your AgentDVR recording path by checking the camera's **Storage** settings in the AgentDVR web interface. The **Location** field shows the base path, and the **Folder** field shows the subfolder name.

### Start Samba

```bash
systemctl enable smbd && systemctl start smbd
```

Verify the share works locally before moving on:

```bash
smbclient //127.0.0.1/doorbell -U haos -c "ls"
```

You should see the camera subfolder listed.

## Step 4: Mount the Share in Home Assistant

In HA, navigate to **Settings > System > Storage > Add Network Storage** and fill in:

| Field | Value |
|---|---|
| Name | `agentdvr_recordings` |
| Usage | **Media** |
| Server | `<AgentDVR LXC IP address>` |
| Protocol | **Samba/Windows (CIFS)** |
| Remote share path | `doorbell` |
| Username | `haos` |
| Password | *(the password you set)* |

Click **Connect**. If successful, recordings will appear under `/media/agentdvr_recordings/` inside HA and will be browsable in the Media Browser.

### Register the Media Directory

Update your `configuration.yaml` to make the mount available as a named media source:

```yaml
homeassistant:
  media_dirs:
    doorbell_recordings: /media/agentdvr_recordings
```

Restart HA Core after saving. The recordings should now appear in the Media Browser under **My media**.

## Step 5: Add the Shell Command

HAOS runs HA Core in a container that cannot follow symlinks to paths outside its own mount. This means files in `/media/` are not directly URL-accessible via `/local/`. To make a recording playable from a notification tap, we copy the latest file to `/config/www/`:

```yaml
shell_command:
  doorbell_copy_video: >-
    cp "$(ls -t /media/agentdvr_recordings/AWKQL/*.mp4 | head -1)"
    /config/www/doorbell_latest.mp4
```

Replace `AWKQL` with your camera's subfolder name from AgentDVR. Add this to your `configuration.yaml` and restart HA Core.

> **Why not a symlink?** HAOS runs HA Core in an isolated container. Symlinks from `/config/www/` to `/media/` do not resolve inside the container, resulting in a 404. Copying the file is the only reliable way to make it URL-accessible at `/local/doorbell_latest.mp4`.

## Step 6: Remove HA-Based Recording from the Automation

If your existing automation uses `camera.record`, remove it along with any related video file path variables, `shell_command.fix_video`, and `shell_command.cleanup_videos`. The snapshot step can stay if you want the notification thumbnail to be a captured frame at the moment of detection. If you prefer AgentDVR's generated thumbnails, you can remove the snapshot as well.

## Step 7: Build the Final Automation

The complete automation:

```yaml
alias: Doorbell Motion Detection
description: >-
  On doorbell motion, capture a snapshot, wait for AgentDVR
  to finish recording, copy the video to a web-accessible path,
  then notify both phones. Tapping plays the video directly.
  60-second cooldown.
trigger:
  - platform: mqtt
    topic: agentdvr/cameras/doorbell/alert
    payload: "true"
    id: doorbell_motion
condition:
  - condition: template
    value_template: >-
      {{ this.attributes.last_triggered is none or
         (now() - this.attributes.last_triggered).total_seconds() > 60 }}
action:
  - action: camera.snapshot
    data:
      filename: /config/www/doorbell_motion.jpg
    target:
      entity_id: camera.agentdvr_doorbell_doorbell
  - wait_for_trigger:
      - platform: mqtt
        topic: agentdvr/cameras/doorbell/recording_stopped
    timeout: "00:05:00"
    continue_on_timeout: false
  - action: shell_command.doorbell_copy_video
  - action: notify.mobile_app_iphone
    data:
      message: Motion detected at the doorbell.
      data:
        image: https://ha.example.com/local/doorbell_motion.jpg
        tag: doorbell-motion
        url: https://ha.example.com/local/doorbell_latest.mp4
  - action: notify.mobile_app_s22
    data:
      message: Motion detected at the doorbell.
      data:
        image: https://ha.example.com/local/doorbell_motion.jpg
        tag: doorbell-motion
        clickAction: https://ha.example.com/local/doorbell_latest.mp4
mode: single
```

Replace `ha.example.com` with your HA external URL. Replace `camera.agentdvr_doorbell_doorbell` with your camera entity, and adjust the `notify.mobile_app_*` services to match your devices.

### How It Works

Let's walk through each step:

1. **MQTT trigger**: AgentDVR detects motion and sends `true` to `agentdvr/cameras/doorbell/alert`. HA picks this up immediately.

2. **Cooldown condition**: A template checks if the last trigger was more than 60 seconds ago. This prevents duplicate notifications from rapid consecutive motion events.

3. **Snapshot**: `camera.snapshot` grabs a frame from the live stream and saves it to `/config/www/doorbell_motion.jpg`. This is served at `/local/doorbell_motion.jpg` and used as the notification thumbnail.

4. **Wait for recording**: `wait_for_trigger` listens for the `recording_stopped` MQTT topic. This is the critical piece. Instead of a hardcoded `delay`, the automation waits exactly as long as the recording takes. If the motion lasts 15 seconds, it waits 15 seconds. If it lasts 2 minutes, it waits 2 minutes. The 5-minute timeout is a safety net in case the MQTT message never arrives.

5. **Copy video**: The shell command finds the newest `.mp4` in the AgentDVR recordings folder and copies it to `/config/www/doorbell_latest.mp4`, making it available at `/local/doorbell_latest.mp4`.

6. **Notify**: Both phones receive a notification with the snapshot as the image. On iOS, the `url` key makes tapping the notification open the video. On Android, `clickAction` does the same.

### iOS vs Android Notification Differences

The HA Companion App handles notification actions differently per platform:

| Platform | Thumbnail Key | Tap Action Key |
|---|---|---|
| **iOS** | `entity_id` (camera entity) or `image` (URL) | `url` |
| **Android** | `image` (URL) | `clickAction` |

Both point to the same URLs, but the keys differ. The automation sends both in the same action block, and each platform picks up its relevant fields.

## Troubleshooting

### Samba mount fails with "BAD_NETWORK_NAME"

Do not use hyphens in the Samba share name. Use `[doorbell]` instead of `[doorbell-recordings]`. HAOS CIFS mounts can fail on share names with special characters.

### Samba mount fails with "permission denied" (return code -13)

Reset the Samba password with `smbpasswd -a haos` on the AgentDVR LXC, then delete and re-add the network storage in HA with the new password. HA caches the old credentials.

### Media Browser shows the mount but no files

Ensure the `haos` user has read and traverse permissions on the recording directory:

```bash
chmod -R o+rX /opt/agentdvr/agent/Media/WebServerRoot/Media/video
```

### Notification tap returns a 404

The file at `/config/www/doorbell_latest.mp4` must exist before the notification is sent. Check the automation trace to confirm the `shell_command.doorbell_copy_video` step completed successfully. Also verify that the HA external URL in the notification matches your actual setup.

### Recording starts but the MQTT message never arrives

Verify the action is configured on the **Recording Finished** event (not Recording Started) in AgentDVR. Test with `mosquitto_sub -t "agentdvr/cameras/doorbell/recording_stopped"` and trigger a recording manually.

## Conclusion

By letting each system handle what it does best, the result is a recording pipeline that is faster, more reliable, and captures footage that the old setup missed. AgentDVR records with a 10-second pre-buffer and zero latency. HA takes a snapshot at the moment of detection, waits for the recording to complete, and delivers a notification that plays the video in a single tap.

The Samba share keeps everything internal with no additional services exposed to the internet. The `wait_for_trigger` pattern makes the timing fully dynamic with no hardcoded delays to tune. And if HA restarts mid-recording, AgentDVR keeps recording independently.

## Sources

* [AgentDVR User Guide](https://www.ispyconnect.com/userguide-agent-dvr.aspx)
* [Home Assistant Companion App Notifications](https://companion.home-assistant.io/docs/notifications/notifications-basic/)
* [Home Assistant camera.record Service](https://www.home-assistant.io/integrations/camera/#service-record)
* [Home Assistant wait_for_trigger](https://www.home-assistant.io/docs/scripts/#wait-for-trigger)
* [Home Assistant Network Storage](https://www.home-assistant.io/common-tasks/os/#network-storage)
