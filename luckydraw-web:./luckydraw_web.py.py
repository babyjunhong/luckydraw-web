#!/usr/bin/env python3
"""
luckydraw.py

Simple CLI program that asks the user for a quantity (number of prizes bought)
and prints randomized prizes chosen from a fixed list of 6 prize types.

Prizes in order (first to last):
  "photo frame", "slogan", "sticker set", "notebook", "pin button", "postcard"

Tiered behavior:
  - By default the draw is tiered (weighted). "photo frame" is the rarest,
    "postcard" is the most common.
  - You can disable tiering with --no-tiered to get uniform sampling.
  - Drawing without replacement (--unique) supports weighted sampling without
    replacement as well (implemented via iterative weighted selection).

Usage:
  python luckydraw.py
  python luckydraw.py 10
  python luckydraw.py 3 --unique
  python luckydraw.py 5 --seed 42
  python luckydraw.py 8 --no-tiered

Options:
  quantity      Positional integer: number of prizes to draw.
  --unique      If set, draws without replacement (quantity must be <= 6).
  --seed SEED   Seed for the RNG (useful for reproducible draws).
  --no-tiered   Disable tiered (weighted) draws and use uniform probability.
"""
from __future__ import annotations
import argparse
import random
from collections import Counter
import sys
from typing import List, Optional

PRIZES: List[str] = [
    "photo frame",
    "slogan",
    "sticker set",
    "notebook",
    "pin button",
    "postcard",
]

# Default weights for tiered draws (aligned with PRIZES order).
# Smaller weight -> rarer prize. These are relative weights.
DEFAULT_WEIGHTS: List[float] = [
    1.0,   # photo frame (rarest)
    3.0,   # slogan
    6.0,   # sticker set
    10.0,  # notebook
    20.0,  # pin button
    30.0,  # postcard (most common)
]


def weighted_sample_without_replacement(population: List[str], weights: List[float], k: int, rng: random.Random) -> List[str]:
    """
    Performs weighted sampling without replacement.
    This is done by iteratively selecting one item according to weights,
    removing it, and repeating until k items are selected.
    Suitable for small populations (here 6 prizes).
    """
    if k < 0:
        raise ValueError("k must be non-negative")
    if k > len(population):
        raise ValueError("k must be <= population size for sampling without replacement")
    pop = population[:]
    w = weights[:]
    result: List[str] = []
    for _ in range(k):
        total = sum(w)
        if total <= 0:
            # If all remaining weights are zero, fall back to uniform choice among remaining
            idx = rng.randrange(len(pop))
            result.append(pop.pop(idx))
            w.pop(idx)
            continue
        r = rng.random() * total
        cum = 0.0
        for i, wi in enumerate(w):
            cum += wi
            if r <= cum:
                result.append(pop.pop(i))
                w.pop(i)
                break
    return result


def draw_prizes(quantity: int, unique: bool = False, seed: Optional[int] = None, tiered: bool = True, weights: Optional[List[float]] = None) -> List[str]:
    """
    Draw `quantity` prizes.

    - If tiered is True (default), use weights (DEFAULT_WEIGHTS unless provided).
    - If unique is False (default), draw with replacement:
        - tiered -> use random.choices with weights
        - not tiered -> use random.choices uniform
    - If unique is True, draw without replacement:
        - tiered -> use weighted sampling without replacement
        - not tiered -> use random.sample uniform
    """
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    rng = random.Random(seed)

    if weights is None:
        weights = DEFAULT_WEIGHTS

    if len(weights) != len(PRIZES):
        raise ValueError("weights length must match number of prizes")

    if unique:
        if quantity > len(PRIZES):
            raise ValueError(f"quantity must be <= {len(PRIZES)} when drawing unique prizes")
        if tiered:
            return weighted_sample_without_replacement(PRIZES, weights, quantity, rng)
        else:
            return rng.sample(PRIZES, k=quantity)
    else:
        # with replacement
        if tiered:
            # random.choices supports weights on Random instance
            return rng.choices(PRIZES, weights=weights, k=quantity)
        else:
            return [rng.choice(PRIZES) for _ in range(quantity)]


def parse_args(argv):
    p = argparse.ArgumentParser(description="Lucky draw: randomize prizes for purchased quantity.")
    p.add_argument("quantity", nargs="?", type=int, help="Number of prizes bought (positive integer).")
    p.add_argument("--unique", action="store_true", help="Draw without replacement (no duplicate prizes).")
    p.add_argument("--seed", type=int, help="Optional integer seed for reproducible results.")
    p.add_argument("--no-tiered", action="store_true", help="Disable tiered (weighted) draws and use uniform probability.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    quantity = args.quantity

    # If quantity not provided on CLI, prompt the user interactively
    if quantity is None:
        try:
            raw = input(f"Enter quantity (number of prizes bought): ").strip()
            quantity = int(raw)
        except ValueError:
            print("Invalid input. Please enter a positive integer for quantity.", file=sys.stderr)
            return 1

    try:
        prizes = draw_prizes(quantity=quantity, unique=args.unique, seed=args.seed, tiered=(not args.no_tiered))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    print("\nYou bought:", quantity, "prize(s). Here are your randomized prizes:\n")
    for i, prize in enumerate(prizes, start=1):
        print(f" {i}. {prize}")

    print("\nSummary:")
    counts = Counter(prizes)
    for prize in PRIZES:
        if counts[prize]:
            print(f" - {prize}: {counts[prize]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())