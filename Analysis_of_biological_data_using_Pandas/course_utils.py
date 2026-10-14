# -*- coding: utf-8 -*-
"""
course_utils.py
Βοηθητικές συναρτήσεις για το μάθημα «Στατιστική ανάλυση βιολογικών δεδομένων
με Pandas» - Πανεπιστήμιο Ιωαννίνων.

Χρήση μέσα στο notebook:

    import course_utils as cu
    cu.ONOMA = "Papadopoulou_Maria"

    cu.katagrapse(1, apantisi_1)     # έλεγχος + χρονοσήμανση
    cu.epanafora()                   # επαναφορά μετά από διακοπή
    cu.katevase_apantiseis()         # αποθήκευση και λήψη

Οι λέξεις-κλειδιά κάθε ερώτησης βρίσκονται στο λεξικό KLEIDIA παρακάτω.
"""

import os, time, pickle, unicodedata
from datetime import datetime

# --------------------------------------------------------------------------
# Όνομα φοιτητή/φοιτήτριας - ΣΥΜΠΛΗΡΩΣΤΕ ΤΟ ΠΡΙΝ ΞΕΚΙΝΗΣΕΤΕ
# --------------------------------------------------------------------------
ONOMA = ""          # π.χ. "Papadopoulou_Maria_14102027
ARXEIO = "apantiseis_timestamps.pkl"

EROTISEIS = {
    1: "Ριβοσώματα",
    2: "Χρωμόσωμα",
    3: "Μέτρηση συγκέντρωσης πρωτεΐνης",
    4: "Δύο δημοφιλή στατιστικά",
}

# Κάθε "omada" είναι μία έννοια· μέσα της βρίσκονται συνώνυμα. Αρκεί να
# εντοπιστεί ΜΙΑ έννοια για να καταγραφεί η απάντηση (ανεκτικός έλεγχος) -
# το πλήρες κείμενο αποθηκεύεται ούτως ή άλλως για έλεγχο από τον διδάσκοντα.
KLEIDIA = {
    1: [["κυτταροπλασμ"], ["πρωτε"], ["συνθεσ"]],
    2: [["κυτταροπλασμ"], ["dna"], ["πληροφορ"]],
    3: [["φθορ"], ["γενετικ"], ["μικροσκ"]],
    4: [["μεσοσ ορ", "μεσο ορ", "μεσου ορ", "μεσων ορ", "μ.ο", "mean", "average"],
        ["αποκλισ", "standard deviation", "τυπικη απ"]],
}


def _norm(s):
    """Πεζά, χωρίς τόνους, με τελικό σ - ώστε «Μέσος» και «μεσοσ» να ταιριάζουν."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ς", "σ")


def _tairiasmata(n, keimeno):
    t = _norm(keimeno)
    briskontai, leipoun = [], []
    for omada in KLEIDIA.get(n, []):
        hit = next((w for w in omada if _norm(w) in t), None)
        (briskontai if hit else leipoun).append(hit or omada[0])
    return briskontai, leipoun


def _apaitoumena(n):
    """Πόσες έννοιες πρέπει να εντοπιστούν για να καταγραφεί η απάντηση.

    Όταν η ερώτηση ορίζει περισσότερες από δύο έννοιες, ζητούνται τουλάχιστον
    δύο· διαφορετικά αρκεί μία.
    """
    return 2 if len(KLEIDIA.get(n, [])) > 2 else 1


def _fortose():
    if os.path.exists(ARXEIO):
        with open(ARXEIO, "rb") as f:
            rec = pickle.load(f)
        rec.setdefault("proxeira", {})      # ό,τι γράφτηκε, έστω ατελές
        rec.setdefault("apantiseis", {})
        return rec
    return {"onoma": ONOMA, "enarxi": time.time(),
            "enarxi_iso": datetime.now().isoformat(timespec="seconds"),
            "apantiseis": {}, "proxeira": {}}


def _apothikeuse(rec):
    rec["onoma"] = ONOMA or rec.get("onoma", "")
    with open(ARXEIO, "wb") as f:
        pickle.dump(rec, f)


def _bar(rec):
    from IPython.display import HTML, display
    seires = []
    for n in sorted(EROTISEIS):
        a = rec["apantiseis"].get(n)
        if a:
            chroma, keimeno = "#1565c0", a["timestamp"].replace("T", "  ")
            lepta = f"{a['lepta_apo_tin_arxi']} λεπτά"
        else:
            chroma, keimeno, lepta = "#c62828", "&mdash;", ""
        seires.append(f"""
<tr>
  <td style="padding:4px 10px; color:#1a1a1a; white-space:nowrap;">
      <b>{n}.</b> {EROTISEIS[n]}</td>
  <td style="padding:4px 10px; width:220px;">
      <div style="background:{chroma}; height:14px; width:200px;
                  border-radius:7px;"></div></td>
  <td style="padding:4px 10px; color:#555; font-family:monospace;
             white-space:nowrap;">{keimeno}</td>
  <td style="padding:4px 10px; color:#555; white-space:nowrap;">{lepta}</td>
</tr>""")

    plithos = len(rec["apantiseis"])
    display(HTML(f"""
