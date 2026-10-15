# -*- coding: utf-8 -*-
"""
make_keys.py
Μετατρέπει τις λέξεις-κλειδιά σε κατακερματισμένη (hashed) μορφή, ώστε να μπορούν
να δημοσιευτούν στο GitHub χωρίς να είναι αναγνώσιμες.

Χρήση:
    1. Γράψτε τις λέξεις-κλειδιά στο λεξικό KEYWORDS παρακάτω, κανονικά στα ελληνικά.
    2. Τρέξτε:  python3 make_keys.py
    3. Αντιγράψτε την έξοδο στο course_utils.py, στη θέση του KLEIDIA.

ΜΗΝ ανεβάσετε ΑΥΤΟ το αρχείο στο GitHub - περιέχει τις λέξεις σε καθαρή μορφή.
"""

import hashlib, unicodedata

SALT = "UoI-pandas-2026"          # ίδιο με αυτό του course_utils.py

# --------------------------------------------------------------------------
# Οι λέξεις-κλειδιά, σε καθαρή μορφή. Κάθε εσωτερική λίστα είναι ΜΙΑ έννοια·
# μέσα της μπαίνουν συνώνυμα ή παραλλαγές.
# --------------------------------------------------------------------------
KEYWORDS = {
    1: [["κυτταρόπλασμ"], ["πρωτε"], ["σύνθεσ"]],
    2: [["κυτταρόπλασμ"], ["DNA"], ["πληροφορ"]],
    3: [["φθορ"], ["γενετικ"], ["μικροσκ"]],
    4: [["μέσος όρ", "μέσο όρ", "μέσου όρ", "μέσων όρ", "μ.ο", "mean", "average"],
        ["απόκλισ", "standard deviation", "τυπική απ"]],
}


def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ς", "σ")


def _h(s):
    return hashlib.sha256((SALT + s).encode("utf-8")).hexdigest()[:16]


def main():
    print("KLEIDIA = {")
    for n in sorted(KEYWORDS):
        print(f"    {n}: [")
        for omada in KEYWORDS[n]:
            items = []
            for w in omada:
                k = _norm(w)
                items.append(f'"{len(k)}:{_h(k)}"')
            print("        [" + ", ".join(items) + "],")
        print("    ],")
    print("}")

    total = sum(len(o) for g in KEYWORDS.values() for o in g)
    print(f"\n# {total} λέξεις-κλειδιά, {sum(len(g) for g in KEYWORDS.values())} έννοιες")


if __name__ == "__main__":
    main()
