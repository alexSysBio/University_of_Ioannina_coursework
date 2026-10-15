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

import os, re, glob, time, shutil, pickle, unicodedata, hashlib
import pandas as pd
import numpy as np
from datetime import datetime

# --------------------------------------------------------------------------
# Όνομα φοιτητή/φοιτήτριας - ΣΥΜΠΛΗΡΩΣΤΕ ΤΟ ΠΡΙΝ ΞΕΚΙΝΗΣΕΤΕ
# --------------------------------------------------------------------------
ONOMA = ""          # π.χ. "Papadopoulou_Maria_14102027"
EMAIL = ""          # ακαδημαϊκό email, π.χ. "bio01234@uoi.gr"
VASI_ARXEIOU = "apantiseis"        # το όνομα συμπληρώνεται από το email


def onoma_arxeiou():
    """apantiseis_<χρήστης>.pkl, όπου <χρήστης> είναι το email πριν το @,
    χωρίς τελείες.

    Έτσι, αν πολλοί φοιτητές δουλέψουν στον ίδιο υπολογιστή, ο καθένας έχει
    ΔΙΚΟ ΤΟΥ αρχείο και κανείς δεν διαβάζει τις απαντήσεις κάποιου άλλου.
    Π.χ. a.papagiannakis@uoi.gr -> apantiseis_apapagiannakis.pkl
    """
    xristis = ""
    if EMAIL and "@" in EMAIL:
        xristis = EMAIL.split("@", 1)[0].strip().lower().replace(".", "")
        xristis = re.sub(r"[^A-Za-z0-9_-]", "_", xristis)
    return f"{VASI_ARXEIOU}_{xristis}.pkl" if xristis else f"{VASI_ARXEIOU}_ANONYMO.pkl"

EROTISEIS = {
    1: "Ερώτηση 1",
    2: "Ερώτηση 2",
    3: "Ερώτηση 3",
    4: "Ερώτηση 4",
    5: "Άσκηση 1",
    6: "Άσκηση 2",
    7: "Άσκηση 3",
    8: "Άσκηση 4",
}

# Ποιες στήλες ελέγχει κάθε άσκηση κώδικα: n -> (στήλη φοιτητή, σωστή στήλη).
# Η επαλήθευση γίνεται ΑΠΟ ΤΑ ΙΔΙΑ ΤΑ ΔΕΔΟΜΕΝΑ και όχι από τον αριθμό που
# δηλώνει ο φοιτητής, ώστε να μην αρκεί ένα «diafora = 0».
ASKISEIS = {
    5: ("cell_area_micrometer", "area_um"),
}

# Ασκήσεις που ζητούν αριθμητικές τιμές: n -> {όνομα: (στήλη, μέθοδος, ορίσματα)}.
# Η συνάρτηση υπολογίζει μόνη της το σωστό και το συγκρίνει με τη δήλωση του φοιτητή.
ASKISEIS_TIMON = {
    6: {
        "mesos":           ("cell_area_micrometer", "mean", {}),
        "typiki_apoklisi": ("cell_area_micrometer", "std", {"ddof": 1}),
    },
}

# Κάθε "omada" είναι μία έννοια· μέσα της βρίσκονται συνώνυμα. Αρκεί να
# εντοπιστεί ΜΙΑ έννοια για να καταγραφεί η απάντηση (ανεκτικός έλεγχος) -
# το πλήρες κείμενο αποθηκεύεται ούτως ή άλλως για έλεγχο από τον διδάσκοντα.
# --------------------------------------------------------------------------
# Λέξεις-κλειδιά σε κατακερματισμένη μορφή.
#
# Κάθε στοιχείο είναι "<μήκος>:<sha256 των πρώτων 16 δεκαεξαδικών>" της
# κανονικοποιημένης λέξης. Έτσι το αρχείο μπορεί να είναι δημόσιο χωρίς να
# αποκαλύπτει τις λέξεις - ούτε σε όποιον το διαβάσει στο GitHub, ούτε σε
# όποιον τυπώσει το KLEIDIA μέσα στο notebook.
#
# Για να τις αλλάξετε: επεξεργαστείτε το make_keys.py (ΜΗΝ το ανεβάζετε στο
# GitHub) και αντικαταστήστε το μπλοκ παρακάτω με την έξοδό του.
# --------------------------------------------------------------------------
# Ασκήσεις που παράγουν ΠΙΝΑΚΑ ανά ομάδα.
#   stili_omadas       : η στήλη ομαδοποίησης
#   stili_apotelesmatos: η στήλη που πρέπει να έχει υπολογίσει ο φοιτητής
ASKISEIS_PINAKA = {
    7: {
        "stili_omadas":        "cell_trajectory_id",
        "stili_apotelesmatos": "mesos_rythmos_afxisis_perhour",
        "stili_xronou":        "frame",      # 1 καρέ = 1 λεπτό
    },
}

