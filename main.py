import flet as ft
import engine

def main(page: ft.Page):
    page.title = "Brawl Draft App"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    NORMAL_BORDER = ft.Border.all(2, ft.Colors.WHITE24)
    ACTIVE_BORDER = ft.Border.all(5, ft.Colors.WHITE)

    state = {
        "current_step": 0,
        "slots": [],
        "selected_names": [],
        "all_characters": []
    }

    def load_master_data():
        char_data = engine.load_data("キャラ役割.json")
        if char_data:
            state["all_characters"] = [n for n in char_data[0][1:] if n]
    load_master_data()

    def get_map_options():
        rows = engine.load_data("マップ.json")
        if rows:
            return [ft.dropdown.Option(key=r[1], text=r[1]) for r in rows[1:] if len(r) > 1]
        return []

    selection_history = ft.Text("", size=12, color=ft.Colors.WHITE70)
    ranking_list = ft.ListView(expand=True, spacing=5)

    def update_highlights():
        for i, slot in enumerate(state["slots"]):
            if i == state["current_step"]:
                slot.border = ACTIVE_BORDER
                slot.bgcolor = ft.Colors.WHITE10
            else:
                slot.border = NORMAL_BORDER
                slot.bgcolor = ft.Colors.TRANSPARENT
            slot.update()

    def update_ranking_display():
        selected_map = map_dropdown.value
        search_query = search_field.value.lower() if search_field.value else ""
        
        # 1. マップに応じた推奨リストをエンジンから取得
        # state["selected_names"] を渡すことで、今のBAN/Pick状況を反映させる
        recommendations = []
        if selected_map and selected_map != "選択なし":
            recommendations = engine.get_pick_recommendations(selected_map, state["selected_names"])
        
        # 2. 現在表示されているリストを一旦空にする
        ranking_list.controls.clear()
        
        # 推奨がない場合は全キャラをデフォルト表示
        display_list = recommendations if recommendations else [{"name": n, "total": "-"} for n in state["all_characters"]]

        # 3. リストを新しいデータで構築し直す
        for item in display_list:
            name = item["name"]
            if (search_query and search_query not in name.lower()) or name in state["selected_names"]:
                continue

            score_val = item.get("total", "-")
            score_text = f"Score: {score_val}" if score_val != "-" else ""
            
            ranking_list.controls.append(
                ft.ListTile(
                    title=ft.Text(name, size=13, weight="bold"),
                    subtitle=ft.Text(score_text, size=11, color=ft.Colors.WHITE54),
                    on_click=lambda e, n=name: on_char_click({"name": n})
                )
            )
        
        # 4. 重要: 変更をUIに強制反映
        ranking_list.update()
        page.update()

    # --- UIパーツ定義 ---
    map_dropdown = ft.Dropdown(
        options=get_map_options(), 
        width=200, 
        height=45,
        hint_text="Select Map"
    )

    search_field = ft.TextField(
        prefix_icon=ft.Icons.SEARCH_ROUNDED, 
        hint_text="Search...", 
        height=45
    )

    # --- イベント紐付け ---
    # マップを変えた瞬間に「今の枠」のスコアを出し直す
    map_dropdown.on_change = lambda e: update_ranking_display()
    # 検索窓に入力した瞬間にフィルタリング
    search_field.on_change = lambda e: update_ranking_display()

    def on_char_click(char_data):
        if state["current_step"] < len(state["slots"]):
            name = char_data["name"]
            if name in state["selected_names"]: return

            target_slot = state["slots"][state["current_step"]]
            font_size = 10 if state["current_step"] < 6 else 14
            
            target_slot.content = ft.Text(name, size=font_size, weight="bold", text_align="center")
            state["selected_names"].append(name)
            selection_history.value = " > ".join(state["selected_names"])
            selection_history.update()
            
            search_field.value = ""
            search_field.update()
            
            state["current_step"] += 1
            if state["current_step"] < len(state["slots"]):
                update_highlights()
                # キャラを選んだ後も、次の枠のためにランキングを更新
                update_ranking_display()
            page.update()

    def create_slot(size: int):
        return ft.Container(
            content=ft.Text("?", size=size // 3, weight="bold", color=ft.Colors.WHITE10),
            width=size, height=size, 
            alignment=ft.Alignment(0, 0),
            border=NORMAL_BORDER, border_radius=12
        )

    def create_draft_column(title: str, is_ban: bool):
        size = 55 if is_ban else 110
        slots = [create_slot(size) for _ in range(3)]
        return ft.Column([
            ft.Text(title, size=14, weight="w900"),
            ft.Column(slots, spacing=15)
        ], horizontal_alignment="center"), slots

    c_f_b, s_f_b = create_draft_column("BAN", True)
    c_f_p, s_f_p = create_draft_column("先攻", False)
    c_s_p, s_s_p = create_draft_column("後攻", False)
    c_s_b, s_s_b = create_draft_column("BAN", True)

    state["slots"] = [s_f_b[0], s_f_b[1], s_f_b[2], s_s_b[0], s_s_b[1], s_s_b[2], s_f_p[0], s_s_p[0], s_s_p[1], s_f_p[1], s_f_p[2], s_s_p[2]]

    page.add(
        ft.Row([
            ft.Container(
                content=ft.Column([search_field, ft.Text("RECOMMENDED", size=10, color=ft.Colors.WHITE24), ranking_list]),
                width=280, bgcolor="#0A0A0A", padding=20
            ),
            ft.Column([
                ft.Container(
                    content=ft.Row([ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: page.window_reload())], alignment="end"),
                    padding=ft.Padding(0, 20, 30, 0)
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Row([c_f_b, c_f_p], spacing=20),
                        ft.Container(ft.Text("VS", size=80, weight="w900", color=ft.Colors.WHITE10), padding=ft.Padding(40, 0, 40, 0)),
                        ft.Row([c_s_p, c_s_b], spacing=20)
                    ], alignment="center"), expand=True
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(ft.Column([
                            ft.Row([ft.Text("MODE", width=60), ft.Dropdown(width=200, height=45, value="Ranked")]),
                            ft.Row([ft.Text("MAP", width=60), map_dropdown])
                        ]), padding=20),
                        ft.VerticalDivider(width=1, color=ft.Colors.WHITE10),
                        ft.Container(ft.Column([ft.Text("HISTORY", size=12, color=ft.Colors.WHITE24), selection_history]), expand=True, padding=20)
                    ]),
                    height=160, bgcolor="#0D0D0D", border=ft.Border(top=ft.BorderSide(1, ft.Colors.WHITE10))
                )
            ], expand=True)
        ], expand=True)
    )

    update_highlights()
    update_ranking_display()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)