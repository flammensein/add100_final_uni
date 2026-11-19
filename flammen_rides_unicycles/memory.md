# Next-Session Memory

## Correct project location

Use `/home/flammen/Desktop/ADD_100_AI_Final_repo/add100_final_uni/flammen_rides_unicycles` as the active project directory. Confirm this location before editing. Do not continue work in `/home/flammen/Desktop/2026-11-10/ADD_100_2026/flammen_rides_unicycles` unless explicitly asked.

The earlier wrong-location folder has a `backup004` snapshot that includes its root files, including the earlier app version. The user plans to decide on cleanup later; do not edit or remove that backup without permission.

## Current app

- Entry point: `streamlit_app.py`
- Run from the `add100_final_uni` repository root with `streamlit run flammen_rides_unicycles/streamlit_app.py`.
- Guided stages: frame/tire → saddle/seatpost → rim/drivetrain/brakes → review and confirm build → billing/shipping and final order review.
- Billing and shipping fields must remain unavailable until the user confirms the build.
- Going back to edit should preserve the build draft and any checkout details already entered.
- The app reuses the project catalog, invoice formatting, pricing/validation constants, and `order_storage.py`; orders remain structured JSON for now.
- Payment method is recorded as a choice only; the app does not process payments.

## Validation and follow-up

The guided-flow tests verified deferred billing fields, order submission, and edit-and-return behavior; the existing order-storage tests also passed. Streamlit was launched from the target repository root and returned HTTP 200.

Before the next implementation, confirm the assignment rubric and ask what the user wants to prioritize next. Useful open questions include visual styling, any rubric-specific required features, and whether JSON storage remains acceptable for the final deployment or should be migrated to MySQL.

## Process reminders

- Confirm the intended directory before making changes.
- Ask one focused question at a time when a requirement is unclear.
- Keep changes limited to the requested project and preserve existing backups.
