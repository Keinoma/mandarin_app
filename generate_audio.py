"""Génère un mp3 par phrase à partir de data.json et ajoute le champ "audio".

Usage :  python generate_audio.py
- Les mp3 déjà générés ne sont pas refaits (nom basé sur le texte chinois).
- Si tu modifies une phrase, un nouveau mp3 est créé automatiquement.
"""
import asyncio
import hashlib
import json
from pathlib import Path

import edge_tts

VOICE = "zh-CN-XiaoxiaoNeural"   # autres choix : zh-CN-YunxiNeural (homme), zh-CN-XiaoyiNeural
RATE = "-10%"                    # un peu plus lent pour apprendre ("+0%" = vitesse normale)
DATA = Path("data.json")
AUDIO_DIR = Path("audio")


def filename(hanzi: str) -> str:
    return hashlib.sha1((hanzi + VOICE + RATE).encode("utf-8")).hexdigest()[:12] + ".mp3"


async def make(text: str, path: Path):
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
            return
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  nouvel essai ({e})")
            await asyncio.sleep(2)


async def main():
    items = json.loads(DATA.read_text(encoding="utf-8"))
    AUDIO_DIR.mkdir(exist_ok=True)
    used, created = set(), 0

    for i, item in enumerate(items, 1):
        name = filename(item["hanzi"])
        path = AUDIO_DIR / name
        used.add(name)
        if not path.exists() or path.stat().st_size == 0:
            print(f"[{i}/{len(items)}] {item['hanzi']}")
            await make(item["hanzi"], path)
            created += 1
        item["audio"] = f"audio/{name}"

    DATA.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    # supprime les mp3 qui ne correspondent plus à aucune phrase
    removed = 0
    for f in AUDIO_DIR.glob("*.mp3"):
        if f.name not in used:
            f.unlink()
            removed += 1

    print(f"Terminé : {created} créé(s), {removed} supprimé(s), {len(items)} phrases au total.")


asyncio.run(main())