class_name RestaurantAudio
extends Node
## Presentation only: audio never reads or advances the game session.

const AUDIO_PATH := "res://assets/audio/"
const VOICE_COUNT := 6
const COOLDOWN_MS := {"click": 75, "cook": 170, "load": 100, "coin": 140, "tea_ideal": 300, "tea_good": 300, "tea_soft": 300, "tea_splash": 300}
const CUE_VOLUME_DB := {"click": -12.0, "cook": -15.0, "load": -14.0, "coin": -12.0, "tea_ideal": -11.0, "tea_good": -11.0, "tea_soft": -13.0, "tea_splash": -12.0}
const ALIASES := {"ui": "click", "cooking": "cook", "prepared": "cook", "loading": "load", "loaded": "load", "sale": "coin", "tip": "coin"}

var music_volume_db := -16.0
var effects_volume_db := 0.0
var _muted := false
var _backgrounded := false
var _focused := true
var _music: AudioStreamPlayer
var _voices: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _last_cue: Dictionary = {}
var _last_any_cue := -1000
var _pour: AudioStreamPlayer

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for key in COOLDOWN_MS:
		_streams[key] = load(AUDIO_PATH + str(key) + ".wav")
	for index in range(VOICE_COUNT):
		var player := AudioStreamPlayer.new()
		player.name = "Cue%s" % index
		add_child(player)
		_voices.append(player)
	# #62: the tea stream, looped while the pour sheet is open; set_pour() follows the flow.
	var stream := load(AUDIO_PATH + "tea_pour.wav") as AudioStreamWAV
	if stream != null:
		var looped := stream.duplicate() as AudioStreamWAV
		looped.loop_mode = AudioStreamWAV.LOOP_FORWARD
		looped.loop_begin = 0
		looped.loop_end = int(round(looped.get_length() * looped.mix_rate))
		_pour = AudioStreamPlayer.new()
		_pour.name = "TeaPour"
		_pour.stream = looped
		add_child(_pour)
	var source := load(AUDIO_PATH + "harbor_cafe.wav") as AudioStreamWAV
	if source != null:
		var loop := source.duplicate() as AudioStreamWAV
		loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
		loop.loop_begin = 0
		loop.loop_end = int(round(loop.get_length() * loop.mix_rate))
		_music = AudioStreamPlayer.new()
		_music.name = "HarborCafe"
		_music.stream = loop
		_music.volume_db = music_volume_db
		add_child(_music)
		_music.play()
	_sync_pause()

func play_cue(name: String) -> void:
	if _muted or _backgrounded or not _focused or not is_inside_tree():
		return
	var cue: String = ALIASES.get(name, name)
	if not _streams.has(cue):
		return
	var now := Time.get_ticks_msec()
	# Ignore bursts rather than queueing obsolete sounds after a large time step.
	if (cue != "coin" and now - _last_any_cue < 35) or now - int(_last_cue.get(cue, -1000)) < int(COOLDOWN_MS[cue]):
		return
	for voice in _voices:
		if not voice.playing:
			_last_cue[cue] = now
			_last_any_cue = now
			voice.stream = _streams[cue]
			voice.volume_db = float(CUE_VOLUME_DB[cue]) + effects_volume_db
			voice.play()
			return

## Tea stream loudness for a flow share in [0, 1]; 0 stops it.
func set_pour(flow: float) -> void:
	if _pour == null: return
	var audible := flow > 0.001 and not (_muted or _backgrounded or not _focused) and is_inside_tree()
	if not audible:
		if _pour.playing: _pour.stop()
		return
	_pour.volume_db = linear_to_db(0.25 + 0.75 * clampf(flow, 0.0, 1.0)) - 14.0 + effects_volume_db
	_pour.pitch_scale = 0.9 + 0.25 * clampf(flow, 0.0, 1.0)
	if not _pour.playing: _pour.play()

func set_muted(value: bool) -> void:
	_muted = value
	_sync_pause()

func set_backgrounded(value: bool) -> void:
	_backgrounded = value
	_sync_pause()

func _sync_pause() -> void:
	var quiet := _muted or _backgrounded or not _focused
	if quiet and _pour != null and _pour.playing: _pour.stop()
	if _music != null:
		_music.stream_paused = quiet
	# Never resume stale coin/cooking/UI sounds after returning to the app.
	if quiet:
		for voice in _voices:
			voice.stop()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		set_backgrounded(true)
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		set_backgrounded(false)
	elif what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		_focused = false
		_sync_pause()
	elif what == NOTIFICATION_APPLICATION_FOCUS_IN:
		_focused = true
		_sync_pause()

func _exit_tree() -> void:
	if _music != null:
		_music.stop()
	for voice in _voices:
		voice.stop()