# Ασκήσεις που ομαδοποιούν σε ΔΙΑΣΤΗΜΑΤΑ και υπολογίζουν ανά διάστημα.
# Οι αναμενόμενες τιμές είναι ΚΑΤΑΚΕΡΜΑΤΙΣΜΕΝΕΣ: ούτε η μέθοδος ούτε οι
# απαντήσεις φαίνονται σε όποιον διαβάσει αυτό το αρχείο.
ASKISEIS_BIN = {
    8: {
        "stili_apotelesmatos": "meso_emvadon",
        "psifia":              3,
        "kleidia":             [
            "c3288d62351728d7",
            "10e4bd9509940a6f",
            "85da49f644335c40",
            "cf285b57633ffb73",
            "8c29455502ef8ed1",
            "33dbfeac67ef15b8",
        ],
    },
}

SALT = "UoI-pandas-2026"

KLEIDIA = {
    1: [
        ["12:15d98cd5f45ca699"],
        ["5:033258d17457ff4f"],
        ["6:b0a23fa13b4b96ea"],
    ],
    2: [
        ["12:15d98cd5f45ca699"],
        ["3:6639bede9fb0c1de"],
        ["8:412bbdf07c22f3a8"],
    ],
    3: [
        ["4:a1a1e172d4495fa2"],
        ["7:3dcedc783d240a0b"],
        ["7:cc4dd0b6f2acdc3b"],
    ],
    4: [
        ["8:fc3cc00170fe7e73", "7:f86633d8a88d090a", "8:d715c9a07d83b8d1", "8:fcf3dfa56c0a4e1d", "3:76f47131373c4eb9", "4:f3e00df57fe2b558", "7:218716b5861952aa"],
        ["7:19b6b016ab321b3b", "18:1bf61b3c2985868f", "9:85d8214daf20973a"],
    ],
}

COLUMN_NAMES = {'cell_id':'Cell ID', 
                'cell_trajectory_id': 'Cell Cycle ID',
                'area_um': 'Cell Area (μm²)',
                'frame': 'Time (min)', 
                'cc_phase': 'Position in the cell cycle',
                'x': 'X cell coordinate (pixels)', 
                'y': 'Y cell coordinate (pixels)', 
                'cell_length_px': 'Cell Length (pixels)',
                'pixel_scale':0.066,
                'mean_fluor_2': 'RplA-GFP Mean Fluorescence (AU)',
                'mean_fluor_3': 'HupA-mCherry Mean Fluorescence (AU)'}


def _elegxos_email(address):
    """Επιστρέφει (έγκυρο, μήνυμα).

    Απαιτείται ακαδημαϊκό email του Πανεπιστημίου Ιωαννίνων. Γίνονται δεκτά και
    τα υποτομέα-email (π.χ. @cc.uoi.gr, @biology.uoi.gr), όχι όμως διευθύνσεις
    εκτός του ιδρύματος.
    """
    address = (address or "").strip()

    if not address:
        return False, ("δεν έχετε συμπληρώσει το cu.EMAIL - χωρίς αυτό δεν "
                       "μπορούν να σταλούν τα αποτελέσματά σας")

    if not re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", address):
        return False, f"το '{address}' δεν μοιάζει με έγκυρη διεύθυνση email"

    tomeas = address.rsplit("@", 1)[1].lower()
    if tomeas != "uoi.gr" and not tomeas.endswith(".uoi.gr"):
        return False, (f"το '{address}' δεν είναι ακαδημαϊκό email του "
                       "Πανεπιστημίου Ιωαννίνων - πρέπει να τελειώνει σε @uoi.gr")

    return True, ""


def _etiketa(n):
    """Η ετικέτα της ερώτησης/άσκησης, ίδια με αυτήν της μπάρας προόδου."""
    return EROTISEIS.get(n, f"Ερώτηση {n}")


def _norm(s):
    """Πεζά, χωρίς τόνους, με τελικό σ - ώστε «Μέσος» και «μεσοσ» να ταιριάζουν."""
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ς", "σ")


def _hash(s):
    return hashlib.sha256((SALT + s).encode("utf-8")).hexdigest()[:16]


