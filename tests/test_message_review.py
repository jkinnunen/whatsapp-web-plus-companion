"""Exercise fallback selection with NVDA provider doubles, not a running NVDA."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class NativeTextInfo:
	def __init__(self, obj, position):
		if obj.providerError:
			raise RuntimeError("Provider disappeared")
		self.text = obj.nativeText


class GenericTextInfo:
	pass


class AutoPropertyType(type):
	def __new__(cls, name, bases, namespace):
		for key, value in tuple(namespace.items()):
			if key.startswith("_get_"):
				namespace[key[5:]] = property(value)
		return super().__new__(cls, name, bases, namespace)


class AutoPropertyObject(metaclass=AutoPropertyType):
	pass


class Ia2Web(AutoPropertyObject):
	TextInfo = NativeTextInfo
	basicText = "native basic text"


CONTROL = types.SimpleNamespace(
	Role=types.SimpleNamespace(TABLECELL="cell", BUTTON="button", TOGGLEBUTTON="toggle", TAB="tab"),
	State=types.SimpleNamespace(FOCUSABLE="focusable", EDITABLE="editable", PROTECTED="protected"),
)
spec = importlib.util.spec_from_file_location(
	"messageReviewUnderTest",
	Path(__file__).parents[1] / "addon/appModules/wwpMessageReview.py",
)
review = importlib.util.module_from_spec(spec)
with patch.dict(
	sys.modules,
	{
		"controlTypes": CONTROL,
		"baseObject": types.SimpleNamespace(AutoPropertyObject=AutoPropertyObject),
		"textInfos": types.SimpleNamespace(POSITION_ALL="all"),
		"NVDAObjects": types.SimpleNamespace(NVDAObjectTextInfo=GenericTextInfo),
		"NVDAObjects.IAccessible.ia2Web": types.SimpleNamespace(Ia2Web=Ia2Web),
	},
):
	spec.loader.exec_module(review)


class ReviewObject(review.MessageReview, Ia2Web):
	pass


def message():
	obj = ReviewObject()
	obj.windowClassName = "Chrome_RenderWidgetHostHWND"
	obj.role = "cell"
	obj.states = {"focusable"}
	obj.IA2Attributes = {
		"tag": "div",
		"xml-roles": "gridcell",
		"class": "obfuscated focusable-list-item other",
		"name-from": "attribute",
		"explicit-name": "true",
	}
	obj.name = "Message with emoji 🎟️ and\nsecond line"
	obj.nativeText = ""
	obj.providerError = False
	return obj


class MessageReviewTests(unittest.TestCase):
	def controlExamples(self):
		chat = message()
		chat.IA2Attributes.pop("class")
		chat.name = "Example group, voice message, muted"
		chat.states.update({"selectable", "selected"})
		toggle = message()
		toggle.role = "toggle"
		toggle.name = "Chats"
		toggle.states.add("pressed")
		toggle.IA2Attributes = {"tag": "button", "name-from": "attribute", "explicit-name": "true"}
		tab = message()
		tab.role = "tab"
		tab.name = "All"
		tab.states.update({"selectable", "selected"})
		tab.IA2Attributes = {"tag": "button", "xml-roles": "tab", "name-from": "contents"}
		return (chat, toggle, tab)

	def test_chat_toggle_and_tab_review_preserves_semantics(self):
		for obj in self.controlExamples():
			with self.subTest(role=obj.role):
				originalRole, originalStates = obj.role, obj.states.copy()
				self.assertTrue(review.isReviewTarget(obj))
				self.assertTrue(review.isReviewTarget(types.SimpleNamespace(**vars(obj)), [Ia2Web]))
				self.assertIs(obj.TextInfo, GenericTextInfo)
				self.assertEqual(obj.basicText, obj.name)
				self.assertEqual((obj.role, obj.states), (originalRole, originalStates))
				obj.states.difference_update({"selected", "pressed"})
				obj.name = "Nama baru"
				self.assertEqual(obj.basicText, "Nama baru")
				self.assertIs(obj.TextInfo, GenericTextInfo)

	def test_controls_use_names_while_chat_cells_keep_native_text(self):
		for obj in self.controlExamples():
			expected = NativeTextInfo if obj.role == "cell" else GenericTextInfo
			obj.nativeText = "Existing native text"
			self.assertIs(obj.TextInfo, expected)
			obj.nativeText = ""
			obj.providerError = True
			self.assertIs(obj.TextInfo, expected)
			obj.providerError = False
			obj.name = ""
			self.assertIs(obj.TextInfo, NativeTextInfo)

	def test_new_controls_exclude_editable_protected_and_recycled_objects(self):
		for state in ("editable", "protected"):
			for obj in self.controlExamples():
				obj.states.add(state)
				self.assertIs(obj.TextInfo, NativeTextInfo)
				self.assertEqual(obj.basicText, "")
		for obj in self.controlExamples():
			obj.role = "edit"
			self.assertIs(obj.TextInfo, NativeTextInfo)
			self.assertEqual(obj.basicText, "")

	def test_tab_requires_matching_role_markup_and_name_source(self):
		for key in ("xml-roles", "name-from"):
			obj = self.controlExamples()[2]
			del obj.IA2Attributes[key]
			self.assertFalse(review.isReviewTarget(obj))
		obj = self.controlExamples()[2]
		obj.IA2Attributes.update({"name-from": "attribute", "explicit-name": "true"})
		self.assertTrue(review.isReviewTarget(obj))
		obj.IA2Attributes.pop("explicit-name")
		self.assertFalse(review.isReviewTarget(obj))

	def test_toggle_and_tab_provider_role_and_action_remain_inherited(self):
		class ControlProvider(Ia2Web):
			def _get_role(self):
				return self.nativeRole

			def doAction(self):
				self.actionCount += 1
				self.states.symmetric_difference_update({self.actionState})

		class ControlObject(review.MessageReview, ControlProvider):
			pass

		for example, state in zip(self.controlExamples()[1:], ("pressed", "selected")):
			obj = ControlObject()
			obj.__dict__.update(vars(example))
			obj.nativeRole = example.role
			obj.actionState = state
			obj.actionCount = 0
			self.assertEqual(obj.role, example.role)
			self.assertIs(obj.TextInfo, GenericTextInfo)
			obj.doAction()
			self.assertEqual(obj.actionCount, 1)
			self.assertNotIn(state, obj.states)
			self.assertEqual(obj.basicText, example.name)
			obj.nativeText = "Provider text"
			self.assertIs(obj.TextInfo, GenericTextInfo)

	def test_named_html_button_reviews_complete_name(self):
		obj = message()
		obj.role = "button"
		obj.name = "New chat"
		obj.IA2Attributes = {"tag": "button", "name-from": "attribute", "explicit-name": "true"}
		self.assertTrue(review.isReviewTarget(obj))
		self.assertFalse(review.isNamedGridCell(obj))
		self.assertIs(obj.TextInfo, GenericTextInfo)
		self.assertEqual(obj.basicText, "New chat")
		obj.nativeText = "Native button text"
		self.assertIs(obj.TextInfo, GenericTextInfo)
		obj.nativeText = ""
		obj.providerError = True
		self.assertIs(obj.TextInfo, GenericTextInfo)

	def test_unread_tab_reviews_label_and_badge_together(self):
		obj = self.controlExamples()[2]
		obj.name = "Unread 8"
		for nativeText in ("8", "\ufffc8", "Unread", "Unread 8", "", "\u200b"):
			with self.subTest(nativeText=nativeText):
				obj.nativeText = nativeText
				self.assertIs(obj.TextInfo, GenericTextInfo)
				self.assertEqual(obj.basicText, "Unread 8")
		obj.name = "Unread 9"
		self.assertEqual(obj.basicText, "Unread 9")
		obj.states.add("editable")
		self.assertIs(obj.TextInfo, NativeTextInfo)
		self.assertEqual(obj.basicText, "")

	def test_named_control_review_does_not_probe_native_text(self):
		for obj in self.controlExamples()[1:]:
			with patch.object(
				NativeTextInfo,
				"__init__",
				side_effect=AssertionError("Must not probe"),
			) as probe:
				self.assertIs(obj.TextInfo, GenericTextInfo)
				probe.assert_not_called()

	def test_semantic_buttons_and_tabs_do_not_require_native_html_tag(self):
		for role, xmlRole in (("button", "button"), ("toggle", "button"), ("tab", "tab")):
			for tag in ("div", "span", "button"):
				with self.subTest(role=role, tag=tag):
					obj = message()
					obj.role = role
					obj.IA2Attributes = {"tag": tag, "xml-roles": xmlRole, "name-from": "contents"}
					obj.name = "Example preview, sender, today"
					obj.nativeText = "partial preview"
					self.assertTrue(review.isReviewTarget(types.SimpleNamespace(**vars(obj)), [Ia2Web]))
					self.assertIs(obj.TextInfo, GenericTextInfo)
					self.assertEqual(obj.basicText, obj.name)
					obj.name = "Preview hidden"
					self.assertEqual(obj.basicText, "Preview hidden")
					obj.states.add("editable")
					self.assertIs(obj.TextInfo, NativeTextInfo)

	def test_plain_div_and_conflicting_semantics_remain_native(self):
		for role, xmlRole in (("button", ""), ("button", "tab"), ("tab", "button"), ("edit", "button")):
			obj = message()
			obj.role = role
			obj.IA2Attributes = {"tag": "div", "xml-roles": xmlRole, "name-from": "contents"}
			self.assertIs(obj.TextInfo, NativeTextInfo)
			self.assertEqual(obj.basicText, "")

	def test_button_matching_before_overlay_and_exclusions(self):
		obj = types.SimpleNamespace(**vars(message()))
		obj.role = "button"
		obj.IA2Attributes = {"tag": "button", "name-from": "attribute", "explicit-name": "true"}
		self.assertTrue(review.isReviewTarget(obj, [Ia2Web]))
		self.assertFalse(review.isReviewTarget(obj))
		for state in ("editable", "protected"):
			obj.states = {state}
			self.assertFalse(review.isReviewTarget(obj, [Ia2Web]))
		obj.states = set()
		for key in tuple(obj.IA2Attributes):
			original = obj.IA2Attributes.pop(key)
			self.assertFalse(review.isReviewTarget(obj, [Ia2Web]))
			obj.IA2Attributes[key] = original
		obj.IA2Attributes["tag"] = "input"
		self.assertFalse(review.isReviewTarget(obj, [Ia2Web]))

	def test_mixin_preserves_button_provider_order_and_activation(self):
		class Button:
			TextInfo = NativeTextInfo

			def doAction(self):
				self.activated = True

		class ButtonObject(review.MessageReview, Button, Ia2Web):
			pass

		obj = ButtonObject()
		obj.__dict__.update(vars(message()))
		obj.role = "button"
		obj.IA2Attributes = {"tag": "button", "name-from": "attribute", "explicit-name": "true"}
		self.assertLess(ButtonObject.__mro__.index(Button), ButtonObject.__mro__.index(Ia2Web))
		self.assertIs(obj.TextInfo, GenericTextInfo)
		obj.doAction()
		self.assertTrue(obj.activated)
		obj.name = ""
		self.assertIs(obj.TextInfo, NativeTextInfo)
		obj.name = "New chat"
		obj.states.add("protected")
		self.assertEqual(obj.basicText, "")

	def test_raw_provider_matches_before_overlay_classes_are_applied(self):
		obj = types.SimpleNamespace(**vars(message()))
		self.assertFalse(review.isNamedGridCell(obj))
		self.assertTrue(review.isNamedGridCell(obj, [Ia2Web]))
		self.assertFalse(review.isNamedGridCell(obj, [object]))
		# Ia2Web adds FOCUSABLE for gridcells after overlay selection.
		obj.states = set()
		self.assertTrue(review.isNamedGridCell(obj, [Ia2Web]))

	def test_observed_cell_gets_generic_review_without_requiring_focus(self):
		obj = message()
		self.assertTrue(review.isNamedGridCell(obj))
		self.assertIs(obj.TextInfo, GenericTextInfo)

	def test_empty_native_text_uses_exposed_name(self):
		for text in ("", " \n\t", "\ufffc", " \ufffc\n"):
			with self.subTest(text=text):
				obj = message()
				obj.nativeText = text
				self.assertIs(obj.TextInfo, GenericTextInfo)
				self.assertEqual(obj.basicText, obj.name)

	def test_real_native_text_wins(self):
		for text in ("Native message", "\ufffc usable text", "0"):
			obj = message()
			obj.nativeText = text
			self.assertIs(obj.TextInfo, NativeTextInfo)

	def test_provider_failure_is_not_treated_as_empty(self):
		obj = message()
		obj.providerError = True
		self.assertIs(obj.TextInfo, NativeTextInfo)

	def test_empty_or_invalid_name_keeps_native(self):
		for name in (None, "", " \n", 12):
			obj = message()
			obj.name = name
			self.assertIs(obj.TextInfo, NativeTextInfo)

	def test_name_only_and_current_privacy_mask(self):
		obj = message()
		obj.value = "hidden value"
		obj.description = "hidden description"
		self.assertEqual(obj.basicText, obj.name)
		obj.name = "Message hidden"
		self.assertEqual(obj.basicText, "Message hidden")

	def test_other_controls_and_recycled_cells_keep_native(self):
		for field, value in (
			("role", "button"),
			("windowClassName", "other"),
			("states", {"focusable", "editable"}),
			("states", {"focusable", "protected"}),
		):
			with self.subTest(field=field, value=value):
				obj = message()
				setattr(obj, field, value)
				self.assertFalse(review.isNamedGridCell(obj))
				self.assertIs(obj.TextInfo, NativeTextInfo)
				self.assertEqual(obj.basicText, "")

	def test_missing_identity_attributes_do_not_match(self):
		for key in ("tag", "xml-roles", "name-from", "explicit-name"):
			obj = message()
			del obj.IA2Attributes[key]
			self.assertFalse(review.isNamedGridCell(obj), key)

	def test_unavailable_provider_does_not_match(self):
		self.assertFalse(review.isNamedGridCell(object()))
		obj = message()
		obj.IA2Attributes = None
		self.assertFalse(review.isNamedGridCell(obj))
