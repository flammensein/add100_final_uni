# Process Reflection

## What went well

- The existing unicycle catalog, compatibility rules, invoice formatter, and JSON order-storage code provided a useful foundation for the Streamlit app.
- Clarifying that AI was intended to help build the app—not be a feature inside it—kept the app focused on the assignment.
- Feedback about the single-page layout led to a guided flow that separates customization, build review, and checkout.
- The updated flow was tested to confirm billing and shipping stay hidden until build confirmation, edits preserve entered checkout details, and submitted orders retain the existing structured format.

## What could have been done better

- The assistant should have confirmed the intended repository path before editing. The first implementation went into the wrong folder and caused avoidable rework.
- The assistant should have translated “more of a flow” into separate customization stages sooner, instead of initially moving only checkout to a later step.
- The assignment’s AI requirement could have been clarified earlier to avoid interpreting it as a request for an AI-powered feature inside the app.

## What the user could have done better

- Naming the intended project path and describing the desired step-by-step experience in the first request could have reduced rework.
- Once the mismatch appeared, the user gave clear, actionable corrections and constraints, which helped get the work back on track.

## What we learned

- Confirm the source-of-truth repository and destination before changing files, especially when multiple similar project folders are available.
- A Streamlit configurator can use `st.session_state` to preserve drafts while navigating between stages.
- The customer should review and confirm the build before the app asks for billing or shipping details.
- Existing JSON order storage is reusable for a prototype, but should be replaced with durable storage before relying on cloud persistence.
- Small, focused interaction tests can verify that later-stage fields do not appear prematurely and that the full order flow still works.
