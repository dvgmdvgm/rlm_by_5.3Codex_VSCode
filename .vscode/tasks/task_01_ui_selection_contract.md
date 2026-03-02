# Task 01 — UI Selection Contract

## Objective
Define the minimal contract: selecting a specific car triggers 3D viewer update for that exact model.

## Scope
- Identify current car selection UI element(s).
- Define selected-car payload (minimum: `carId`, optional: `modelPath`).
- Define where 3D viewer container is mounted on page.

## File Targets
- `examples/login_page.html` (selection hook + viewer container placement)
- `examples/` (only if existing assets mapping file is present)

## Acceptance Criteria
- A single documented selection event/handler contract exists.
- Viewer mount point is explicitly defined.
- No unrelated UX additions are introduced.
