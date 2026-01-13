"""
City Aliases Module
===================
支持大都市区多城市查询的城市别名映射

功能：
- 单个城市扩展为大都市区所有城市
- 解析多目的地字符串 (Miami and Key West)
- 合并多目的地的有效城市集合
"""

import re

# 城市别名映射表
# key: 主城市名, value: 该大都市区的所有城市/地区
CITY_ALIASES: dict[str, list[str]] = {
    # 迈阿密大都市区 (Miami-Fort Lauderdale-Pompano Beach MSA)
    "Miami": [
        "Miami",
        "Miami Beach",
        "Hialeah",
        "Coral Gables",
        "Fort Lauderdale",
        "Hollywood",
        "Pompano Beach",
        "Boca Raton",
        "Deerfield Beach",
        "Aventura",
    ],
    # 佛罗里达群岛 (Florida Keys)
    "Key West": [
        "Key West",
        "Key Largo",
        "Islamorada",
        "Marathon",
        "Big Pine Key",
        "Tavernier",
    ],
    # 奥兰多大都市区 (Orlando-Kissimmee-Sanford MSA)
    "Orlando": [
        "Orlando",
        "Kissimmee",
        "Winter Park",
        "Lake Buena Vista",
        "Sanford",
        "Altamonte Springs",
    ],
    # 坦帕大都市区 (Tampa-St. Petersburg-Clearwater MSA)
    "Tampa": [
        "Tampa",
        "St. Petersburg",
        "Clearwater",
        "Brandon",
        "Largo",
        "Palm Harbor",
    ],
    # 杰克逊维尔大都市区
    "Jacksonville": [
        "Jacksonville",
        "Jacksonville Beach",
        "Neptune Beach",
        "Atlantic Beach",
        "St. Augustine",
    ],
    # 那不勒斯大都市区
    "Naples": [
        "Naples",
        "Marco Island",
        "Bonita Springs",
    ],
    # 西棕榈滩大都市区
    "West Palm Beach": [
        "West Palm Beach",
        "Palm Beach",
        "Delray Beach",
        "Boynton Beach",
    ],
}


def get_city_variations(destination: str) -> list[str]:
    """
    获取单个城市及其大都市区变体列表

    Args:
        destination: 目的地城市名

    Returns:
        该城市所在大都市区的所有城市列表
        如果未找到匹配，返回原始输入

    Example:
        >>> get_city_variations("Miami")
        ["Miami", "Miami Beach", "Hialeah", ...]
        >>> get_city_variations("Unknown City")
        ["Unknown City"]
    """
    dest_lower = destination.lower().strip()

    # 查找完全匹配或别名匹配
    for main_city, aliases in CITY_ALIASES.items():
        if dest_lower == main_city.lower():
            return aliases
        if any(dest_lower == alias.lower() for alias in aliases):
            return aliases

    # 无匹配时返回原始值
    return [destination]


def get_all_valid_cities(destinations: list[str]) -> set[str]:
    """
    获取多个目的地的所有有效城市集合

    Args:
        destinations: 目的地列表，如 ["Miami", "Key West"]

    Returns:
        所有有效城市名（小写）的集合

    Example:
        >>> get_all_valid_cities(["Miami", "Key West"])
        {"miami", "miami beach", "hialeah", ..., "key west", "key largo", ...}
    """
    valid_cities: set[str] = set()
    for dest in destinations:
        variations = get_city_variations(dest)
        valid_cities.update(c.lower() for c in variations)
    return valid_cities


def parse_destination(destination: str) -> list[str]:
    """
    解析目的地字符串，支持多种格式

    支持格式:
    - "Miami" → ["Miami"]
    - "Miami and Key West" → ["Miami", "Key West"]
    - "Miami, Key West" → ["Miami", "Key West"]
    - "Miami/Key West" → ["Miami", "Key West"]
    - "Miami & Key West" → ["Miami", "Key West"]

    Args:
        destination: 原始目的地字符串

    Returns:
        解析后的目的地列表

    Example:
        >>> parse_destination("Miami and Key West")
        ["Miami", "Key West"]
    """
    if not destination:
        return []

    # 按常见分隔符拆分: "and", ",", "/", "&"
    parts = re.split(r"\s+and\s+|,\s*|/\s*|\s*&\s*", destination, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]
