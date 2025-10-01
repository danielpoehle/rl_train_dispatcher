# src/rail_types.py

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum, auto

# --------------------------------------------------------------------------
# ## ENUMS: Für klar definierte Zustände
# --------------------------------------------------------------------------

class KnotenTyp(Enum):
    """
    Definiert die 4 möglichen Arten von Knotenpunkten, die die physische
    Infrastruktur aufspannen.
    """
    SIGNAL = auto()         # Ein Punkt, an dem eine Fahrstraße beginnt oder endet.
    WEICHE = auto()         # Ein Punkt, an dem sich Gleisabschnitte verzweigen.
    STRECKEN_ENDE = auto()  # Ein Endpunkt des Netzes, z.B. ein Prellbock.
    AUFLOESEPUNKT = auto()  # Ein Punkt in der Topologie für Teilfahrstraßenauflösung
                            

class ZugStatus(Enum):
    """
    Definiert die möglichen physikalischen Zustände, in denen sich ein Zug
    befinden kann. (BLEIBT UNVERÄNDERT)
    """
    STEHEND = auto()
    BESCHLEUNIGEND = auto()
    FAHREND = auto()
    BREMSEND = auto()


# --------------------------------------------------------------------------
# ## 1. PHYSIKALISCHE INFRASTRUKTUR (STATISCH)
#
# Diese Klassen beschreiben das unveränderliche Grund-Layout des Schienennetzes.
# Sie sind die "Hardware".
# --------------------------------------------------------------------------

@dataclass
class Knotenpunkt:
    """
    Ein Knoten im Graphen unseres Schienennetzes. Jeder Knoten hat eine
    exakte geografische und betriebliche Position.
    """
    # Eindeutige ID, z.B. 'weiche_12a' oder 'signal_42'.
    knoten_id: str
    
    # Der Typ des Knotenpunkts, definiert durch das Enum 'KnotenTyp'.
    typ: KnotenTyp

    # Die exakte Position auf einer Strecke in Kilometern.
    # Erlaubt die Berechnung von Längen und Positionen.
    # Einheit: Kilometer (mit 3 Nachkommastellen für Metergenauigkeit).
    kilometrierung: float

    # Die X- und Y-Koordinaten für eine optionale grafische Darstellung.
    koordinate_x: float
    koordinate_y: float


@dataclass
class Gleisabschnitt:
    """
    Eine ungerichtete Kante im Graphen, die zwei Knotenpunkte physisch
    miteinander verbindet. Repräsentiert das reine Gleis ohne Fahrtrichtung.
    """
    # Eindeutige ID, z.B. 'gleis_twh_gbl_1'.
    abschnitt_id: str
    
    # Die ID des einen angebundenen Knotenpunkts.
    knoten_a_id: str
    
    # Die ID des anderen angebundenen Knotenpunkts.
    knoten_b_id: str
    
    # Die physikalische Länge des Gleisabschnitts.
    # Diese wird typischerweise aus der Differenz der Kilometrierung
    # der verbundenen Knoten berechnet.
    # Einheit: Meter.
    laenge: float
    
    # Die maximal zulässige Geschwindigkeit auf diesem Abschnitt.
    # Einheit: Meter pro Sekunde (m/s).
    geschwindigkeitslimit: float


# --------------------------------------------------------------------------
# ## 2. OPERATIONELLE LOGIK (DYNAMISCH)
#
# Diese Klassen beschreiben, wie die physische Infrastruktur genutzt wird.
# Sie sind die "Software".
# --------------------------------------------------------------------------

@dataclass
class Fahrstrasse:
    """
    Eine gesicherte, gerichtete Route für einen Zug von einem Start- zu
    einem Ziel-Signal. Sie besteht aus einer geordneten Kette von
    Gleisabschnitten und kann nur von einem Zug gleichzeitig genutzt werden.
    """
    # Eindeutige ID, z.B. 'fs_sig42_sig45_via_w12a'.
    fahrstrasse_id: str

    # Die geordnete Liste der Gleisabschnitt-IDs, aus denen diese Fahrstraße besteht.
    gleisabschnitte: List[str]

    # Der Startknoten dieser Fahrstraße (typischerweise ein Signal).
    von_knoten_id: str

    # Der Zielknoten dieser Fahrstraße (typischerweise ein Signal).
    bis_knoten_id: str

    # Die Gesamtlänge der Fahrstraße.
    # Ergibt sich aus der Summe der Längen der enthaltenen Gleisabschnitte.
    # Einheit: Meter.
    laenge: float

    # Eine Liste der IDs aller anderen Fahrstraßen, die nicht gleichzeitig
    # aktiv sein dürfen, weil sie mindestens einen Gleisabschnitt teilen
    # oder Weichen in einer inkompatiblen Stellung benötigen.
    konfligierende_fahrstrassen: List[str]

    # Die FIFO-Warteschlange für eingehende Anforderungen von Zügen,
    # die diese Fahrstraße nutzen möchten.
    anforderungs_warteschlange: List['RoutenAnforderung'] = field(default_factory=list)

    # --- Dynamische Zustände ---
    
    # Gibt die ID des Zuges an, der sich PHYSISCH auf der Fahrstraße befindet.
    belegt_von_zug_id: Optional[str] = None
    
    # Gibt die ID des Zuges an, für den diese Fahrstraße ZUKÜNFTIG reserviert ist.
    reserviert_fuer_zug_id: Optional[str] = None

    # Eine Liste der IDs der konfligierenden Fahrstraßen, die aktuell
    # belegt oder reserviert sind und somit diese Fahrstraße blockieren.
    # Eine Fahrstraße kann nur eingestellt werden, wenn `belegt_von_zug_id` None ist,
    # `reserviert_fuer_zug_id` None ist UND diese Liste leer ist.
    blockiert_durch_konflikt_ids: List[str] = field(default_factory=list)