def _tairiasmata(n, keimeno):
    """Ποιες έννοιες εντοπίζονται στο κείμενο.

    Οι λέξεις-κλειδιά δεν υπάρχουν πουθενά σε καθαρή μορφή: για κάθε μήκος που
    εμφανίζεται στο κλειδί, σαρώνουμε το κείμενο με παράθυρο αυτού του μήκους
    και συγκρίνουμε κατακερματισμούς.
    """
    t = _norm(keimeno)
    briskontai, leipoun = [], []

    for deiktis, omada in enumerate(KLEIDIA.get(n, []), start=1):
        ana_mikos = {}
        for item in omada:
            mikos, digest = item.split(":")
            ana_mikos.setdefault(int(mikos), set()).add(digest)

        vrethike = None
        for mikos, digests in sorted(ana_mikos.items(), reverse=True):
            if mikos > len(t):
                continue
            for i in range(len(t) - mikos + 1):
                if _hash(t[i:i + mikos]) in digests:
                    vrethike = t[i:i + mikos]
                    break
            if vrethike:
                break

        if vrethike:
            briskontai.append(vrethike)
        else:
            leipoun.append(f"έννοια {deiktis}")

    return briskontai, leipoun


def _apaitoumena(n):
    """Πόσες έννοιες πρέπει να εντοπιστούν για να καταγραφεί η απάντηση.

    Όταν η ερώτηση ορίζει περισσότερες από δύο έννοιες, ζητούνται τουλάχιστον
    δύο· διαφορετικά αρκεί μία.
    """
    return 2 if len(KLEIDIA.get(n, [])) > 2 else 1


def _diko_mou(rec):
    """True μόνο αν το αρχείο ανήκει σε ΑΥΤΟΝ τον χρήστη."""
    if not isinstance(rec, dict):
        return False
    email_arx = (rec.get("email") or "").strip().lower()
    onoma_arx = (rec.get("onoma") or "").strip()
    if EMAIL and email_arx and email_arx == EMAIL.strip().lower():
        return True
    if ONOMA and onoma_arx and onoma_arx == ONOMA.strip():
        return True
    return False


def _vres_proigoumeno():
    """Αρχείο από προηγούμενη αποθήκευση ΤΟΥ ΙΔΙΟΥ χρήστη - π.χ. αν διόρθωσε
    το email του. ΔΕΝ αγγίζει ποτέ αρχεία άλλων φοιτητών."""
    ypopsifia = sorted(glob.glob(VASI_ARXEIOU + "*.pkl"))
    ypopsifia += ["apantiseis_timestamps.pkl"]        # παλιό όνομα
    for diadromi in ypopsifia:
        if not os.path.exists(diadromi):
            continue
        try:
            with open(diadromi, "rb") as f:
                rec = pickle.load(f)
        except Exception:
            continue
        if _diko_mou(rec):
            return diadromi, rec
    return None, None


def _fortose():
    diadromi = onoma_arxeiou()
    if os.path.exists(diadromi):
        with open(diadromi, "rb") as f:
            rec = pickle.load(f)
        rec.setdefault("proxeira", {})      # ό,τι γράφτηκε, έστω ατελές
        rec.setdefault("apantiseis", {})
        return rec

    # Μήπως υπάρχει αρχείο του ΙΔΙΟΥ χρήστη με άλλο όνομα;
    palio, rec = _vres_proigoumeno()
    if rec is not None:
        print(f"(βρέθηκαν προηγούμενες απαντήσεις στο {palio})")
        rec.setdefault("proxeira", {})
        rec.setdefault("apantiseis", {})
        return rec

    return {"onoma": ONOMA, "email": EMAIL, "enarxi": time.time(),
            "enarxi_iso": datetime.now().isoformat(timespec="seconds"),
            "apantiseis": {}, "proxeira": {}}


