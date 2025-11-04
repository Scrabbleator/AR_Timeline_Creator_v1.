# AR.Timeline Creator v1

A lightweight Streamlit app for writers to record and display narrative timelines for novels and worlds — built for Overmorrow and Stelo Vienas, and flexible enough for any project.

Co-produced with ChatGPT (credit optional).

FEATURES:
- Add events with: Title, Date Text (freeform), optional Start/End Date (ISO-like), Era, Story, Characters, Categories, Notes, and a Sort Index.
- Save/Load: Export JSON or CSV; upload JSON to restore.
- Filter & Search by Story, Era, Character, Category, or keyword.
- Two Views: Event Cards (always works) and Timeline Chart (requires Start/End in ISO-like formats: YYYY or YYYY-MM or YYYY-MM-DD).
- Edit/Delete any event in-place.

QUICK START:
1) pip install -r requirements.txt
2) streamlit run AR_Timeline_Creator.py

DATA MODEL (JSON keys): id, title, date_text, start_date, end_date, era, story, characters[], categories[], notes, sort_index.

Tip: If your world uses non-Gregorian calendars, use date_text for display and the numeric sort_index to order items in Event Cards.

ROADMAP: drag & drop ordering; layered views; custom epochs; PDF export.

Credits: Anselm Rajah (Author & Worldbuilder) and ChatGPT (Co-producer).