@dataclass
class RoutenAnforderung:
    """
    Repräsentiert die Anforderung eines Zuges, eine bestimmte Fahrstraße zu
    reservieren. (fordert eine Fahrstraße an)
    """
    # Die ID des Zuges, der die Route anfordert.
    zug_id: str
    
    # Die ID der gewünschten Fahrstraße.
    fahrstrasse_id: str
    
    # Der Simulationszeitpunkt, zu dem die Anforderung erstellt wurde.
    zeitstempel: int


# --------------------------------------------------------------------------
# ## ZUG-KLASSEN (vorerst unverändert)
# --------------------------------------------------------------------------

@dataclass
class FahrplanEintrag:
    """
    Beschreibt einen Schritt im Fahrplan. Der Fahrplan ist eine geordnete
    Liste dieser Einträge. Jeder Eintrag definiert das nächste Signal-Ziel
    und die exakte Fahrstraße, die dorthin genommen werden soll.
    """
    # Die ID der Fahrstraße, die der Zug anfordern muss, um zum Ziel-Signal zu gelangen.
    fahrstrasse_id: str

    # Die ID des Ziel-Signals, das am Ende der Fahrstraße erreicht wird.
    signal_id: str
    
    # Die geplante Ankunftszeit an diesem Signal. Kann None sein, wenn es
    # nur ein Durchfahrtspunkt ohne Zeitmessung ist.
    # Einheit: Sekunden seit Simulationsstart.
    geplante_ankunft: Optional[int] = None
    
    # Die geplante Abfahrtszeit an diesem Signal. Kann None sein. Bei
    # reiner Durchfahrt ist ankunft == abfahrt.
    # Einheit: Sekunden seit Simulationsstart.
    geplante_abfahrt: Optional[int] = None

@dataclass
class Zug:
    """
    Repräsentiert einen einzelnen Zug mit all seinen statischen Eigenschaften
    und seinem dynamischen Zustand in der Simulation.
    """
    # --- Statische Eigenschaften ---
    
    # Eindeutige ID des Zuges, z.B. 'ICE_101'.
    zug_id: str
    
    # Zugtyp, z.B. 'ICE', 'Regionalbahn', 'Güterzug'.
    zug_typ: str
    
    # Die Gesamtlänge des Zuges. Wichtig, um zu wissen, wann ein Block
    # vollständig geräumt ist.
    # Einheit: Meter.
    laenge: float
    
    # Die fahrplangebundene Höchstgeschwindigkeit des Zuges.
    # Einheit: Meter pro Sekunde (m/s).
    max_geschwindigkeit: float
    
    # Die (vereinfachte, konstante) Beschleunigung des Zuges.
    # Einheit: Meter pro Sekunde zum Quadrat (m/s^2).
    beschleunigung: float
    
    # Die (vereinfachte, konstante) Bremsverzögerung des Zuges.
    # Einheit: Meter pro Sekunde zum Quadrat (m/s^2).
    bremsverzoegerung: float
    
    # Der vollständige Fahrplan des Zuges als eine Liste von Einträgen.
    fahrplan: List[FahrplanEintrag]
    
    # --- Dynamische Zustände (ändern sich in jedem Simulationsschritt) ---
    
    # Der aktuelle physikalische Zustand des Zuges.
    status: ZugStatus = ZugStatus.STEHEND
    
    # Die momentane Geschwindigkeit des Zuges.
    # Einheit: Meter pro Sekunde (m/s).
    aktuelle_geschwindigkeit: float = 0.0
    
    # Die aktuelle Position des ZUGANFANGS. Dargestellt als Tupel, das
    # angibt, WO sich der Zug befindet und wie weit er in diesem Element fortgeschritten ist.
    # Beispiele: ('abschnitt', 'gleis_A_B_1', 520.5) -> auf Gleisabschnitt, 520.5m vom Anfang entfernt
    #            ('knoten', 'weiche_12a', 0) -> steht genau auf einem Knotenpunkt
    aktuelle_position: Tuple[str, str, float] = ('knoten', 'start_node', 0.0)

    # Die aktuelle Verspätung des Zuges im Vergleich zum Fahrplan.
    # Eine positive Zahl bedeutet Verspätung, eine negative Verfrühung.
    # Einheit: Sekunden.
    verspaetung: int = 0

    # Index, der auf den nächsten zu erreichenden Eintrag im Fahrplan zeigt.
    naechster_fahrplan_eintrag_idx: int = 0
    
    # Ein Flag, das anzeigt, ob der Zug bereits eine Route zu seinem
    # NÄCHSTEN Zielknoten angefordert hat.
    hat_route_angefordert_naechste: bool = False

    # Ein Flag, das anzeigt, ob der Zug bereits eine Route zu seinem
    # ÜBERNÄCHSTEN Zielknoten angefordert hat (wichtig für kurze Blöcke).
    hat_route_angefordert_uebernaechste: bool = False