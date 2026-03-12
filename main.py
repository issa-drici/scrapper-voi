#!/usr/bin/env python3
"""
Point d'entrée : lance un scraper par id.
Usage: python main.py [scraper_id]
Exemple: python main.py voi_havre
"""

import argparse
import sys

from scrapers import get_scraper, list_scrapers


def main() -> int:
    scrapers_list = list_scrapers()
    ids = [s[0] for s in scrapers_list]
    parser = argparse.ArgumentParser(description="Lancer un scraper")
    parser.add_argument(
        "scraper_id",
        nargs="?",
        default=ids[0] if ids else None,
        help=f"Id du scraper (défaut: {ids[0] if ids else 'aucun'}). Disponibles: {ids}",
    )
    args = parser.parse_args()
    if args.scraper_id not in ids:
        print(f"Scraper inconnu: {args.scraper_id}. Disponibles: {ids}", file=sys.stderr)
        return 1
    scraper = get_scraper(args.scraper_id)
    scraper.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
