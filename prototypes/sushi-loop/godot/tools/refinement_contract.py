"""Read exact independently approved refinement artifacts using only stdlib."""
from pathlib import Path
import json

from verify_editor_ui import require, sha


def read(path):
    return json.loads(Path(path).read_text())


def contained(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    require(path.is_relative_to(root), 'Refinement artifact escapes the prototype')
    return path


def verified_packet(prototype, packet_path, packet_sha, review_path, review_sha, asset):
    """Verify the receipt, independent verdict and every sealed artifact byte."""
    packet_path = contained(prototype, packet_path)
    review_path = contained(prototype, review_path)
    require(sha(packet_path) == packet_sha and sha(review_path) == review_sha,
            f'Refinement packet/review changed: {asset}')
    packet, review = read(packet_path), read(review_path)
    require(packet.get('schemaVersion') == 1 and packet.get('asset') == asset,
            f'Refinement packet identity changed: {asset}')
    require(review.get('asset') == asset and review.get('verdict') == 'approve'
            and review.get('candidatePacketSHA256') == packet_sha
            and review.get('blockers') == [], f'Refinement is not approved: {asset}')
    inspected = review.get('inspectedFiles')
    require(isinstance(inspected, list) and inspected
            and all(isinstance(path, str) and path for path in inspected),
            f'Refinement inspection receipt is incomplete: {asset}')
    bound = {}
    for group in ('files', 'candidateRenders', 'previews'):
        require(isinstance(packet.get(group), dict) and packet[group],
                f'Refinement artifact group is missing: {asset}/{group}')
        for record in packet[group].values():
            path = contained(prototype, packet_path.parent / record['path'])
            expected = record['sha256']
            if path in bound:
                require(bound[path] == expected, 'Conflicting refinement artifact hashes')
            else:
                require(sha(path) == expected, f'Refinement artifact changed: {path.name}')
                bound[path] = expected
    return packet, bound
