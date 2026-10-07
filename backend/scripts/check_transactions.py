"""Read-only database readiness check. Uses local deployment environment; never prints secrets."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

async def main():
    from database import db, client
    try:
        info = await db.command('hello')
        ok = bool(info.get('setName') or info.get('msg') == 'isdbgrid') and info.get('logicalSessionTimeoutMinutes') is not None and info.get('maxWireVersion', 0) >= 9
        print('GATI: MongoDB mbështet transaksione.' if ok else 'JO GATI: kërkohet MongoDB Atlas/replica set. Mos publikoni këtë fazë pa e konfiguruar.')
        return 0 if ok else 2
    except Exception:
        print('Lidhja nuk u verifikua. Kontrolloni konfigurimin dhe lejet e databazës; nuk u ndryshuan të dhëna.')
        return 3
    finally:
        client.close()

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
