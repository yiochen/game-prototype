# Issue 18 · shopping bag returns to inventory

The floating bag is now an accessible Back to inventory button. It uses the existing close path, restoring the same Edit tray, category, horizontal scroll and Shop opener focus. Click, touch tap and keyboard Enter are supported. The button stays usable during purchase flights, preserving the already committed item and payment. Popup, beige rounded catalog and bag artwork remain unchanged.

Build and five model tests passed. Fifteen feature browser checks cover touch bag return, keyboard return/focus, purchasing while closing, persistence, Edit-only flow and phone/wide/landscape bounds. Narrow and wide returned-tray captures verify the purchased stool is immediately available. No native Godot changes; the prototype remains pending approval before integration.
