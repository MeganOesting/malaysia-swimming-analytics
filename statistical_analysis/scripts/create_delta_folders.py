# -*- coding: utf-8 -*-
import os

BASE_DIR = 'Delta Data'
EVENTS = [
    '50 Free', '100 Free', '200 Free', '400 Free', '800 Free', '1500 Free',
    '100 Back', '200 Back', '100 Breast', '200 Breast',
    '100 Fly', '200 Fly', '200 IM', '400 IM'
]
GENDERS = ['F', 'M']
TRANSITIONS = [('15', '16'), ('16', '17'), ('17', '18')]

def main() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    created = 0
    for event in EVENTS:
        for gender in GENDERS:
            for age_from, age_to in TRANSITIONS:
                folder_name = f"{gender} {event} {age_from} to {age_to}"
                target = os.path.join(BASE_DIR, folder_name)
                os.makedirs(target, exist_ok=True)
                created += 1
    print(f"Created/ensured {created} folders under: {os.path.abspath(BASE_DIR)}")

if __name__ == '__main__':
    main()
