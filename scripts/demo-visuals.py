#!/usr/bin/env python3
"""Dependency-free ANSI visuals for the recorded terminal demo."""

from __future__ import annotations

import sys


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def fg(red: int, green: int, blue: int, text: str) -> str:
    return f"\033[38;2;{red};{green};{blue}m{text}{RESET}"


def badge(red: int, green: int, blue: int, text: str) -> str:
    return f"\033[48;2;{red};{green};{blue}m\033[38;2;255;255;255m {text} {RESET}"


def architecture() -> None:
    print(f"{BOLD}THE POLIGN EVIDENCE GRAPH{RESET}\n")
    print(
        "  "
        + badge(19, 105, 120, "1  CURATOR MEMORY")
        + " " * 13
        + badge(40, 80, 150, "2  NGA CANDIDATES")
    )
    print(f"  {fg(120, 210, 220, 'preferences + prior choices')}        {fg(145, 180, 255, 'scoped, eligible artworks')}")
    print("              │                                  │")
    print("              └──────────────┬───────────────────┘")
    print("                             ▼")
    print("                  " + badge(99, 74, 160, "AGENT DECIDES WHAT IT NEEDS"))
    print("                       ╱              ╲")
    print("                      ▼                ▼")
    print(
        "       "
        + badge(155, 65, 130, "3  VISUAL CACHE")
        + "      "
        + badge(174, 112, 29, "4  ART CONTEXT")
    )
    print(f"       {fg(230, 145, 205, 'image observations')}         {fg(245, 188, 92, 'research passages')}")
    print("                      ╲                ╱")
    print("                       ╲              ╱")
    print("                        ▼            ▼")
    print("                    " + badge(42, 135, 91, "DRAFT → REVIEW → SUMMARY"))
    print(f"\n  {DIM}Each box is an independent collection in the same durable database.{RESET}")


MONET = [
    ["315f65", "39736e", "4f8374", "659484", "5a8979", "3c746c", "356863", "3f7870", "558a79", "6c9983", "518070", "35645e"],
    ["254f3b", "315f40", "4b774e", "6d965f", "749d68", "527c55", "365e42", "476f4c", "668c5c", "789e6b", "4e744f", "294f3c"],
    ["203a2d", "273e30", "334936", "3a4c38", "3c4b38", "354431", "30402f", "354632", "3b4c36", "344731", "293d2e", "22372b"],
    ["547c70", "47766f", "366a69", "3d7474", "5a8580", "779792", "6f918c", "55817e", "3f7472", "376b6b", "477572", "5b8178"],
    ["6d9189", "73968c", "5f8883", "d09aa4", "6b918c", "507d79", "70928c", "8ba39a", "c795a2", "668b86", "507b77", "78968c"],
    ["76958c", "557e79", "cc8f9d", "78958d", "5d8580", "83a098", "628983", "d6a0aa", "71938d", "577f7a", "8aa39a", "6b8e87"],
    ["60847b", "d29ca5", "6e9087", "4f7974", "86a099", "638781", "d29ba6", "75938c", "557c78", "8aa19a", "698b84", "d09aa5"],
]

VAN_GOGH = [
    ["7896b5", "829dbc", "8ba3bf", "94abc5", "9baec5", "91a7c1", "829dbb", "7895b4", "849fbd", "91a9c4", "879fbd", "7995b5"],
    ["6684a1", "708da8", "7894ae", "829bb3", "7892ac", "6a87a4", "7893ae", "86a0b7", "7692ad", "6986a3", "7893ad", "829bb4"],
    ["315747", "3e694e", "557958", "66855d", "4b714f", "365f49", "547855", "6c8960", "517451", "3b6248", "587b55", "6d8a60"],
    ["c4a15a", "d8b45e", "c79650", "dfbd67", "d09d4f", "e0bd65", "c89b54", "d8af59", "c7944b", "dfb966", "cfa052", "d8af5c"],
    ["a84f48", "c76655", "d07d62", "b4564c", "cf7259", "df8967", "b6574b", "cc6b54", "dc8364", "b34f48", "cb6956", "db8263"],
    ["d7b95e", "e4ca6d", "d8b858", "edcf78", "d9ba60", "e7cb73", "d3af50", "e6c76c", "dab95d", "ebcc75", "d3b154", "e3c36b"],
    ["456b47", "547b4d", "638750", "486f47", "5e824d", "709258", "4b7046", "62864f", "72945a", "4e7248", "638550", "74945b"],
]


def color_row(colors: list[str]) -> str:
    cells = []
    for color in colors:
        red, green, blue = (int(color[index : index + 2], 16) for index in (0, 2, 4))
        cells.append(f"\033[48;2;{red};{green};{blue}m  ")
    return "".join(cells) + RESET


def artworks() -> None:
    left_title = fg(118, 208, 183, "THE JAPANESE FOOTBRIDGE")
    right_title = fg(242, 180, 77, "FLOWER BEDS IN HOLLAND")
    print(f"{BOLD}THE AGENT INSPECTS VISUAL EVIDENCE{RESET}\n")
    print(f"  {left_title:<55} {right_title}")
    print("  ┌────────────────────────┐       ┌────────────────────────┐")
    for left, right in zip(MONET, VAN_GOGH):
        print(f"  │{color_row(left)}│       │{color_row(right)}│")
    print("  └────────────────────────┘       └────────────────────────┘")
    print(f"  {fg(118, 208, 183, 'enclosed • shallow • interwoven'):<63}{fg(242, 180, 77, 'receding • rhythmic • directional')}")
    print(f"\n  {DIM}Palette/composition abstractions; cached observations came from the actual NGA images.{RESET}")


def review() -> None:
    print(f"{BOLD}INDEPENDENT REVIEW GATE{RESET}\n")
    print("  " + badge(78, 105, 155, "EVIDENCE-TAGGED DRAFT"))
    print("                 │")
    print("                 ▼")
    print("  " + badge(174, 73, 62, "80 / 100  NEEDS REVISION") + "  " + fg(224, 128, 112, "missing explicit comparison"))
    print("                 │")
    print("                 ▼")
    print("  " + badge(177, 120, 35, "TARGETED REVISION") + "       " + fg(242, 192, 96, "preserve citations"))
    print("                 │")
    print("                 ▼")
    print("  " + badge(38, 139, 88, "96 / 100  PASSED") + "          " + fg(112, 218, 160, "grounded + complete"))


SCENES = {
    "architecture": architecture,
    "artworks": artworks,
    "review": review,
}


def main() -> None:
    try:
        render = SCENES[sys.argv[1]]
    except (IndexError, KeyError):
        raise SystemExit(f"usage: {sys.argv[0]} [{', '.join(SCENES)}]")
    render()


if __name__ == "__main__":
    main()
