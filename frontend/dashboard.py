import streamlit as st
import pandas as pd
import os
from backend.media_service import search_external_media
from backend.db_operations import (
    save_user_like,
    like_existing_media,
    get_user_likes,
    get_user_list_items,
    add_to_list_workflow,
    add_existing_to_list,
    submit_rating,
    get_search_gallery,
    get_top_rated_genres,
    get_user_activity_level,
    get_format_popularity,
    get_hidden_gems,
    get_audit_stats,
    add_tag_to_media,
    get_similar_media,
    get_user_recommendations,
    get_user_theme_weights,
    refresh_all_recommendations,
    get_advanced_analytics,
    get_db_stats,
    get_full_audit_log,
    generate_recommendations_for_user,
)

# ── Constants ─────────────────────────────────────────────────────────
TYPE_COLORS = {"movie": "#b9e6ff", "book": "#f7b3d3", "music": "#c6f7d4"}
TYPE_ICONS  = {"movie": "🎬",      "book": "📖",       "music": "🎵"}
LIST_MAP    = {"movie": "watchlist","book": "readlist", "music": "playlist"}

def _accent(type_name):
    return TYPE_COLORS.get((type_name or "").lower(), "#dddddd")

def _icon(type_name):
    return TYPE_ICONS.get((type_name or "").lower(), "•")

