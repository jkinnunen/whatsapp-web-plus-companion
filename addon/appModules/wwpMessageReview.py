"""Expose named WhatsApp cells, buttons, and tabs to NVDA's native object review."""

import controlTypes
import textInfos
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObjectTextInfo
from NVDAObjects.IAccessible.ia2Web import Ia2Web


def isNamedGridCell(obj, clsList=()):
	"""Match named message and chat-list cells, not their interactive children."""
	try:
		attributes = obj.IA2Attributes
		return (
			(isinstance(obj, Ia2Web) or any(issubclass(cls, Ia2Web) for cls in clsList))
			and obj.windowClassName == "Chrome_RenderWidgetHostHWND"
			and obj.role == controlTypes.Role.TABLECELL
			and controlTypes.State.EDITABLE not in obj.states
			and controlTypes.State.PROTECTED not in obj.states
			and attributes.get("tag") == "div"
			and "gridcell" in attributes.get("xml-roles", "").split()
			and attributes.get("name-from") == "attribute"
			and attributes.get("explicit-name") == "true"
		)
	except Exception:
		# WhatsApp can replace the provider during inspection.
		return False


def isReviewTarget(obj, clsList=()):
	if isNamedGridCell(obj, clsList):
		return True
	try:
		attributes = obj.IA2Attributes
		if not (
			(isinstance(obj, Ia2Web) or any(issubclass(cls, Ia2Web) for cls in clsList))
			and obj.windowClassName == "Chrome_RenderWidgetHostHWND"
			and controlTypes.State.EDITABLE not in obj.states
			and controlTypes.State.PROTECTED not in obj.states
		):
			return False
		explicitName = (
			attributes.get("name-from") == "attribute" and attributes.get("explicit-name") == "true"
		)
		supportedName = explicitName or attributes.get("name-from") == "contents"
		roles = attributes.get("xml-roles", "").split()
		if obj.role in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON):
			return supportedName and (attributes.get("tag") == "button" or "button" in roles)
		if obj.role == controlTypes.Role.TAB:
			return supportedName and "tab" in roles
		return False
	except Exception:
		return False


class MessageReview(AutoPropertyObject):
	# A mixin preserves the order of NVDA's Button and Ia2Web provider classes.
	def _get_TextInfo(self):
		nativeTextInfo = super().TextInfo
		if not isReviewTarget(self):
			return nativeTextInfo
		try:
			name = self.name
			if not isinstance(name, str) or not name.strip():
				return nativeTextInfo
			# IA2 text may contain only a badge; review the complete control label.
			if self.role in (controlTypes.Role.BUTTON, controlTypes.Role.TOGGLEBUTTON, controlTypes.Role.TAB):
				return NVDAObjectTextInfo
			text = nativeTextInfo(self, textInfos.POSITION_ALL).text
			# Embedded-object markers are not characters of the exposed message name.
			if isinstance(text, str) and not text.replace("\ufffc", "").strip():
				return NVDAObjectTextInfo
		except Exception:
			# A provider failure is not proof that its text is empty.
			pass
		return nativeTextInfo

	def _get_basicText(self):
		# Read the current exposed name to preserve privacy masking.
		if not isReviewTarget(self):
			return ""
		name = self.name
		return name if isinstance(name, str) else ""
