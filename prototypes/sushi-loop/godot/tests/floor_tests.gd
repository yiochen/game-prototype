extends SceneTree
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/floor_book.gd")
var count:=0
var failures:Array[String]=[]
func check(value:bool,message:String)->void:
	count+=1
	if not value:failures.append(message);printerr("FAIL: "+message)
func _initialize()->void:call_deferred("run")
func purchase(s)->Dictionary:
	var data:Dictionary=s.snapshot().floor_styles
	return s.command({"type":"floor_purchase","offer_id":"floor:"+str(data.offer),"expected_sequence":data.purchase_sequence,"rotation":data.rotation})
func run()->void:
	var thin:Array=[]
	for t in Book.stroke_samples(Vector2(2.01,3.99),Vector2(6.01,4.01)):
		var point:=Vector2(2.01,3.99).lerp(Vector2(6.01,4.01),t)
		thin.append(Vector2i(floori(point.x),floori(point.y)))
	check(Vector2i(4,3) in thin and Vector2i(4,4) in thin,"stroke traversal includes both cells beside a grazed corner")
	var seen:Dictionary={};var none:=false;var selected_seed:=0
	for seed_value in range(1,201):
		var candidate=Session.new_session(seed_value)
		var offer:String=candidate.snapshot().floor_styles.offer
		if offer.is_empty():none=true
		else:seen[offer]=true;selected_seed=seed_value
	check(none and seen.size()==6,"optional seeded stock has no guarantee and all six styles eligible immediately")
	var s=Session.new_session(selected_seed,{"starting_coins":100000})
	var first:Dictionary=s.save_data()
	check(not purchase(s).ok and s.save_data()==first,"Live rejects purchase without mutation")
	s.command({"type":"set_mode","mode":"edit"});s.command({"type":"editor_layer","layer":"floor"})
	var before_inventory:Array=s.snapshot().inventory
	var before:Dictionary=GameSession.flat_view(s.save_data());var offered:String=s.snapshot().floor_styles.offer
	var request:Dictionary={"type":"floor_purchase","offer_id":"floor:"+offered,"expected_sequence":0,"rotation":0}
	check(s.command(request).ok,"one affordable floor style unlock")
	var data:Dictionary=s.snapshot()
	check(data.coins==100000-Book.style(offered).cost and data.floor_styles.owned==[offered,"cream"],"single debit, newest first, original last")
	check(data.inventory==before_inventory and data.shop.purchase_sequence==before.state.shop.purchase_sequence,"unlimited unlock never grants finite tile inventory")
	var bought:Dictionary=GameSession.flat_view(s.save_data())
	check(not s.command(request).ok and GameSession.flat_view(s.save_data())==bought,"replayed purchase does not debit twice")
	check(data.shop.offers[0].owned and data.shop.offers[0].style_id==offered,"purchased offer stays Owned until rotation")
	check(s.command({"type":"floor_select","style_id":offered}).ok,"select an owned brush")
	var selected:Dictionary=s.save_data()
	check(s.advance(3601).is_empty() and s.save_data()==selected,"Edit pauses rotation/service/time/RNG")
	var paint:=s.command({"type":"floor_paint","cells":[{"x":2,"y":6},{"x":3,"y":7},{"x":7,"y":3},{"x":8,"y":7}]})
	check(paint.ok and paint.changed and paint.blocked,"stroke paints under objects/dock and skips trash")
	data=s.snapshot()
	check(data.floor_styles.painted.get("2,6")==offered and data.floor_styles.painted.get("3,7")==offered and data.floor_styles.painted.get("8,7")==offered and not data.floor_styles.painted.has("7,3"),"trash mask blocks only covered cells")
	check(data.coins==bought.state.coins and data.inventory==before_inventory,"painting consumes no currency or items")
	var saved:Dictionary=s.save_data()
	check(not s.command({"type":"floor_paint","cells":[{"x":0,"y":5},{"x":-1,"y":5}]}).ok and s.save_data()==saved,"invalid batch rejected atomically")
	s.command({"type":"editor_toggle_tray"});s.command({"type":"set_camera","x":2,"y":1})
	check(s.snapshot().editor.floor_brush==offered,"brush survives tray collapse and panning")
	var restored=Session.new();check(restored.restore(JSON.parse_string(JSON.stringify(s.save_data()))),"JSON painted collection restores")
	check(restored.snapshot().floor_styles.painted==data.floor_styles.painted and restored.snapshot().floor_styles.owned==data.floor_styles.owned,"painted cells and collection persist")
	check(restored.snapshot().editor.get("floor_brush","")=="","reopened Floor has no armed brush")
	check(s.command({"type":"clear_trash","id":"sofa-west"}).ok,"clear a neighboring trash object")
	check(s.command({"type":"floor_paint","cells":[{"x":7,"y":3}]}).changed,"cleared floor becomes paintable")
	s.command({"type":"floor_select","style_id":"cream"});s.command({"type":"floor_paint","cells":[{"x":2,"y":6}]})
	check(not s.snapshot().floor_styles.painted.has("2,6"),"free original brush restores original tile")
	for kind in ["future","unknown","duplicate","bad_cell","unowned","brush"]:
		var corrupt:Dictionary=GameSession.flat_view(s.save_data())
		match kind:
			"future":corrupt.version=99
			"unknown":corrupt.state.floor_styles.owned[0]="missing"
			"duplicate":corrupt.state.floor_styles.owned.append("cream")
			"bad_cell":corrupt.state.floor_styles.painted["-1,3"]=offered
			"unowned":corrupt.state.floor_styles.painted["0,3"]="missing"
			"brush":corrupt.state.editor.floor_brush="missing"
		var guard:Dictionary=restored.save_data()
		check(not restored.restore(corrupt) and restored.save_data()==guard,"invalid "+kind+" restore is atomic")
	var poor=Session.new_session(selected_seed,{"starting_coins":0});poor.command({"type":"set_mode","mode":"edit"})
	var unchanged:Dictionary=poor.save_data();check(not purchase(poor).ok and poor.save_data()==unchanged,"unaffordable style changes nothing")
	# The ended-expedition lifecycle invokes a replay-safe stock refresh.
	s.command({"type":"set_entrance_open","open":false});s.command({"type":"set_mode","mode":"live"});s.advance(3601)
	check(s.snapshot().floor_styles.rotation==0,"ordinary Live time never refreshes expedition-return stock")
	check(s.command({"type":"floor_refresh","expected_rotation":0}).ok and s.snapshot().floor_styles.rotation==1 and s.snapshot().floor_styles.offer!=offered,"ended-expedition refresh excludes owned styles")
	var rotation:Dictionary=s.save_data();check(not s.command({"type":"floor_refresh","expected_rotation":0}).ok and s.save_data()==rotation,"duplicate expedition-return token cannot reroll stock")
	check(s.save_data().random_state==before.random_state,"floor operations never consume restaurant service RNG with entrance closed")
	print("Floor rules: %s checks, %s failures"%[count,failures.size()]);quit(0 if failures.is_empty() else 1)
