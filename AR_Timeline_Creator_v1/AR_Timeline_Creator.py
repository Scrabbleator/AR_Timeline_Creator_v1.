
# AR.Timeline Creator v1
# Author: Anselm Rajah & ChatGPT (Co-produced)
# Description: Minimal Streamlit app to record and display narrative timelines for novels.
# Save/Load: JSON file persisted locally (download/upload).

import json
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="AR.Timeline Creator v1", layout="wide")

# ----------------------- Utilities -----------------------

def safe_parse_date(s: str):
    """Try to parse a date string into a datetime.date (YYYY or YYYY-MM or YYYY-MM-DD). Return None if it fails."""
    if not s:
        return None
    s = s.strip()
    fmts = ["%Y-%m-%d", "%Y-%m", "%Y"]
    for f in fmts:
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            continue
    return None

def ensure_list(s):
    if s is None:
        return []
    if isinstance(s, list):
        return s
    # allow comma separated text
    parts = [p.strip() for p in str(s).split(",") if str(p).strip()]
    # remove empties and dedupe preserving order
    seen = set()
    out = []
    for p in parts:
        if p.lower() not in seen:
            out.append(p)
            seen.add(p.lower())
    return out

def new_event_template() -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": "",
        "date_text": "",           # freeform like "Spring 1842" or "Year 12 – Sepia Age"
        "start_date": "",          # ISO-like "1842" or "1842-05" or "1842-05-17"
        "end_date": "",            # same format as start_date (optional)
        "era": "",
        "story": "",
        "characters": [],          # list[str]
        "categories": [],          # list[str]
        "notes": "",
        "sort_index": 0            # numeric tie-breaker when date is ambiguous
    }

