# Task 02 — 3D Viewer Integration

## Objective
Implement 3D rendering so selected car is shown and appears to rotate continuously.

## Scope
- Add minimal WebGL/3D integration (scene, camera, renderer).
- Load/render selected car model based on `carId` mapping.
- Add continuous rotation animation for the selected model.
- Update/replace model when a different car is selected.

## File Targets
- `examples/login_page.html` (viewer DOM and integration script)
- `examples/assets/models/*` (if model files are required)

## Acceptance Criteria
- Selecting a car displays corresponding 3D model.
- Model visibly rotates without manual user interaction.
- Switching selection updates the model without page reload.
- Failures (missing model) are handled with a simple visible fallback message.
