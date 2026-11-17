"""
Zentrale Konfiguration: Kästchen-Koordinaten, Varianz-Parameter.
Hier anpassen, wenn sich das Formular ändert.
"""

# ---- Formular ----
FORMULAR_PFAD = "static/formular.pdf"
FORMULAR_SEITE = 0                 # 0 = erste Seite

# ---- Unterschriftenkästchen (Bounding Box in PDF-Punkten) ----
# Einmalig an dein Formular anpassen (siehe README unten).
KAESTCHEN_X0 = 352                 # linke Kante
KAESTCHEN_Y0 = 266                 # obere Kante
KAESTCHEN_X1 = 535                 # rechte Kante
KAESTCHEN_Y1 = 335                 # untere Kante

# ---- Signaturgröße im Kästchen ----
SIGNATUR_BREITE_FAKTOR = 0.85      # 85 % der Kästchenbreite
SIGNATUR_HOEHE_FAKTOR = 0.90       # max. 90 % der Kästchenhöhe

# ---- Positionsvarianz innerhalb des Kästchens ----
POSITION_VARIANZ_X = 0.15          # ±15 % der Kästchenbreite
POSITION_VARIANZ_Y = 0.15          # ±15 % der Kästchenhöhe

# ---- Organische Varianz (95 % Ähnlichkeit zum Original) ----
ROTATION_MIN_GRAD = -8.0
ROTATION_MAX_GRAD = 8.0
SKALIERUNG_MIN = 0.97
SKALIERUNG_MAX = 1.03
PERSPEKTIVE_MAX = 0.015
STRICH_DILATE_WAHRSCHEINLICHKEIT = 0.15
STRICH_ERODE_WAHRSCHEINLICHKEIT = 0.15
RAUSCH_SIGMA = 3.0
