# -*- coding: utf-8 -*-
import os

BASE = os.path.join('Delta Data')


def main() -> None:
    removed = 0
    for root, dirs, files in os.walk(BASE):
        for fn in files:
            # Legacy file pattern to remove
            if fn.endswith('Improvement Analysis.txt') and not fn.endswith('Improvement Analysis Report.txt'):
                path = os.path.join(root, fn)
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    pass
    print(f"Removed {removed} legacy report file(s)")


if __name__ == '__main__':
    main()



