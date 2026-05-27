import random

# (forma żeńska, forma męska) — jedno źródło prawdy dla obu rodzajów.
ADJECTIVE_PAIRS = [
    ("Zaangażowana", "Zaangażowany"), ("Skupiona", "Skupiony"), ("Wesoła", "Wesoły"),
    ("Przemyślana", "Przemyślany"), ("Energiczna", "Energiczny"), ("Spokojna", "Spokojny"),
    ("Kreatywna", "Kreatywny"), ("Zdeterminowana", "Zdeterminowany"), ("Ciekawa", "Ciekawy"),
    ("Ambitna", "Ambitny"), ("Odważna", "Odważny"), ("Precyzyjna", "Precyzyjny"),
    ("Dynamiczna", "Dynamiczny"), ("Uważna", "Uważny"), ("Zmotywowana", "Zmotywowany"),
    ("Pomysłowa", "Pomysłowy"), ("Dokładna", "Dokładny"), ("Opanowana", "Opanowany"),
    ("Empatyczna", "Empatyczny"), ("Niezawodna", "Niezawodny"), ("Konsekwentna", "Konsekwentny"),
    ("Bystra", "Bystry"), ("Wytrwała", "Wytrwały"), ("Pracowita", "Pracowity"),
    ("Pogodna", "Pogodny"), ("Rzetelna", "Rzetelny"), ("Spontaniczna", "Spontaniczny"),
    ("Życzliwa", "Życzliwy"), ("Błyskotliwa", "Błyskotliwy"), ("Rozważna", "Rozważny"),
    ("Elastyczna", "Elastyczny"), ("Skrupulatna", "Skrupulatny"), ("Zaradna", "Zaradny"),
    ("Serdeczna", "Serdeczny"), ("Natchniona", "Natchniony"),
]

FEMALE_ADJECTIVES = [pair[0] for pair in ADJECTIVE_PAIRS]
MALE_ADJECTIVES = [pair[1] for pair in ADJECTIVE_PAIRS]

FEMALE_NAMES = [
    "Izabela", "Zofia", "Karolina", "Agnieszka", "Monika",
    "Anna", "Magdalena", "Natalia", "Katarzyna", "Joanna",
    "Aleksandra", "Weronika", "Paulina", "Marta", "Patrycja",
    "Barbara", "Ewa", "Emilia", "Gabriela", "Dominika",
    "Julia", "Wiktoria", "Alicja", "Maja", "Nina",
    "Oliwia", "Helena", "Klaudia", "Liliana", "Iga",
]

MALE_NAMES = [
    "Marek", "Tomasz", "Piotr", "Łukasz", "Rafał",
    "Krzysztof", "Jakub", "Michał", "Paweł", "Adam",
    "Mateusz", "Bartosz", "Damian", "Szymon", "Kamil",
    "Maciej", "Sebastian", "Marcin", "Artur", "Dominik",
    "Wojciech", "Jan", "Filip", "Patryk", "Hubert",
    "Oskar", "Igor", "Antoni", "Leon", "Mikołaj",
]


def generate_session_name() -> str:
    # 0 = żeński, 1 = męski — losujemy raz, by przymiotnik i imię miały zgodny rodzaj.
    gender = random.randint(0, 1)
    adjective = random.choice(ADJECTIVE_PAIRS)[gender]
    name = random.choice(FEMALE_NAMES if gender == 0 else MALE_NAMES)
    return f"{adjective} {name}"

