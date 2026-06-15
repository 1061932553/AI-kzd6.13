# P2-11 Basic Image Tap

P2-11 adds offline single-template matching and routes a successful match into
the existing `tap` action. It does not access a real camera, JxbService, COM
ports, or real hardware.

## Template Matching

`TemplateMatcher` accepts RGB24 `CameraFrame` input and a PPM/P6 template. It
checks every candidate location inside an optional search rectangle, computes a
simple normalized pixel-difference confidence, and returns the highest
confidence match when it meets the configured threshold.

Returned fields include:

- top-left match coordinate
- template size
- center coordinate
- confidence
- search rectangle
- candidates checked

## Tap Image

`execute_tap_image`:

1. Captures a frame from an injected frame provider.
2. Searches for one template.
3. Converts the matched center to screen-normalized coordinates.
4. Calls the existing `execute_tap` action.

If no template is found, no arm call is made. When configured, the failed frame
is saved as a PPM screenshot.

## Debug Command

```powershell
python -m tools.template_debugger --image tests\fixtures\screen.png --template tests\fixtures\confirm.png
```

The fixture files use PPM/P6 bytes with `.png` names to match the task command
without adding an image library dependency.
