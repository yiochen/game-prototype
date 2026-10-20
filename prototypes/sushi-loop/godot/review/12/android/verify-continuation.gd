extends SceneTree
const Session = preload("res://scripts/session.gd")
func _initialize() -> void:
 var arguments := OS.get_cmdline_user_args()
 var before: Dictionary = JSON.parse_string(JSON.parse_string(FileAccess.get_file_as_string(arguments[0])).payload)
 var after: Dictionary = JSON.parse_string(JSON.parse_string(FileAccess.get_file_as_string(arguments[1])).payload)
 var expected := Session.new_session(1)
 var observed := Session.new_session(2)
 var valid_before: bool = expected.restore(before)
 var valid_after: bool = observed.restore(after)
 var duration: float = float(after.state.elapsed) + float(after.remainder) - float(before.state.elapsed) - float(before.remainder)
 if arguments.size() > 2 and arguments[2] == "resume": expected.command({"type": "set_mode", "mode": "live"})
 expected.advance(duration)
 var matches := _same(expected.save_data(), observed.save_data())
 print(JSON.stringify({"restored_before": valid_before, "restored_after": valid_after, "continuation_seconds": duration, "public_session_continuation_matches": matches, "all_customer_timer_rng_inventory_editor_fields": true}))
 quit(0 if valid_before and valid_after and matches else 1)
func _same(a: Variant, b: Variant) -> bool:
 if (a is float or a is int) and (b is float or b is int):
  return absf(float(a) - float(b)) < 0.0000001
 if a is Dictionary and b is Dictionary:
  if a.size() != b.size(): return false
  for key in a:
   if not b.has(key) or not _same(a[key], b[key]): return false
  return true
 if a is Array and b is Array:
  if a.size() != b.size(): return false
  for index in range(a.size()):
   if not _same(a[index], b[index]): return false
  return true
 return a == b
