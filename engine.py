import json
import os
import re

def load_data(filename):
    path = os.path.join("data", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("values", data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def safe_float(val, default=0.0):
    try:
        if val is None or val == "": return default
        clean_val = str(val).split('%')[0].strip()
        return float(clean_val)
    except (ValueError, TypeError):
        return default

def get_pick_recommendations(selected_map, selected_names):
    if not selected_map or selected_map == "選択なし": return []
    
    s2_data = load_data("シート2.json")
    s3_data = load_data("シート3.json")
    s_anti_data = load_data("アンチピック係数.json")
    role_data = load_data("キャラ役割.json")
    s_weight = load_data("キャラスコア決め方.json")
    
    if not all([s2_data, s3_data, s_anti_data, role_data, s_weight]): return []

    pick_count = len(selected_names)
    if pick_count < 6: return [] 
    
    p_idx = pick_count - 6 # 0:先1, 1:後1, 2:後2, 3:先2, 4:先3, 5:後3
    if p_idx > 5: return []

    # 重みの取得 (GAS: pickIdx + 2 行目)
    try:
        w_row = s_weight[p_idx + 1] 
        w = {
            "map": safe_float(w_row[2]) / 100, "anti": safe_float(w_row[3]) / 100,
            "e1": safe_float(w_row[4]) / 100, "e2": safe_float(w_row[5]) / 100,
            "e3": safe_float(w_row[6]) / 100, "skill": safe_float(w_row[7]) / 100,
            "ms": safe_float(w_row[8]) / 100
        }
    except: return []

    MAX_TOTAL = 11250
    char_header = s2_data[0]
    map_row = next((r for r in s2_data if r and r[0] == selected_map), None)
    role_names = role_data[0]

    # Pickされたキャラ (index 6以降)
    picks_only = selected_names[6:]
    
    # 敵のインデックスマップ (GAS: enemyPos 完全移植)
    enemy_indices_map = [
        [1, 2, 5], [0, 3, 4], [0, 3, 4], [1, 2, 5], [1, 2, 5], [0, 3, 4]
    ]
    side_indices_map = [
        [0, 3, 4], [1, 2, 5], [1, 2, 5], [0, 3, 4], [0, 3, 4], [1, 2, 5]
    ]
    
    curr_enemies = enemy_indices_map[p_idx]
    curr_sides = side_indices_map[p_idx]

    # 敵キャラ名の特定
    e_names = []
    for idx in curr_enemies:
        name = picks_only[idx] if len(picks_only) > idx else None
        e_names.append(name if name != "選択なし" else None)

    # hasMid 判定
    has_mid = False
    for idx in curr_sides:
        p_name = picks_only[idx] if len(picks_only) > idx else None
        if p_name and p_name in role_names:
            col = role_names.index(p_name)
            if len(role_data) > 31 and str(role_data[31][col]).strip() != "":
                has_mid = True; break

    ranking = []
    for name in char_header[1:]:
        if not name or name in selected_names: continue

        # 1. Map
        f_map = 0.5
        if map_row:
            c_idx = char_header.index(name)
            val_str = str(map_row[c_idx])
            if "(" in val_str and int(re.search(r"\((\d+)\)", val_str).group(1)) <= 100: f_map = 0.1
            else: f_map = max(0.0, min(1.0, (safe_float(val_str) - 40) / 20))

        # 2. Anti (次の行を参照)
        f_anti = 5/9
        for i, row in enumerate(s_anti_data):
            if name in row:
                c_idx = row.index(name)
                if i+1 < len(s_anti_data): f_anti = safe_float(s_anti_data[i+1][c_idx], 5.0) / 9
                break

        # 3. Skill & 4. MS
        f_skill, f_ms = 5/9, 0.5
        if name in role_names:
            c_idx = role_names.index(name)
            f_skill = safe_float(role_data[37][c_idx], 5.0) / 9
            is_m = str(role_data[31][c_idx]).strip() != ""
            is_s = str(role_data[32][c_idx]).strip() != ""
            f_ms = ((9 if is_m else 3) if not has_mid else (9 if is_s else 1)) / 9

        # 5. Affinities
        def get_aff(me, enemy):
            if not enemy or enemy not in s3_data[0]: return 0
            e_col = s3_data[0].index(enemy)
            m_row = next((r for r in s3_data if r[0] == me), None)
            return (safe_float(m_row[e_col], 5.0) / 9) if m_row else 0

        f_e1, f_e2, f_e3 = get_aff(name, e_names[0]), get_aff(name, e_names[1]), get_aff(name, e_names[2])

        total = (f_map*w["map"] + f_anti*w["anti"] + f_skill*w["skill"] + f_ms*w["ms"] + f_e1*w["e1"] + f_e2*w["e2"] + f_e3*w["e3"]) * MAX_TOTAL
        ranking.append({"name": name, "total": round(total, 1), "details": f"M:{int(f_map*MAX_TOTAL*w['map'])} A:{int(f_anti*MAX_TOTAL*w['anti'])} E:{int(f_e1*MAX_TOTAL*w['e1'])}+{int(f_e2*MAX_TOTAL*w['e2'])}+{int(f_e3*MAX_TOTAL*w['e3'])} MS:{int(f_ms*MAX_TOTAL*w['ms'])}"})

    ranking.sort(key=lambda x: x["total"], reverse=True)
    print(f"\n--- {['先1','後1','後2','先2','先3','後3'][p_idx]} ---")
    for r in ranking[:3]: print(f"{r['name']}: {r['total']} ({r['details']})")
    return ranking