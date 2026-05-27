import random

FEMALE_ADJECTIVES = [
    "Zaangażowana", "Skupiona", "Wesoła", "Przemyślana", "Energiczna",
    "Spokojna", "Kreatywna", "Zdeterminowana", "Ciekawa", "Ambitna",
    "Odważna", "Precyzyjna", "Dynamiczna", "Uważna", "Zmotywowana",
    "Pomysłowa", "Dokładna", "Opanowana", "Empatyczna", "Niezawodna",
    "Konsekwentna", "Bystra", "Wytrwała", "Pracowita", "Pogodna",
    "Rzetelna", "Spontaniczna", "Życzliwa", "Błyskotliwa", "Rozważna",
    "Elastyczna", "Skrupulatna", "Zaradna", "Serdeczna", "Natchniona",
]

MALE_ADJECTIVES = [
    "Zaangażowany", "Skupiony", "Wesoły", "Przemyślany", "Energiczny",
    "Spokojny", "Kreatywny", "Zdeterminowany", "Ciekawy", "Ambitny",
    "Odważny", "Precyzyjny", "Dynamiczny", "Uważny", "Zmotywowany",
    "Pomysłowy", "Dokładny", "Opanowany", "Empatyczny", "Niezawodny",
    "Konsekwentny", "Bystry", "Wytrwały", "Pracowity", "Pogodny",
    "Rzetelny", "Spontaniczny", "Życzliwy", "Błyskotliwy", "Rozważny",
    "Elastyczny", "Skrupulatny", "Zaradny", "Serdeczny", "Natchniony",
]

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
    # Keep adjective and first name in the same grammatical gender.
    gender_pool = random.choice([
        (FEMALE_ADJECTIVES, FEMALE_NAMES),
        (MALE_ADJECTIVES, MALE_NAMES),
    ])
    adjectives, names = gender_pool
    return f"{random.choice(adjectives)} {random.choice(names)}"