<div style="background:#fafafa; border:1px solid #e0e0e0; border-radius:6px;
            padding:12px 16px; color:#1a1a1a; display:inline-block;">
<b>Πρόοδος: {plithos} από {len(EROTISEIS)}</b>
&nbsp;&nbsp;<span style="color:#777;">{rec.get("onoma") or "χωρίς όνομα"}</span>
<table style="border-collapse:collapse; margin-top:8px;">{''.join(seires)}</table>
</div>"""))


def katagrapse(n, keimeno):
    """Ελέγχει την απάντηση, καταγράφει χρονοσήμανση και ενημερώνει την μπάρα."""
    keimeno = str(keimeno).strip()
    rec = _fortose()

    if not keimeno:
        print(f"Ερώτηση {n}: δεν έχετε γράψει ακόμη απάντηση.")
        _bar(rec); return

    # Σώζεται πρώτα το κείμενο: αν χαθεί η σύνδεση, δεν χάνεται ό,τι γράφτηκε.
    rec["proxeira"][n] = keimeno
    _apothikeuse(rec)

    briskontai, leipoun = _tairiasmata(n, keimeno)

    apaitoumena = _apaitoumena(n)

    if len(briskontai) >= apaitoumena and n not in rec["apantiseis"]:
        tora = time.time()
        rec["apantiseis"][n] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lepta_apo_tin_arxi": round((tora - rec["enarxi"]) / 60, 2),
            "keimeno": keimeno,
            "lexeis_pou_vrethikan": briskontai,
            "ennoies": f"{len(briskontai)}/{apaitoumena}",
        }
        _apothikeuse(rec)
        print(f"Ερώτηση {n}: καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    elif n in rec["apantiseis"]:
        rec["apantiseis"][n]["keimeno"] = keimeno      # η χρονοσήμανση μένει
        _apothikeuse(rec)
        print(f"Ερώτηση {n}: ήδη καταγεγραμμένη "
              f"({rec['apantiseis'][n]['timestamp'].replace('T', ' ')}). "
              "Το κείμενο ενημερώθηκε.")
    else:
        print(f"Ερώτηση {n}: χρειάζονται τουλάχιστον {apaitoumena} από τις "
              f"ζητούμενες έννοιες, εντοπίστηκαν {len(briskontai)}. "
              "Συμπληρώστε την απάντησή σας και ξανατρέξτε το κελί.")

    _bar(rec)


def epanafora():
    """Επαναφέρει τις απαντήσεις μετά από διακοπή σύνδεσης ή επανεκκίνηση.

    Αν το Colab έσβησε τη μηχανή, το αρχείο δεν υπάρχει πια εδώ: ανεβάστε αυτό
    που είχατε κατεβάσει και οι απαντήσεις επιστρέφουν στις μεταβλητές.
    """
    if not os.path.exists(ARXEIO):
        try:
            from google.colab import files
            print(f"Δεν βρέθηκε {ARXEIO}. Ανεβάστε το αρχείο που είχατε κατεβάσει:")
            files.upload()
        except Exception:
            pass

    if not os.path.exists(ARXEIO):
        print("Δεν βρέθηκε αρχείο απαντήσεων. Ξεκινήστε κανονικά από την αρχή.")
        return

    rec = _fortose()

    # Οι μεταβλητές πρέπει να επανέλθουν στον χώρο ονομάτων του notebook,
    # όχι σε αυτόν του module - γι' αυτό παίρνουμε το frame του καλούντος.
    import inspect
    frame = inspect.currentframe()
    g = frame.f_back.f_globals if frame and frame.f_back else globals()

    epanaferthikan = []
    for n in sorted(EROTISEIS):
        keimeno = (rec["apantiseis"].get(n, {}).get("keimeno")
                   or rec["proxeira"].get(n))
        if keimeno:
            g[f"apantisi_{n}"] = keimeno
            epanaferthikan.append(n)

    if rec.get("onoma"):
        g["ONOMA"] = rec["onoma"]

    print(f"Επαναφέρθηκαν οι απαντήσεις: {epanaferthikan or 'καμία'}")
    print("Οι χρονοσημάνσεις που είχαν καταγραφεί διατηρούνται.")
    print("Προσοχή: τα κελιά δείχνουν ακόμη το παλιό τους κείμενο - "
          "τυπώστε π.χ. apantisi_1 για να δείτε τι επαναφέρθηκε.")
    _bar(rec)
    return rec


def katevase_apantiseis():
    """Αποθηκεύει και κατεβάζει το αρχείο με τις χρονοσημάνσεις."""
    rec = _fortose()
    _apothikeuse(rec)
    print(f"Αποθηκεύτηκαν {len(rec['apantiseis'])} από {len(EROTISEIS)} απαντήσεις "
          f"στο {ARXEIO}")
    if not ONOMA:
        print("ΠΡΟΣΟΧΗ: δεν έχετε συμπληρώσει το ONOMA στο πρώτο κελί.")
    try:
        from google.colab import files
        files.download(ARXEIO)
    except Exception:
        print(f"(Εκτός Colab: το αρχείο βρίσκεται στο {os.path.abspath(ARXEIO)})")
    return rec