def _load_css():
    css_path = os.path.join("frontend", "theme.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Shared card renderer ──────────────────────────────────────────────
def _media_card(title, type_name, year, genre, desc=None, score=None):
    color = _accent(type_name)
    icon  = _icon(type_name)

    score_part = (
        "<span style=\"float:right;color:{c};font-size:11px;font-weight:600;\">&#9733; {s}</span>".format(
            c=color, s="{:.1f}".format(score))
        if score is not None else ""
    )
    desc_part = ""
    if desc:
        safe = desc[:160].replace("<", "&lt;").replace(">", "&gt;")
        ellipsis = "&#8230;" if len(desc) > 160 else ""
        desc_part = "<p style=\"color:#777;font-size:13px;margin:8px 0 0 0;line-height:1.5;\">{}{}</p>".format(safe, ellipsis)

    parts = [
        "<div class=\"media-card\">",
        "<div style=\"display:flex;justify-content:space-between;align-items:flex-start;\">",
        "<p style=\"color:{c};font-size:11px;letter-spacing:1px;margin:0 0 4px 0;\">{i} {g}</p>".format(
            c=color, i=icon, g=(genre or "").upper()),
        score_part,
        "</div>",
        "<h3 style=\"font-family:Georgia,serif;font-size:22px;font-weight:400;margin:0 0 2px 0;\">{}</h3>".format(title),
        "<p style=\"color:#555;font-size:12px;letter-spacing:1px;margin:0;\">{} &nbsp;&middot;&nbsp; {}</p>".format(
            (type_name or "").upper(), year),
        desc_part,
        "</div>",
    ]
    st.markdown("".join(parts), unsafe_allow_html=True)

# ── Taste profile pills ───────────────────────────────────────────────
def _taste_pills(themes):
    genres = [t for t in themes if t['category'] == 'Genre'][:6]
    tags   = [t for t in themes if t['category'] == 'Tag'][:4]
    if not genres and not tags:
        return
    pills = ""
    PILL_STYLE = "background:#1a1a1a;border-radius:20px;padding:3px 12px;font-size:11px;margin:3px;display:inline-block;"
    for g in genres:
        pills += "<span style=\"{s}border:1px solid #f7b3d3;color:#f7b3d3;\">{v}</span>".format(
            s=PILL_STYLE, v=g['theme'])
    for t in tags:
        pills += "<span style=\"{s}border:1px solid #c6f7d4;color:#c6f7d4;\"># {v}</span>".format(
            s=PILL_STYLE, v=t['theme'])
    st.markdown("<div style=\"margin:8px 0 16px 0;\">{}</div>".format(pills), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
def dashboard():
    _load_css()

    # ── Sidebar ───────────────────────────────────────────────────────
    with st.sidebar:
        logo_path = os.path.join("frontend", "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)
        else:
            st.markdown(
                "<h2 style=\"font-family:Georgia,serif;font-weight:400;\">Vault.</h2>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        user = st.session_state.user

        # User badge
        badge = (
            "<div style=\"background:#111;border:1px solid #222;border-radius:12px;"
            "padding:10px 14px;margin-bottom:16px;\">"
            "<p style=\"margin:0;font-size:13px;color:#aaa;\">Logged in as</p>"
            "<p style=\"margin:0;font-size:15px;font-weight:500;\">{name}</p>"
            "<p style=\"margin:0;font-size:11px;color:#555;letter-spacing:1px;\">{role}</p>"
            "</div>"
        ).format(name=user['name'], role=user['role'].upper())
        st.markdown(badge, unsafe_allow_html=True)

        if user['role'] == 'admin':
            st.markdown("---")
            st.caption("ADMIN TOOLS")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ── Route admins directly to admin panel ──────────────────────────
    user = st.session_state.user
    if user['role'] == 'admin':
        show_admin_panel()
        return

    # ── Page header ───────────────────────────────────────────────────
    first_name = user['name'].split()[0]
    st.markdown(
        "<h1 style=\"font-family:Georgia,serif;font-size:58px;font-weight:400;margin-bottom:0;line-height:1.1;\">Hello, {}.</h1>"
        "<div class=\"rainbow-bar\" style=\"width:100%;height:3px;margin:12px 0 32px 0;\"></div>".format(first_name),
        unsafe_allow_html=True
    )

    tab_search, tab_vault, tab_recs = st.tabs(["DISCOVER", "MY VAULT", "FOR YOU"])

    # ══════════════════════════════════════════════════════════════════
    # TAB 1 — DISCOVER
    # ══════════════════════════════════════════════════════════════════
    with tab_search:
        st.markdown(
            "<p style=\"color:#666;font-size:13px;letter-spacing:1px;\">SEARCH ACROSS MOVIES, BOOKS & MUSIC</p>",
            unsafe_allow_html=True
        )

        col_q, col_t = st.columns([4, 1])
        with col_q:
            query = st.text_input("search", placeholder="e.g. Inception, Dune, After Hours…",
                                  label_visibility="collapsed")
        with col_t:
            m_type = st.selectbox("type", ["movie", "book", "music"],
                                  label_visibility="collapsed",
                                  format_func=lambda x: f"{_icon(x)} {x.capitalize()}")

        if query:
            with st.spinner("Searching…"):
                results = search_external_media(query, m_type)

            if not results:
                st.info("No results found. Try a different search term.")
            else:
                for item in results:
                    _media_card(
                        title=item['title'],
                        type_name=item['type'],
                        year=item['year'],
                        genre=item.get('genre', 'General'),
                        desc=item.get('desc', ''),
                    )

                    save_key    = f"saved_{item['external_id']}"
                    target_list = LIST_MAP.get(item['type'], "watchlist")

                    if save_key in st.session_state:
                        st.success("✓ Saved to Favorites")
                        r_col, s_col = st.columns([2, 1])
                        with r_col:
                            new_rating = st.select_slider(
                                "Your rating",
                                options=[1, 2, 3, 4, 5],
                                format_func=lambda x: "★" * x,
                                key=f"rate_val_{item['external_id']}"
                            )
                        with s_col:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Submit rating", key=f"rate_btn_{item['external_id']}"):
                                res = submit_rating(user['id'], st.session_state[save_key], new_rating)
                                st.toast(f"Rated {'★' * new_rating}") if res is True else st.error(res)
                    else:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("♥  Add to Favorites", key=f"fav_{item['external_id']}",
                                         use_container_width=True):
                                try:
                                    mid = save_user_like(user['id'], item)
                                    st.session_state[save_key] = mid
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                        with c2:
                            if st.button(f"+ {target_list.capitalize()}", key=f"list_{item['external_id']}",
                                         use_container_width=True):
                                res = add_to_list_workflow(user['id'], item, target_list)
                                st.toast(f"Added to {target_list}!") if res is True else st.warning(res)

                    st.markdown("<div style=\"height:8px\"></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # TAB 2 — MY VAULT
    # ══════════════════════════════════════════════════════════════════
    with tab_vault:
        view_mode = st.radio(
            "view",
            ["Favorites", "Watchlist", "Readlist", "Playlist"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("<div style=\"height:16px\"></div>", unsafe_allow_html=True)

        items = (
            get_user_likes(user['id'])
            if view_mode == "Favorites"
            else get_user_list_items(user['id'], view_mode.lower())
        )

        if not items:
            empty_icons = {"Favorites": "&#9829;", "Watchlist": "&#127916;", "Readlist": "&#128214;", "Playlist": "&#127925;"}
            st.markdown(
                "<div style=\"text-align:center;padding:60px 0;color:#444;\">"
                "<p style=\"font-size:40px;margin:0;\">{}</p>"
                "<p style=\"font-size:15px;margin:12px 0 0 0;\">Your {} is empty.</p>"
                "<p style=\"font-size:13px;color:#333;\">Head to Discover to add some.</p>"
                "</div>".format(empty_icons[view_mode], view_mode),
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"<p style=\"color:#555;font-size:12px;letter-spacing:1px;\">{len(items)} ITEMS</p>",
                        unsafe_allow_html=True)
            for idx, item in enumerate(items):
                type_name  = item.get('type_name', 'media')
                color      = _accent(type_name)
                icon       = _icon(type_name)
                unique_key = f"{view_mode}_{idx}_{item['media_id']}"

                row_html = (
                    "<div style=\"border-bottom:1px solid #141414;padding:16px 0;"
                    "display:flex;align-items:center;gap:14px;\">"
                    "<span style=\"color:{c};font-size:18px;\">{i}</span>"
                    "<div style=\"flex:1;\">"
                    "<span style=\"font-size:17px;font-weight:500;\">{t}</span><br>"
                    "<span style=\"color:#555;font-size:11px;letter-spacing:1px;\">"
                    "{tt} &nbsp;&middot;&nbsp; {y}"
                    "</span></div></div>"
                ).format(c=color, i=icon, t=item['title'],
                         tt=type_name.upper(), y=item.get('year','N/A'))
                st.markdown(row_html, unsafe_allow_html=True)

                with st.expander(f"Details & actions — {item['title']}"):
                    t1, t2 = st.columns(2)

                    with t1:
                        st.caption("Add a custom tag")
                        new_tag = st.text_input("tag", label_visibility="collapsed",
                                                key=f"tag_in_{unique_key}",
                                                placeholder="e.g. Dystopian, Cozy…")
                        if st.button("Add Tag", key=f"tag_btn_{unique_key}"):
                            if new_tag.strip():
                                res = add_tag_to_media(user['id'], item['media_id'], new_tag.strip())
                                st.success(f"Tagged as '{new_tag}'!") if res is True else st.error(res)
                            else:
                                st.warning("Enter a tag name first.")

                    with t2:
                        st.caption("More like this")
                        similar = get_similar_media(item['media_id'])
                        if similar:
                            for s in similar:
                                sc = _accent(s['type_name'])
                                sim_html = (
                                    "<span style=\"color:{c}\">&#8594;</span> "
                                    "<strong>{t}</strong> "
                                    "<span style=\"color:#555;font-size:11px;\">({})</span>"
                                ).format(s["type_name"], c=sc, t=s["title"])
                                st.markdown(sim_html, unsafe_allow_html=True)
                        else:
                            st.caption("No similar items found yet.")

    # ══════════════════════════════════════════════════════════════════
    # TAB 3 — FOR YOU
    # ══════════════════════════════════════════════════════════════════
    with tab_recs:
        themes = get_user_theme_weights(user['id'])
        if themes:
            st.markdown(
                "<p style=\"color:#555;font-size:12px;letter-spacing:1px;margin-bottom:4px;\">YOUR TASTE PROFILE</p>",
                unsafe_allow_html=True
            )
            _taste_pills(themes)
        else:
            st.info("Like some media in Discover to build your taste profile and get recommendations.")

        st.markdown("<div style=\"height:8px\"></div>", unsafe_allow_html=True)

        recs = get_user_recommendations(user['id'])

        if not recs:
            st.markdown(
                "<div style=\"text-align:center;padding:48px 0;color:#444;\">"
                "<p style=\"font-size:36px;margin:0;\">&#127919;</p>"
                "<p style=\"font-size:15px;margin:12px 0 4px 0;\">No recommendations yet.</p>"
                "<p style=\"font-size:13px;color:#333;\">Like at least one item in Discover to get started.</p>"
                "</div>",
                unsafe_allow_html=True
            )
            if themes:
                if st.button("🔄 Generate Recommendations Now"):
                    with st.spinner("Generating…"):
                        result = generate_recommendations_for_user(user['id'])
                    if result is True:
                        st.rerun()
                    else:
                        st.error(result)
        else:
            st.markdown(
                f"<p style=\"color:#555;font-size:12px;letter-spacing:1px;\">{len(recs)} PICKS FOR YOU</p>",
                unsafe_allow_html=True
            )

            for rec in recs:
                _media_card(
                    title=rec['title'],
                    type_name=rec['type_name'],
                    year=rec['year'],
                    genre=rec['genres'],
                    desc=rec.get('desc', ''),
                    score=rec['score'],
                )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("♥  Add to Favorites", key=f"fav_rec_{rec['media_id']}",
                                 use_container_width=True):
                        res = like_existing_media(user['id'], rec['media_id'])
                        if res is True:
                            st.toast("Added to Favorites!")
                            st.rerun()
                        else:
                            st.error(res)
                with c2:
                    target_list = LIST_MAP.get(rec['type_name'], "watchlist")
                    if st.button(f"+ {target_list.capitalize()}", key=f"list_rec_{rec['media_id']}",
                                 use_container_width=True):
                        res = add_existing_to_list(user['id'], rec['media_id'], target_list)
                        if res is True:
                            st.toast(f"Added to {target_list}!")
                            st.rerun()
                        else:
                            st.error(res)

                st.markdown("<div style=\"height:8px\"></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════
def show_admin_panel():
    st.markdown(
        "<h1 style=\"font-family:Georgia,serif;font-weight:400;\">Admin Dashboard</h1>",
        unsafe_allow_html=True
    )

    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "System Control", "Basic Analytics", "Advanced Analytics", "Audit Logs"
    ])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.caption("RECOMMENDATION ENGINE")
            if st.button("🔄 Refresh All User Recommendations", use_container_width=True):
                with st.spinner("Regenerating…"):
                    result = refresh_all_recommendations()
                st.success("✅ All recommendations refreshed!") if result is True else st.error(result)

        with col2:
            st.caption("DATABASE STATISTICS")
            stats = get_db_stats()
            m1, m2 = st.columns(2)
            m1.metric("Users",   stats["users"])
            m1.metric("Likes",   stats["likes"])
            m2.metric("Media",   stats["media"])
            m2.metric("Ratings", stats["ratings"])

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.caption("TOP RATED GENRES")
            data = get_top_rated_genres()
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True) if data else st.caption("No data.")

        with col2:
            st.caption("FORMAT POPULARITY")
            data = get_format_popularity()
            st.bar_chart(pd.DataFrame(data).set_index("Format")) if data else st.caption("No data.")

        st.markdown("<div style=\"height:16px\"></div>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.caption("USER LEADERBOARD")
            data = get_user_activity_level()
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True) if data else st.caption("No data.")

        with col4:
            st.caption("HIDDEN GEMS")
            data = get_hidden_gems()
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True) if data else st.caption("No data.")

    with tab3:
        a1, a2, a3 = st.tabs(["Media Distribution", "User Activity Cube", "Genre Hierarchy"])

        with a1:
            st.caption("Multi-dimensional analysis using GROUPING SETS")
            data = get_advanced_analytics('distribution')
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True) if data else st.info("No data yet.")

        with a2:
            st.caption("User activity using CUBE")
            data = get_advanced_analytics('activity_cube')
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True) if data else st.info("No data yet.")

        with a3:
            st.caption("Hierarchical genre stats using ROLLUP")
            data = get_advanced_analytics('genre_hierarchy')
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True) if data else st.info("No data yet.")

    with tab4:
        with st.expander("Media Search Gallery"):
            gallery = get_search_gallery()
            st.dataframe(pd.DataFrame(gallery), hide_index=True, use_container_width=True) if gallery else st.caption("Empty.")

        st.caption("RECENT AUDIT EVENTS")
        logs = get_full_audit_log()
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True) if logs else st.info("No logs yet.")