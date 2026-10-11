# Vendored Premier League data

Source: [football-data.co.uk England results and odds](https://www.football-data.co.uk/englandm.php)

These are the source `E0.csv` files for the seven completed seasons from 2019/20 through 2025/26, copied on 2026-10-11. Source URLs follow `https://www.football-data.co.uk/mmz4281/{season}/E0.csv`.

| Season | File | Rows |
|---|---|---:|
| 2019/20 | `1920-E0.csv` | 380 |
| 2020/21 | `2021-E0.csv` | 380 |
| 2021/22 | `2122-E0.csv` | 380 |
| 2022/23 | `2223-E0.csv` | 380 |
| 2023/24 | `2324-E0.csv` | 380 |
| 2024/25 | `2425-E0.csv` | 380 |
| 2025/26 | `2526-E0.csv` | 380 |

Do not download these files during tests or CI. Historical closing odds are training/evaluation labels; they are never executable live prices. See `python/providers/football_data_uk.py` for the point-in-time availability rule.
