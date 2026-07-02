"""Mock POI data for testing without Amap API keys."""

from __future__ import annotations

import hashlib


def generate_mock_pois(
	keywords: str = "",
	city: str = "杭州",
	types: str = "",
	limit: int = 10,
	page: int = 1,
) -> tuple[list[dict], int]:
	"""Return deterministic mock POI records for a search."""
	base_names = {
		"奶茶": ["喜茶", "奈雪的茶", "CoCo都可", "古茗", "茶百道"],
		"美容": ["美丽人生美容院", "丝域养发", "克丽缇娜", "樊文花"],
		"餐饮": ["外婆家", "绿茶餐厅", "新白鹿", "弄堂里"],
	}

	names = base_names.get(keywords) or [
		f"{keywords or '示例'}{suffix}"
		for suffix in ["一号店", "二号店", "三号店", "四号店", "五号店"]
	]

	districts = ["西湖区", "拱墅区", "余杭区", "滨江区", "上城区"]
	all_pois = []

	for index, name in enumerate(names):
		poi_id = _make_id(keywords, city, name, index)
		district = districts[index % len(districts)]
		lng = 120.10 + index * 0.02
		lat = 30.20 + index * 0.01
		tel = f"138{index:04d}{10000 + index:05d}"[-11:]

		all_pois.append(
			{
				"id": poi_id,
				"name": f"{name}({city}{district})",
				"tel": tel if index % 4 != 3 else "",
				"address": f"{city}{district}文一西路{100 + index}号",
				"location": f"{lng:.6f},{lat:.6f}",
				"type": keywords or "餐饮服务",
				"typecode": (types.split("|")[0] if types else "050000"),
				"pname": "浙江省",
				"cityname": city,
				"adname": district,
			}
		)

	total = len(all_pois)
	page_size = min(limit, 25)
	start = (page - 1) * page_size
	end = start + page_size
	return all_pois[start:end], total


def _make_id(keywords: str, city: str, name: str, index: int) -> str:
	raw = f"{keywords}|{city}|{name}|{index}"
	return hashlib.md5(raw.encode()).hexdigest()[:16].upper()
