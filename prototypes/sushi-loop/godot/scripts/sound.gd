extends Node

var effects := true
var music := true
var current := ""
var player: AudioStreamPlayer
var streams: Dictionary = {}
var voices: Array[AudioStreamPlayer] = []

func _ready() -> void:
	player = AudioStreamPlayer.new()
	player.volume_db = -15
	add_child(player)
	player.finished.connect(func():
		if music: player.play())
	for i in 8:
		var voice := AudioStreamPlayer.new()
		voice.volume_db = -8
		add_child(voice)
		voices.append(voice)

func stream(id: String) -> AudioStream:
	if not streams.has(id):
		var path := "res://assets/audio/" + id + ".wav"
		if not ResourceLoader.exists(path):
			path = "res://assets/" + id + ".wav"
		if ResourceLoader.exists(path):
			streams[id] = load(path)
			if id in ["restaurant","ocean"] and streams[id] is AudioStreamWAV:
				streams[id].loop_mode = AudioStreamWAV.LOOP_FORWARD
				streams[id].loop_begin = 0
				streams[id].loop_end = 352800
	return streams.get(id)

func play(id: String) -> void:
	if not effects: return
	var audio := stream(id)
	if audio == null: return
	for voice in voices:
		if not voice.playing:
			voice.stream = audio
			voice.pitch_scale = randf_range(0.96, 1.04)
			voice.play()
			return

func ambience(id: String) -> void:
	if current == id and player.playing == music: return
	current = id
	player.stop()
	player.stream = stream(id)
	if music and player.stream: player.play()

func configure(sfx: bool, songs: bool) -> void:
	effects = sfx
	music = songs
	ambience(current)