def to_dataframe(events: List[Dict[str, Any]]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(columns=[
            "id","title","date_text","start_date","end_date","era","story","characters","categories","notes","sort_index"
        ])
    df = pd.DataFrame(events)
    # normalize list fields for table display
    df["characters"] = df["characters"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["categories"] = df["categories"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    return df

def filtered_events(all_events: List[Dict[str, Any]], story, era, character, category, keyword) -> List[Dict[str, Any]]:
    def match(ev):
        if story and ev.get("story","").strip() != story:
            return False
        if era and ev.get("era","").strip() != era:
            return False
        if character:
            if character.lower() not in [c.lower() for c in ensure_list(ev.get("characters",[]))]:
                return False
        if category:
            if category.lower() not in [c.lower() for c in ensure_list(ev.get("categories",[]))]:
                return False
        if keyword:
            blob = " ".join([
                ev.get("title",""), ev.get("date_text",""), ev.get("story",""), ev.get("era",""),
                ", ".join(ensure_list(ev.get("characters",[]))), ", ".join(ensure_list(ev.get("categories",[]))),
                ev.get("notes","")
            ]).lower()
            if keyword.lower() not in blob:
                return False
        return True
    return [e for e in all_events if match(e)]

def sorted_events(evts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # sort by parsed start_date, then sort_index, then title
    def key(e):
        d = safe_parse_date(e.get("start_date",""))
        # put None dates later by using a big sentinel
        sentinel = datetime(9999,12,31).date()
        primary = d if d else sentinel
        return (primary, e.get("sort_index", 0), e.get("title","").lower())
    return sorted(evts, key=key)

def download_bytes(data: bytes, filename: str, label: str):
    st.download_button(label, data=data, file_name=filename)

# ----------------------- App State -----------------------

if "events" not in st.session_state:
    st.session_state.events: List[Dict[str, Any]] = []

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# ----------------------- Sidebar -----------------------
with st.sidebar:
    st.markdown("## ⚙️ Save / Load")
    # Export JSON
    json_bytes = json.dumps(st.session_state.events, indent=2).encode("utf-8")
    download_bytes(json_bytes, "AR_Timeline_data.json", "⬇️ Download JSON")
    # Export CSV (flat)
    csv_df = to_dataframe(st.session_state.events)
    download_bytes(csv_df.to_csv(index=False).encode("utf-8"), "AR_Timeline_data.csv", "⬇️ Download CSV")

    # Import JSON
    uploaded = st.file_uploader("Upload JSON to Load/Replace", type=["json"])
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            # basic validation
            if isinstance(data, list):
                st.session_state.events = data
                st.success("Loaded timeline data from JSON.")
            else:
                st.error("Invalid JSON format: expected a list of events.")
        except Exception as e:
            st.error(f"Failed to load JSON: {e}")

    st.markdown("---")
    st.caption("Tip: Keep dates ISO-ish (YYYY or YYYY-MM or YYYY-MM-DD) to unlock the chart view. Use `date_text` for freeform eras.")

# ----------------------- Header -----------------------
st.title("🗓️ AR.Timeline Creator v1")
st.markdown("Co-produced with **ChatGPT** · Designed for **Overmorrow** & **Stelo Vienas** · JSON portable")

# ----------------------- Add / Edit Form -----------------------
st.subheader("Add / Edit Event")

# If editing, prefill fields
editing_event = None
if st.session_state.edit_id:
    editing_event = next((e for e in st.session_state.events if e["id"] == st.session_state.edit_id), None)

col1, col2, col3 = st.columns([2,2,1])
with col1:
    title = st.text_input("Event Title*", value=(editing_event.get("title","") if editing_event else ""))
with col2:
    story = st.text_input("Story (e.g., Overmorrow, Stelo Vienas)", value=(editing_event.get("story","") if editing_event else ""))
with col3:
    era = st.text_input("Era (optional)", value=(editing_event.get("era","") if editing_event else ""))

col4, col5, col6 = st.columns([2,2,1])
with col4:
    start_date = st.text_input("Start Date (YYYY or YYYY-MM or YYYY-MM-DD)", value=(editing_event.get("start_date","") if editing_event else ""))
with col5:
    end_date = st.text_input("End Date (optional; same format)", value=(editing_event.get("end_date","") if editing_event else ""))
with col6:
    sort_index = st.number_input("Sort Index (tie-breaker)", min_value=-100000, max_value=100000, value=(editing_event.get("sort_index",0) if editing_event else 0), step=1)

date_text = st.text_input("Date Text (freeform label, e.g., 'Spring 1842' or 'Year 12 – Sepia Age')", value=(editing_event.get("date_text","") if editing_event else ""))

col7, col8 = st.columns(2)
with col7:
    characters_text = st.text_input("Characters (comma-separated)", value=(", ".join(editing_event.get("characters",[])) if editing_event else ""))
with col8:
    categories_text = st.text_input("Categories/Tags (comma-separated)", value=(", ".join(editing_event.get("categories",[])) if editing_event else ""))

notes = st.text_area("Plot Summary / Notes", value=(editing_event.get("notes","") if editing_event else ""), height=120)

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("💾 Save Event"):
        if not title.strip():
            st.warning("Title is required.")
        else:
            payload = new_event_template()
            if editing_event:
                payload["id"] = editing_event["id"]
            payload.update({
                "title": title.strip(),
                "date_text": date_text.strip(),
                "start_date": start_date.strip(),
                "end_date": end_date.strip(),
                "era": era.strip(),
                "story": story.strip(),
                "characters": ensure_list(characters_text),
                "categories": ensure_list(categories_text),
                "notes": notes.strip(),
                "sort_index": int(sort_index),
            })
            if editing_event:
                st.session_state.events = [payload if e["id"] == editing_event["id"] else e for e in st.session_state.events]
                st.session_state.edit_id = None
                st.success("Event updated.")
            else:
                st.session_state.events.append(payload)
                st.success("Event added.")

with colB:
    if st.button("🧹 Reset Form"):
        st.session_state.edit_id = None
        st.experimental_rerun()

with colC:
    if editing_event and st.button("🗑️ Delete This Event"):
        st.session_state.events = [e for e in st.session_state.events if e["id"] != editing_event["id"]]
        st.session_state.edit_id = None
        st.success("Event deleted.")

st.markdown("---")

# ----------------------- Filters -----------------------
st.subheader("Filter & Search")

all_stories = sorted(set([e.get("story","") for e in st.session_state.events if e.get("story","")]))
all_eras = sorted(set([e.get("era","") for e in st.session_state.events if e.get("era","")]))
all_characters = sorted(set([c for e in st.session_state.events for c in ensure_list(e.get("characters",[]))]))
all_categories = sorted(set([c for e in st.session_state.events for c in ensure_list(e.get("categories",[]))]))

c1, c2, c3, c4, c5 = st.columns([1.2,1.2,1.2,1.2,2])
with c1:
    story_filter = st.selectbox("Story", options=[""] + all_stories, index=0)
with c2:
    era_filter = st.selectbox("Era", options=[""] + all_eras, index=0)
with c3:
    character_filter = st.selectbox("Character", options=[""] + all_characters, index=0)
with c4:
    category_filter = st.selectbox("Category", options=[""] + all_categories, index=0)
with c5:
    keyword = st.text_input("Search keyword")

current = filtered_events(st.session_state.events, story_filter, era_filter, character_filter, category_filter, keyword)
current_sorted = sorted_events(current)

# ----------------------- Views -----------------------
tab1, tab2 = st.tabs(["📋 Event Cards", "📈 Timeline Chart"])

with tab1:
    if not current_sorted:
        st.info("No events match your filters yet. Add an event above.")
    else:
        for ev in current_sorted:
            with st.expander(f"{ev.get('title','(untitled)')} — {ev.get('date_text') or ev.get('start_date') or 'No date'}"):
                colx, coly, colz = st.columns([2,2,1])
                with colx:
                    st.markdown(f"**Story:** {ev.get('story','-')}")
                    st.markdown(f"**Era:** {ev.get('era','-')}")
                    st.markdown(f"**Start:** {ev.get('start_date','-')}")
                    st.markdown(f"**End:** {ev.get('end_date','-')}")
                with coly:
                    st.markdown(f"**Characters:** {', '.join(ensure_list(ev.get('characters',[]))) or '-'}")
                    st.markdown(f"**Categories:** {', '.join(ensure_list(ev.get('categories',[]))) or '-'}")
                    st.markdown(f"**Sort Index:** {ev.get('sort_index',0)}")
                with colz:
                    if st.button("✏️ Edit", key=f"edit_{ev['id']}"):
                        st.session_state.edit_id = ev["id"]
                        st.experimental_rerun()
                    if st.button("🗑️ Delete", key=f"del_{ev['id']}"):
                        st.session_state.events = [e for e in st.session_state.events if e["id"] != ev["id"]]
                        st.experimental_rerun()
                st.markdown("**Date Label:** " + (ev.get("date_text","-") or "-"))
                st.markdown("**Notes:**")
                st.write(ev.get("notes","").strip() or "-")

with tab2:
    # Build a dataframe for chart
    chart_rows = []
    for e in current_sorted:
        sd = safe_parse_date(e.get("start_date",""))
        ed = safe_parse_date(e.get("end_date","")) or sd
        if sd:
            chart_rows.append({
                "Title": e.get("title",""),
                "Start": sd,
                "End": ed,
                "Story": e.get("story",""),
                "Era": e.get("era",""),
                "Category": ", ".join(ensure_list(e.get("categories",[]))) or "Uncategorized"
            })
    if not chart_rows:
        st.info("Add ISO-like dates (YYYY or YYYY-MM or YYYY-MM-DD) to unlock the chart. Otherwise, use Event Cards view.")
    else:
        cdf = pd.DataFrame(chart_rows)
        # pick color by Category to help visual grouping
        fig = px.timeline(
            cdf, x_start="Start", x_end="End", y="Story", color="Category",
            hover_data=["Title","Era"]
        )
        fig.update_yaxes(autorange="reversed")  # timeline convention
        st.plotly_chart(fig, use_container_width=True)

# ----------------------- Footer -----------------------
st.markdown("---")
st.caption("AR.Timeline Creator v1 · Export JSON/CSV · Filter by Story/Era/Character/Category · Edit/Delete entries · Chart view requires ISO-like dates.")
