#!/usr/bin/env python3
import json
import sys
import time
import urllib.parse
import urllib.request

UA = "tbutcher80-lidarr-list/1.0 (MBID builder for Lidarr import lists)"

def mb_search_artist(name: str):
    # MusicBrainz search for best artist match
    q = urllib.parse.urlencode({"query": f'artist:"{name}"', "fmt": "json", "limit": 5})
    url = f"https://musicbrainz.org/ws/2/artist/?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))

    artists = data.get("artists") or []
    if not artists:
        return None

    # Pick highest score; if ties, first.
    best = max(artists, key=lambda a: a.get("score", 0))
    return {
        "query": name,
        "mbid": best.get("id"),
        "name": best.get("name"),
        "score": best.get("score"),
        "disambiguation": best.get("disambiguation", ""),
        "country": best.get("country", ""),
        "type": best.get("type", ""),
    }

def main():
    if len(sys.argv) != 3:
        print("Usage: mbidify.py <input_names.txt> <output_mbids.txt>", file=sys.stderr)
        sys.exit(2)

    inp, outp = sys.argv[1], sys.argv[2]

    names = []
    with open(inp, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                names.append(s)

    results = []
    misses = []
    for i, name in enumerate(names, 1):
        try:
            res = mb_search_artist(name)
        except Exception as e:
            misses.append((name, f"ERROR: {e}"))
            res = None

        if not res or not res.get("mbid"):
            misses.append((name, "NO MATCH"))
        else:
            results.append(res)

        # Rate limit friendliness
        time.sleep(1.0)

    # Write MBID-only file for Lidarr
    with open(outp, "w", encoding="utf-8") as f:
        for r in results:
            f.write(r["mbid"].strip() + "\n")

    # Write a debug mapping you can review
    debug_csv = outp.replace(".txt", "_debug.tsv")
    with open(debug_csv, "w", encoding="utf-8") as f:
        f.write("query\tmbid\tname\tscore\ttype\tcountry\tdisambiguation\n")
        for r in results:
            f.write(
                f'{r["query"]}\t{r["mbid"]}\t{r["name"]}\t{r["score"]}\t'
                f'{r["type"]}\t{r["country"]}\t{r["disambiguation"]}\n'
            )

    print(f"Wrote {len(results)} MBIDs to {outp}")
    print(f"Wrote debug map to {debug_csv}")

    if misses:
        print("\nNeeds review:")
        for n, why in misses:
            print(f"- {n}: {why}")

if __name__ == "__main__":
    main()
