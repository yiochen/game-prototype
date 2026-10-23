from pathlib import Path
p=Path(__file__).resolve().parents[4];d=p/'reviews/round-05-independent/resources/drivers'
for name in ['freeze_used.py','inspect_replay.py','consumer.html','consumer.mjs','probe_runtimes.mjs','analyze_evidence.py','audit_collar_temporal.py','make_collar_context.py','audit_residuals.py','audit_geometry_padding.py','audit_comparison_padding.py','audit_delivery.py','audit_controls_gates.py','freeze_prior_comparison.py','compare_finish.py']:
 src=p/'reviews/round-04-independent/resources/drivers'/name
 text=src.read_text().replace('round-04','round-05').replace('round04','round05').replace('Round04','Round05')
 (d/name).write_text(text)