def _apothikeuse(rec):
    rec["onoma"] = ONOMA or rec.get("onoma", "")
    rec["email"] = EMAIL or rec.get("email", "")
    with open(onoma_arxeiou(), "wb") as f:
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
      <b>{EROTISEIS[n]}</b></td>
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
&nbsp;&nbsp;<span style="color:#999; font-size:0.9em;">{rec.get("email") or "χωρίς email"}</span>
<table style="border-collapse:collapse; margin-top:8px;">{''.join(seires)}</table>
</div>"""))


def katagrapse(n, keimeno):
    """Ελέγχει την απάντηση, καταγράφει χρονοσήμανση και ενημερώνει την μπάρα."""
    keimeno = str(keimeno).strip()
    rec = _fortose()

    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        print("ΠΡΟΣΟΧΗ:", minima)

    if not keimeno:
        print(f"{_etiketa(n)}: δεν έχετε γράψει ακόμη απάντηση.")
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
            "ennoies": f"{len(briskontai)}/{apaitoumena}",
        }
        _apothikeuse(rec)
        print(f"{_etiketa(n)}: καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    elif n in rec["apantiseis"]:
        rec["apantiseis"][n]["keimeno"] = keimeno      # η χρονοσήμανση μένει
        _apothikeuse(rec)
        print(f"{_etiketa(n)}: ήδη καταγεγραμμένη "
              f"({rec['apantiseis'][n]['timestamp'].replace('T', ' ')}). "
              "Το κείμενο ενημερώθηκε.")
    else:
        print(f"{_etiketa(n)}: χρειάζονται τουλάχιστον {apaitoumena} από τις "
              f"ζητούμενες έννοιες, εντοπίστηκαν {len(briskontai)}. "
              "Συμπληρώστε την απάντησή σας και ξανατρέξτε το κελί.")

    _bar(rec)


def katagrapse_askisi_pinaka(n, pinakas, df=None, anoxi=1e-6):
    """Καταγράφει άσκηση που παράγει έναν συγκεντρωτικό πίνακα ανά ομάδα.

    Η συνάρτηση **ξαναϋπολογίζει μόνη της** το σωστό αποτέλεσμα από το `df`
    και το συγκρίνει γραμμή προς γραμμή με τον πίνακα του φοιτητή.
    """
    rec = _fortose()

    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        print("ΠΡΟΣΟΧΗ:", minima)

    prodiagrafi = ASKISEIS_PINAKA.get(n, {})
    if df is None or not prodiagrafi:
        print(f"{_etiketa(n)}: λείπει ο πίνακας δεδομένων.")
        _bar(rec); return False

    stili_omadas = prodiagrafi["stili_omadas"]
    stili_apot   = prodiagrafi["stili_apotelesmatos"]
    stili_xronou = prodiagrafi["stili_xronou"]

    # --- ο πίνακας του φοιτητή ------------------------------------------
    if not isinstance(pinakas, pd.DataFrame):
        print(f"{_etiketa(n)}: περίμενα έναν πίνακα (DataFrame), "
              f"πήρα {type(pinakas).__name__}.")
        print("Μήπως έμεινε το ... στο κελί;")
        _bar(rec); return False

    # Αν ο φοιτητής έκανε reset_index(), η στήλη ομαδοποίησης είναι πάλι στήλη:
    # τη βάζουμε ξανά ως ευρετήριο αντί να τον κόψουμε γι' αυτό.
    if stili_omadas in pinakas.columns:
        pinakas = pinakas.set_index(stili_omadas)

    if stili_apot not in pinakas.columns:
        print(f"{_etiketa(n)}: ο πίνακάς σας δεν έχει στήλη '{stili_apot}'.")
        print("Οι στήλες που βρήκα:", ", ".join(map(str, pinakas.columns)) or "(καμία)")
        _bar(rec); return False

    # --- ανεξάρτητος υπολογισμός ----------------------------------------
    diarkeia = df.groupby(stili_omadas)[stili_xronou].size()
    sosto = np.log(2) / (diarkeia / 60.0)

    if len(pinakas) != len(sosto):
        print(f"{_etiketa(n)}: ο πίνακάς σας έχει {len(pinakas)} γραμμές, "
              f"ενώ οι τροχιές είναι {len(sosto)}.")
        print(f"Ομαδοποιήσατε σωστά ως προς '{stili_omadas}';")
        _bar(rec); return False

    try:
        diko_tous = pd.to_numeric(pinakas[stili_apot], errors="raise")
    except (TypeError, ValueError):
        print(f"{_etiketa(n)}: η στήλη '{stili_apot}' δεν περιέχει αριθμούς.")
        print("Μήπως έμεινε το ... στη γραμμή του υπολογισμού;")
        _bar(rec); return False

    diko_tous = diko_tous.reindex(sosto.index)
    if diko_tous.isna().any():
        print(f"{_etiketa(n)}: οι ετικέτες του πίνακά σας δεν ταιριάζουν με "
              f"τις τροχιές του '{stili_omadas}'.")
        print("Χρησιμοποιήστε groupby(...).agg(...), χωρίς reset_index().")
        _bar(rec); return False

    diafora = float((diko_tous - sosto).abs().max())
    epetyche = diafora < max(anoxi, 1e-9)

    if not epetyche:
        print(f"{_etiketa(n)}: οι τιμές δεν συμφωνούν "
              f"(μέγιστη διαφορά {diafora:.4g}).")

        # οι δύο κλασικές παγίδες
        logos = float((diko_tous / sosto).median())
        if abs(logos - 1/60) < 0.02:
            print("     Ο χρόνος σας είναι σε ΛΕΠΤΑ, όχι σε ώρες.")
            print("     Διαιρέστε τη διάρκεια με το 60: ln(2) / (T / 60)")
        elif abs(logos - (np.log10(2) / np.log(2))) < 0.02:
            print("     Χρησιμοποιήσατε δεκαδικό λογάριθμο (log10).")
            print("     Ο ρυθμός αύξησης ορίζεται με ΦΥΣΙΚΟ λογάριθμο: np.log(2)")
        elif abs(logos - 60) < 2:
            print("     Ο χρόνος σας είναι σε ΩΡΕΣ εκεί που χρειάζονται λεπτά -")
            print("     μήπως διαιρέσατε δύο φορές με το 60;")
        _bar(rec); return False

    if n not in rec["apantiseis"]:
        tora = time.time()
        rec["apantiseis"][n] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lepta_apo_tin_arxi": round((tora - rec["enarxi"]) / 60, 2),
            "keimeno": (f"άσκηση κώδικα - {len(sosto)} τροχιές, "
                        f"διάμεσος ρυθμός {float(sosto.median()):.3f} /ώρα"),
            "ennoies": "1/1",
        }
        _apothikeuse(rec)
        print(f"{_etiketa(n)}: ΣΩΣΤΑ - καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    else:
        print(f"{_etiketa(n)}: σωστό (είχε ήδη καταγραφεί).")

    print(f"  τροχιές        : {len(sosto)}")
    print(f"  διάμεσος ρυθμός: {float(sosto.median()):.3f} ανά ώρα")
    _bar(rec)
    return True


def katagrapse_askisi_bin(n, pinakas, df=None):
    """Άσκηση με διαστήματα. Ο έλεγχος γίνεται με κατακερματισμένες τιμές:
    το αρχείο αυτό ΔΕΝ περιέχει ούτε τις απαντήσεις ούτε τον τρόπο υπολογισμού."""
    rec = _fortose()

    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        print("ΠΡΟΣΟΧΗ:", minima)

    prod = ASKISEIS_BIN.get(n, {})
    if not prod:
        print(f"{_etiketa(n)}: άγνωστη άσκηση.")
        _bar(rec); return False

    stili_apot = prod["stili_apotelesmatos"]
    psifia     = prod["psifia"]
    kleidia    = prod["kleidia"]

    if not isinstance(pinakas, pd.DataFrame):
        print(f"{_etiketa(n)}: περίμενα έναν πίνακα (DataFrame), "
              f"πήρα {type(pinakas).__name__}.")
        print("Μήπως έμεινε το ... στο κελί;")
        _bar(rec); return False

    if stili_apot not in pinakas.columns:
        print(f"{_etiketa(n)}: ο πίνακάς σας δεν έχει στήλη '{stili_apot}'.")
        print("Οι στήλες που βρήκα:", ", ".join(map(str, pinakas.columns)) or "(καμία)")
        _bar(rec); return False

    if len(pinakas) != len(kleidia):
        print(f"{_etiketa(n)}: ο πίνακάς σας έχει {len(pinakas)} γραμμές, "
              f"ενώ περίμενα {len(kleidia)}.")
        print("Ελέγξτε τα όρια των διαστημάτων και το include_lowest=True.")
        _bar(rec); return False

    try:
        dika_tous = pd.to_numeric(pinakas[stili_apot], errors="raise").to_numpy(dtype=float)
    except (TypeError, ValueError):
        print(f"{_etiketa(n)}: η στήλη '{stili_apot}' δεν περιέχει αριθμούς.")
        print("Μήπως έμεινε το ... στη γραμμή του υπολογισμού;")
        _bar(rec); return False

    tairiasan = sum(1 for tim, kl in zip(dika_tous, kleidia)
                    if not (tim != tim) and _hash(f"{tim:.{psifia}f}") == kl)
    anapoda = sum(1 for tim, kl in zip(dika_tous[::-1], kleidia)
                  if not (tim != tim) and _hash(f"{tim:.{psifia}f}") == kl)

    if tairiasan != len(kleidia):
        if anapoda == len(kleidia):
            print(f"{_etiketa(n)}: οι τιμές είναι σωστές αλλά ΑΝΑΠΟΔΑ.")
            print("Ταξινομήστε τον πίνακα κατά αύξον διάστημα.")
        else:
            print(f"{_etiketa(n)}: {tairiasan} από {len(kleidia)} διαστήματα σωστά.")
            print("Ελέγξτε τα όρια, το include_lowest=True, και ότι υπολογίζετε")
            print(f"τον ΜΕΣΟ ΟΡΟ (όχι τη διάμεσο) στη στήλη που ζητείται.")
        _bar(rec); return False

    if n not in rec["apantiseis"]:
        tora = time.time()
        rec["apantiseis"][n] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lepta_apo_tin_arxi": round((tora - rec["enarxi"]) / 60, 2),
            "keimeno": f"άσκηση κώδικα - {len(kleidia)} διαστήματα, όλα σωστά",
            "ennoies": "1/1",
        }
        _apothikeuse(rec)
        print(f"{_etiketa(n)}: ΣΩΣΤΑ - καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    else:
        print(f"{_etiketa(n)}: σωστό (είχε ήδη καταγραφεί).")

    print(f"  και τα {len(kleidia)} διαστήματα αναπαράχθηκαν σωστά.")
    _bar(rec)
    return True


def epanafora():
    """Επαναφέρει τις απαντήσεις μετά από διακοπή σύνδεσης ή επανεκκίνηση.

    Αν το Colab έσβησε τη μηχανή, το αρχείο δεν υπάρχει πια εδώ: ανεβάστε αυτό
    που είχατε κατεβάσει και οι απαντήσεις επιστρέφουν στις μεταβλητές.
    """
    if not os.path.exists(onoma_arxeiou()):
        try:
            from google.colab import files
            print(f"Δεν βρέθηκε {onoma_arxeiou()}. Ανεβάστε το αρχείο που είχατε κατεβάσει:")
            files.upload()
        except Exception:
            pass

    if not os.path.exists(onoma_arxeiou()) and _vres_proigoumeno()[1] is None:
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
    if rec.get("email"):
        g["EMAIL"] = rec["email"]

    print(f"Επαναφέρθηκαν οι απαντήσεις: {epanaferthikan or 'καμία'}")
    print("Οι χρονοσημάνσεις που είχαν καταγραφεί διατηρούνται.")
    print("Προσοχή: τα κελιά δείχνουν ακόμη το παλιό τους κείμενο - "
          "τυπώστε π.χ. apantisi_1 για να δείτε τι επαναφέρθηκε.")
    _bar(rec)
    return None


def katagrapse_askisi(n, diafora, df=None, anoxi=1e-9):
    """Καταγράφει μια άσκηση κώδικα.

    Ο έλεγχος γίνεται σε δύο σκέλη:

    1. Αν δοθεί το `df`, η συνάρτηση **υπολογίζει μόνη της** τη διαφορά από τις
       στήλες του πίνακα· δεν εμπιστεύεται τον αριθμό του φοιτητή.
    2. Ο αριθμός που δήλωσε ο φοιτητής πρέπει να **συμφωνεί** με τον πραγματικό.
    """
    rec = _fortose()

    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        print("ΠΡΟΣΟΧΗ:", minima)

    # --- 1. ανεξάρτητη επαλήθευση από τα ίδια τα δεδομένα ------------------
    pragmatiki = None
    if df is not None and n in ASKISEIS:
        stili_foititi, stili_sosti = ASKISEIS[n]
        if stili_foititi not in df.columns:
            print(f"{_etiketa(n)}: δεν βρέθηκε η στήλη '{stili_foititi}'.")
            print("Τρέξτε πρώτα το κελί που τη δημιουργεί.")
            _bar(rec)
            return False
        if stili_sosti not in df.columns:
            print(f"{_etiketa(n)}: δεν βρέθηκε η στήλη αναφοράς '{stili_sosti}' "
                  f"στον πίνακα.")
            print("Φορτώστε ξανά τα αρχικά δεδομένα και ξανατρέξτε τα κελιά.")
            _bar(rec)
            return False
        try:
            pragmatiki = float(
                (pd.to_numeric(df[stili_foititi], errors="raise")
                 - pd.to_numeric(df[stili_sosti], errors="raise")).abs().max()
            )
        except (TypeError, ValueError):
            print(f"{_etiketa(n)}: η στήλη '{stili_foititi}' δεν είναι αριθμητική.")
            print("Μήπως αφήσατε το ... στο κελί της μετατροπής;")
            _bar(rec)
            return False

    # --- 2. ο αριθμός που δήλωσε ο φοιτητής -------------------------------
    try:
        diafora = float(diafora)
    except (TypeError, ValueError):
        print(f"{_etiketa(n)}: η τιμή που δώσατε δεν είναι αριθμός.")
        print("Μήπως αφήσατε το ... στον υπολογισμό της διαφοράς;")
        _bar(rec)
        return False

    if diafora != diafora:
        print(f"{_etiketa(n)}: η διαφορά βγήκε NaN - ελέγξτε τη στήλη σας.")
        _bar(rec)
        return False

    if pragmatiki is not None and abs(diafora - pragmatiki) > max(anoxi, 1e-6):
        print(f"{_etiketa(n)}: ο αριθμός που δηλώσατε ({diafora:.4g}) δεν προκύπτει "
              f"από τα δεδομένα σας.")
        print(f"Η πραγματική μέγιστη διαφορά είναι {pragmatiki:.4g}.")
        print("Υπολογίστε την από τις στήλες - μην τη γράψετε στο χέρι.")
        _bar(rec)
        return False

    elegxomeni = pragmatiki if pragmatiki is not None else diafora
    epetyche = abs(elegxomeni) < anoxi

    if epetyche and n not in rec["apantiseis"]:
        tora = time.time()
        rec["apantiseis"][n] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lepta_apo_tin_arxi": round((tora - rec["enarxi"]) / 60, 2),
            "keimeno": f"άσκηση κώδικα - διαφορά {elegxomeni:.3g}",
            "ennoies": "1/1",
        }
        _apothikeuse(rec)
        print(f"{_etiketa(n)}: ΣΩΣΤΑ - καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    elif epetyche:
        print(f"{_etiketa(n)}: σωστό (είχε ήδη καταγραφεί "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}).")
    else:
        print(f"{_etiketa(n)}: όχι ακόμη - η διαφορά είναι {elegxomeni:.4g}, "
              f"ενώ θα έπρεπε να είναι πρακτικά μηδέν.")
        print("Ελέγξτε ξανά τον συντελεστή μετατροπής και ξανατρέξτε τα κελιά.")

    _bar(rec)
    return epetyche


def katagrapse_askisi_timon(n, df=None, anoxi=1e-7, **timres):
    """Καταγράφει άσκηση που ζητά αριθμητικές τιμές.

    Ο φοιτητής δηλώνει τις τιμές ως ορίσματα, π.χ.

        cu.katagrapse_askisi_timon(6, df, mesos=..., typiki_apoklisi=...)

    Η συνάρτηση υπολογίζει η ίδια το σωστό αποτέλεσμα από τον πίνακα.
    """
    rec = _fortose()

    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        print("ΠΡΟΣΟΧΗ:", minima)

    prodiagrafi = ASKISEIS_TIMON.get(n, {})
    if df is None or not prodiagrafi:
        print(f"{_etiketa(n)}: λείπει ο πίνακας δεδομένων.")
        _bar(rec); return False

    ola_sosta = True
    for onoma, (stili, methodos, orismata) in prodiagrafi.items():
        if stili not in df.columns:
            print(f"{_etiketa(n)}: δεν βρέθηκε η στήλη '{stili}'.")
            print("Τρέξτε πρώτα την Άσκηση 1 που τη δημιουργεί.")
            _bar(rec); return False

        # Η στήλη μπορεί να υπάρχει αλλά να μην είναι αριθμητική - τυπικά
        # όταν έχει μείνει το «...» στο κελί της Άσκησης 1.
        try:
            arithmitiki = pd.to_numeric(df[stili], errors="raise")
        except (TypeError, ValueError):
            print(f"{_etiketa(n)}: η στήλη '{stili}' δεν περιέχει αριθμούς.")
            print("Μήπως έμεινε το ... στο κελί της Άσκησης 1;")
            print("Συμπληρώστε τη μετατροπή, τρέξτε ξανά εκείνο το κελί, "
                  "και μετά αυτό.")
            _bar(rec); return False

        sosto = float(getattr(arithmitiki, methodos)(**orismata))
        dothike = timres.get(onoma, None)

        try:
            dothike = float(dothike)
        except (TypeError, ValueError):
            print(f"{_etiketa(n)}: η τιμή '{onoma}' λείπει ή δεν είναι αριθμός.")
            ola_sosta = False
            continue

        if abs(dothike - sosto) < anoxi:
            print(f"  {onoma}: {dothike:.6f}  ΣΩΣΤΟ")
            continue

        ola_sosta = False
        print(f"  {onoma}: {dothike:.6f}  ΛΑΘΟΣ (αναμενόταν {sosto:.6f})")

        # η κλασική παγίδη: τυπική απόκλιση πληθυσμού αντί για δείγματος
        if methodos == "std":
            alt = float(arithmitiki.std(ddof=0))
            if abs(dothike - alt) < anoxi:
                print("     Χρησιμοποιήσατε ddof=0 (τυπική απόκλιση πληθυσμού).")
                print("     Τα δεδομένα μας είναι ΔΕΙΓΜΑ - χρειάζεται ddof=1.")
                print("     Η pandas το κάνει από μόνη της: df[...].std()")
                print("     Η numpy ΟΧΙ: np.std(...) -> πρέπει np.std(..., ddof=1)")

    if ola_sosta and n not in rec["apantiseis"]:
        tora = time.time()
        rec["apantiseis"][n] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "lepta_apo_tin_arxi": round((tora - rec["enarxi"]) / 60, 2),
            "keimeno": "άσκηση κώδικα - " + ", ".join(
                f"{k}={float(v):.4f}" for k, v in sorted(timres.items())),
            "ennoies": f"{len(prodiagrafi)}/{len(prodiagrafi)}",
        }
        _apothikeuse(rec)
        print(f"\n{_etiketa(n)}: ΣΩΣΤΑ - καταγράφηκε στις "
              f"{rec['apantiseis'][n]['timestamp'].replace('T', ' ')}.")
    elif ola_sosta:
        print(f"\n{_etiketa(n)}: σωστό (είχε ήδη καταγραφεί).")
    else:
        print(f"\n{_etiketa(n)}: διορθώστε τις τιμές και ξανατρέξτε το κελί.")

    _bar(rec)
    return ola_sosta


def katevase_apantiseis(diadromi=None):
    """Αποθηκεύει ΚΑΙ κατεβάζει το αρχείο με τις χρονοσημάνσεις.

    diadromi : πού θα πάει το αρχείο.
        None            -> μένει στον τρέχοντα φάκελο και ΚΑΤΕΒΑΙΝΕΙ (Colab)
        "φάκελος/"      -> αντιγράφεται εκεί (π.χ. στο Google Drive)
        "φάκελος/x.pkl" -> αντιγράφεται εκεί, με αυτό το όνομα

    Η λήψη γίνεται ΠΑΝΤΑ, ακόμη κι αν λείπει το όνομα ή το email: στο Colab
    ένα αρχείο που δεν κατέβηκε χάνεται μαζί με τη μηχανή, και δεν υπάρχει
    λόγος να χάσει κανείς τη δουλειά του για ένα τυπογραφικό.
    """
    rec = _fortose()
    _apothikeuse(rec)
    arxeio = onoma_arxeiou()

    print(f"Αποθηκεύτηκαν {len(rec['apantiseis'])} από {len(EROTISEIS)} απαντήσεις "
          f"στο {arxeio}")

    provlimata = []
    if not ONOMA:
        provlimata.append("δεν έχετε συμπληρώσει το cu.ONOMA")
    egkyro, minima = _elegxos_email(EMAIL)
    if not egkyro:
        provlimata.append(minima)

    if provlimata:
        print()
        print("!" * 68)
        for p in provlimata:
            print("ΠΡΟΣΟΧΗ:", p)
        print()
        print("Το αρχείο κατεβαίνει κανονικά, ΑΛΛΑ χωρίς σωστό όνομα και email")
        print("δεν μπορεί να σας αποδοθεί. Διορθώστε τα στο πρώτο κελί και")
        print("ξανατρέξτε ΑΥΤΟ το κελί - θα κατέβει διορθωμένο.")
        print("!" * 68)
    else:
        print("Όνομα :", ONOMA)
        print("Email :", EMAIL)

    # --- πού θα καταλήξει ------------------------------------------------
    if diadromi is None:
        # προεπιλογή: μένει εδώ και κατεβαίνει στον υπολογιστή
        try:
            from google.colab import files
            files.download(arxeio)
        except Exception:
            print(f"(Εκτός Colab: το αρχείο βρίσκεται στο "
                  f"{os.path.abspath(arxeio)})")
        return os.path.abspath(arxeio)

    # δόθηκε διαδρομή: αντιγράφουμε εκεί, χωρίς λήψη από τον browser
    diadromi = os.path.expanduser(str(diadromi))
    if diadromi.endswith(".pkl"):
        fakelos, telikо = os.path.dirname(diadromi) or ".", os.path.basename(diadromi)
    else:
        fakelos, telikо = diadromi, arxeio

    try:
        if fakelos and not os.path.isdir(fakelos):
            os.makedirs(fakelos, exist_ok=True)
        proorismos = os.path.join(fakelos, telikо)
        shutil.copy2(arxeio, proorismos)
        print(f"Αντιγράφηκε στο {os.path.abspath(proorismos)}")
        return os.path.abspath(proorismos)
    except Exception as e:
        print(f"ΣΦΑΛΜΑ: δεν μπόρεσα να γράψω στο '{diadromi}' "
              f"({type(e).__name__}: {e})")
        print(f"Το αρχείο παραμένει στο {os.path.abspath(arxeio)}")
        return os.path.abspath(arxeio)
