# WhatsApp Companion changelog

## 2026.10.19 - 2026-10-19

Clean UI now recognizes the Indonesian desktop promotion description, so the promotion is hidden without a custom title.

### NVDA review and connection feedback

- Make empty-text message and chat cells readable through NVDA's standard character, word, and line review commands in Focus Mode.
- Use complete accessible names for supported buttons, toggle buttons, and tabs, including changing unread counts and content-derived labels. Preserve native activation, states, usable cell text, and editable-field text handling.
- Scope review overlays to the WhatsApp app module and respect privacy-masked accessible names.
- Announce connection recovery success, failure, or app closure after recovery starts, rather than leaving users with only a restoring message. Preserve speech, braille, foreground, and cancellation guards.

### Read Sticker and embedded userscript

- Include WhatsApp Web Plus 2026.10.19 with Gemini, Groq, Cloudflare Workers AI, and Custom, OpenAI-compatible providers in that order.
- Add bounded native HTTPS sticker transport without a browser extension or changes to the announcement bridge. Validate endpoints, payloads, deadlines, response limits, and cancellation.
- Keep provider credentials encrypted in the WhatsApp profile. Changing Cloudflare models retains the token for the same account. Support Llama 3.2 image input and multimodal-message input for compatible alternative models.
- Include explicit Llama 3.2 model agreement and local preview, with completion/timeout feedback and no automatic sticker resend.
- Include menu fitting in small windows, download progress, photo album captions, Read more expansion, Alt+1 arrow-navigation fixes, and chat/channel/community closure announcements.
- Update defaults: Privacy mode, automatic message reading, Enter/Space voice playback, Clean Status, menu fitting, and Clean UI on; total unread-chat announcements off. Existing settings are retained.

### Documentation and validation

- Refresh English and Indonesian help, document provider setup and limitations, and summarize object review and recovery results.
- Add regression coverage for review overlays, native sticker transport, and recovery outcomes. Add-on packaging and installed-NVDA validation remain separate steps.
- Align the embedded script with year.month.day version 2026.10.19, which compares higher than 2.6.91. Signed publishing remains a separate step and anti-rollback checks remain unchanged.

## 2026.10.04

### Connection recovery

- Retry connection recovery for up to 90 seconds on busy systems, instead of stopping after three attempts within 20 seconds.
- Retry temporary PowerShell failures while checking whether WhatsApp is still running, using the same overall recovery deadline. Treat WhatsApp as closed only after a successful check returns no running processes.
- Announce recovery progress once when retrying a failed process check or reconnecting to a running app. Preserve the last completed operation result and keep normal app closure quiet.
- Recognize cancellation even when it coincides with a failed probe reaching its deadline.
- Preserve underlying PowerShell stage and timeout details in reconnect logs. Identify discovery that completes after the deadline as a timeout instead of reporting that no target was found.

## 2026.09.25

### Reliability fixes

- Release the registry lease and report a recovery error when deleting the recovery journal fails.
- Discard queued braille output when braille messages are disabled, including timer retries and context-clear notices.
- Verify release tags, source versions, packaged manifests, artifact names, and repair-helper integrity before publishing.
- Verify the embedded userscript version, exact bytes, hash, and bundle metadata against the upstream lock before publishing.

## 2026.09.23

### Message reading

- Open Alt+Shift+C in a native NVDA reader without launching a browser window.
- Read authored message lines in a read-only text field without visual line wrapping. Switch to formatted view for links and lists.
- Copy only message text without viewer headings or timestamps. Preserve original line breaks and explicit blank lines.
- Validate reader content and reject malformed lists while preserving valid nested lists and headings.

### Shortcuts and calls

- Include WhatsApp Web Plus 2.6.84 with shortcut recording, manual remapping, and optional shortcuts to start voice and video calls.
- Open the Shift+F8 Shortcut list in an NVDA reading window with section headings. Include script defaults and WhatsApp built-in shortcuts for browser and WebView2 versions.
- Provide native call shortcuts for answering, declining, microphone, camera, reactions, raising or lowering a hand, screen sharing, and ending calls.
- Customize call-control labels in multiple languages while retaining built-in labels. Settings survive add-on updates in the same NVDA configuration.
- Improve recovery from the compact call view and recognition of controls during screen sharing.
- Prevent recursive dispatch when a remapped shortcut overlaps native chat navigation.

### Startup and compatibility

- Allow slower listener checks up to 30 seconds per query within a 60-second listener budget and the overall launch deadline. Log port and process queries separately. Keep endpoint ownership checks before connecting.

- Narrow package discovery to the selected WhatsApp app and allow more time for initial package and process checks while preserving cancellation and overall deadlines.
- Include the PowerShell stage, elapsed time, and time budget in failure logs.

- Preserve the built-in WhatsApp app module on NVDA 2026.2 and later, including its default focus interaction and manual browse-mode selection.
- Retain compatibility with earlier supported NVDA versions and keep native call shortcuts available.
- Improve startup recovery after WhatsApp reloads without injecting the userscript twice into the same document.
- Improve delayed command feedback in NVDA speech On-demand mode.

### Registry permissions and repair

- Fix permission diagnosis reporting success when the per-user WebView2 policy keys are missing, even though launching WhatsApp cannot create them. Offer setup through Diagnose and repair WebView2 policy permissions.
- Verify registry access from the normal NVDA session after repair, including when the elevated helper reports that permissions already exist. Retry any pending restoration of the temporary launch setting.
- Stop permission diagnosis when the WhatsApp process state cannot be verified.
- Fix repair stopping before the administrator prompt because the packaged batch helper did not match its expected hash. Correct the integrity metadata and stabilize helper line endings.
- Verify both repair helpers inside the built add-on package to catch integrity mismatches before release.

### Updates
- Verify signed userscript updates with trusted Ed25519 keys. Keep the installed bundle when verification fails or is unavailable.

### Requirements

- Requires NVDA 2025.1 or later. The manifest's last-tested version is NVDA 2026.2.
- Bundles WhatsApp Web Plus 2.6.84. Publisher signing guides are available in the script repository in English and Indonesian.
