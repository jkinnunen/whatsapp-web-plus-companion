# Message review validation

Status: installed-NVDA validation pending. Automated tests use provider doubles; they do not validate speech, braille, or the live accessibility tree.

Use NVDA 2026.2 and Microsoft Store WhatsApp with the patched Companion installed. Restart NVDA after installation.

1. Focus a text message in Focus Mode. In object review, test previous, current, and next character, word, and line with the standard commands for both laptop and desktop layouts. Check first/last boundaries, multiline text, and emoji.
2. Repeat with incoming and outgoing messages, a caption, a quoted reply, and a link. Text should follow the exposed accessible name without hidden text or repeated metadata from value/description.
3. Move to another message and repeat. Enable privacy masking and confirm review does not reveal the original text.
4. Review named chat-list cells, including selected and unselected chats. Confirm the currently exposed summary is available without revealing privacy-masked text. Test the compose box, search, message options, and call controls: typing, selection, and existing native review must remain usable.
5. Repeat with review following focus enabled and disabled, and with a message that already has usable native text. Confirm no automatic review-mode or tracking-setting changes.
6. Check braille output and routing if a display is available. Check native call shortcuts and browse/focus switching for regressions.
7. Focus **New chat** and review its label by character and word. Test Enter and Space separately, closing the resulting panel between tests. Confirm activation still works once, and the next focused control is reviewed instead of the previous label. Repeat in another interface language if available. Unnamed buttons, editable fields, and unsupported menu items should retain native behavior.
8. Review the **Chats** toggle and the **All** filter tab. Check pressed/unpressed and selected/unselected announcements during ordinary navigation, then review the current label again. Verify the existing arrow, Tab, Enter, and Space behavior remains unchanged and braille still reports control states.
9. Review **Unread 8** by character and word: the complete label and count must be available, not just the badge. Repeat after the unread count changes and after leaving/returning to the tab. Check braille output and routing against NVDA's configured behavior; object routing may legitimately activate the control. Separately, NVDA's move-caret-to-review command must not create an artificial typing caret or activate a noneditable control. Name-based review has no native IA2 text geometry or formatting. Confirm compose/search caret navigation still works normally.

10. Focus a content-derived preview button implemented as `div role="button"`. Review its entire current name by character/word, then check native activation, focus departure, and any privacy masking. Confirm a plain text container without button/tab semantics keeps native behavior.

Record observed failures using object role, backend, IA2 attributes, TextInfo class, and overlay MRO from NVDA+F1. Redact message text and contact details.
