# MVP Voice Snapshot Protocol

This MVP uses the camera as a local viewfinder and captures still images on command. It does not continuously stream video to an AI service.

## Flow

1. Start the local viewfinder.

   ```bash
   python3 scripts/manga_snapshot_viewfinder.py --device /dev/video2
   ```

2. The user holds the manga naturally in front of the forward-facing C922 and asks a question or presses a trigger.

3. Press Enter, Space, or `S` to capture one high-resolution still image without closing the viewfinder. Press `Q` or Esc to quit.

4. Send the saved snapshot plus the user's question to an AI vision API.

5. Speak the response aloud through the user's audio output.

The one-shot capture script is still available for automation:

```bash
bash scripts/capture_manga_snapshot.sh /dev/video2
```

## Current Boundary

Continuous AI video streaming is deferred. For now, the camera preview stays local, and only an intentional snapshot is prepared for the future AI request.

This keeps the prototype closer to the conversational reading-assistant goal: the user frames the page, asks for help, captures a still, and receives a short spoken answer.

Voice triggering is a later layer over the same action: a recognized phrase should request a snapshot from the local viewfinder, then attach that saved image to the AI request.
