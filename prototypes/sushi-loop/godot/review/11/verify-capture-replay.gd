extends SceneTree
## Confirm the final rules reproduce the captured scene states and movie events.
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []
func _initialize() -> void:
	for label in ["phone", "wide", "landscape"]:
		var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://review/11/" + label + "/manifest.json"))
		for record in data.screens:
			var session = Session.new_session(41)
			session.advance(float(record.session.elapsed))
			check(_same(session.snapshot(), record.session), label + "/" + record.name)
	var movie: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://review/11/motion.json"))
	var session = Session.new_session(41)
	var events: Array = session.advance(float(movie.seconds))
	check(_same(session.snapshot(), movie.final_state), "movie final state")
	check(_same(events, movie.events), "movie complete event history")
	if failures.is_empty():
		print("PASS: %s final-source capture replay checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)
func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures.append(label)
func _same(a: Variant, b: Variant) -> bool:
	if (a is int or a is float) and (b is int or b is float): return absf(float(a) - float(b)) < 0.0000001
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
