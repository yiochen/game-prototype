from pathlib import Path
p=Path(__file__).resolve().parents[4];base=p/'reviews/round-03-independent';d=base/'resources/drivers'
for name in ['freeze_used.py','inspect_replay.py','consumer.html','consumer.mjs','probe_runtimes.mjs','analyze_evidence.py','audit_collar_temporal.py','make_collar_context.py','audit_residuals.py','seal_review.py']:
 src=p/'reviews/round-02-independent/resources/drivers'/name
 text=src.read_text().replace('round-02','round-03').replace('round02','round03').replace('Round02','Round03')
 (d/name).write_text(text)
