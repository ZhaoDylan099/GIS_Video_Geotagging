import panel as pn
import pandas as pd
import ipyleaflet as ipyl
import sounddevice as sd 
import sys
import numpy as np
import wavio as wv
import psycopg2
import whisper
import os
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pgvector.psycopg2 import register_vector
from gpt4all import GPT4All

llm_model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")


model_st = SentenceTransformer("all-MiniLM-L6-v2")


VIDEO_URL = "http://localhost/newburgheights_dash_video.mp4"
CSV_FILE  = "newburgheights_dash_video_gps.csv"
NARRATIVE_FILE = "newburgheights_dash_video_narrative.csv"

TIME_COL = "media time"
LAT_COL  = "latitude"
LON_COL  = "longitude"
ZOOM_START = 15



audio_buffer = []
samplerate = 44100
channels = 2
dtype = np.float32

# May differ between devices
sd.default.device = (1, 3)
print(sd.query_devices())

# Adjust for your database configurations
conn = psycopg2.connect("dbname=GIS_Video_Geotagging user=postgres password=123123 host=localhost")

register_vector(conn)
cur = conn.cursor()

engine = create_engine(
    "postgresql+psycopg2://",
    creator=lambda: conn
)

pn.extension('ipywidgets', design='material')

# ---------------- VIDEO ----------------

video_pane = pn.pane.Video(VIDEO_URL, width=700, height=500)
time_display = pn.pane.Markdown("### 0.00 sec")

def update_time():
    time_display.object = f"### {video_pane.time:.2f} sec"

pn.state.add_periodic_callback(update_time, 200)

# ---------------- DATA ----------------

gps = pd.read_csv(CSV_FILE)

def time_to_seconds(t):
    h, m, s = map(float, t.split(":"))
    return h*3600 + m*60 + s

gps["time_seconds"] = gps[TIME_COL].apply(time_to_seconds)

narrative = pd.read_csv(NARRATIVE_FILE)

def seconds_to_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    s = s % 60
    return f"{h:02}:{m:02}:{s:05.2f}"

narrative["Media Time"] = narrative["st_time"].apply(seconds_to_time)
narrative.rename(columns={"text": "Transcript"}, inplace=True)
narrative["Active"] = ""
    



# ---------------- MAP ----------------

def get_current_location(t=None):
    t = video_pane.time if t is None else t
    idx = (gps["time_seconds"] - t).abs().idxmin()
    row = gps.loc[idx]
    return float(row[LAT_COL]), float(row[LON_COL])

lat, lon = get_current_location()


m = ipyl.Map(center=(lat, lon), zoom=ZOOM_START, scroll_wheel_zoom=True)
m.layout.height = "500px"
m.layout.width = "700px"

marker = ipyl.CircleMarker(location=(lat, lon), radius=7, color="red", fill=True, fill_color="red", fill_opacity=0.7)
m.add_layer(marker)


legend = ipyl.LegendControl(
    {
        "GPS Synced Point": "red",
        "Original Transcript Search Results": "blue",
        "Added Transcript Search Results": "green"
    },
    name="Legend",
    position="bottomright"
)

m.add_control(legend)
map_pane = pn.pane.IPyWidget(m, width=700, height=500)

# ---------------- GPS SYNC ----------------

def update_marker(event):
    lat, lon = get_current_location(event.new)
    marker.location = (lat, lon)

video_pane.param.watch(update_marker, "time")

#---------------- NARRATIVE ----------------

transcript_table = pn.pane.DataFrame(
    narrative[["Active","Media Time", "Transcript"]],
    height=500, width=700                
)


def update_transcript(event=None):
    t = float(video_pane.time)

    # Find first row where time falls inside window
    rows = narrative[narrative["st_time"] <= t]

    index = -1
    if rows.empty == False:

        index = rows.index[-1]
    df = narrative.copy()
    df["Active"] = ""

    if index != -1:
        df.loc[index, "Active"] = "▶ CURRENT"

    t_input = Search.value.strip().lower()

    if t_input:

        df = df[df["Transcript"].str.contains(t_input)]


    # Force UI update with a NEW object ref

    transcript_table.object = df[["Active", "Media Time", "Transcript"]]

    

Search = pn.widgets.TextInput(name='Search', placeholder='Search...')

pn.state.add_periodic_callback(update_transcript, 250)
video_pane.param.watch(update_transcript, "time") 
Search.param.watch(update_transcript, 'value')

# -----------  Plot Search -----------

plot_button = pn.widgets.Button(name='Plot Results', button_type='primary')

def plot_search(event):
    if not event:
        return
    
    to_remove = []

    for layer in m.layers:
        # keep basemap + the marker we want to keep
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker and hasattr(layer, "original"):
            to_remove.append(layer)
        
    for layer in to_remove:
        m.remove_layer(layer)
    
    df = narrative.copy()

    times = df[df["Transcript"].str.contains(Search.value)].st_time.tolist()

    


    for i in times:
        lat = gps[gps["time_seconds"] == i]["latitude"].tolist()
        lon = gps[gps["time_seconds"] == i]["longitude"].tolist()

        if lat:
            dot = ipyl.CircleMarker(
                
                location=(lat[0], lon[0]),
                radius=8,
                color="black",
                fill=True,
                fill_color="blue",
                opacity=0.8,
                fill_opacity=0.8
            )
            dot.original = True

            m.add_layer(dot)

plot_button.on_click(plot_search)

clear_plot_button = pn.widgets.Button(name = "Clear Plot", button_type = "primary")

def clear_search(event):

    to_remove = []

    for layer in m.layers:
        # keep basemap + the marker we want to keep
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker and hasattr(layer, "original"):
            to_remove.append(layer)
        
    for layer in to_remove:
        m.remove_layer(layer)

clear_plot_button.on_click(clear_search)

# ---------- Audio Recording ---------

recording_status = pn.pane.Markdown("### 🔴 **Not Recording**")
record_button = pn.widgets.Button(name= 'Record', button_type = "primary")
stop_button = pn.widgets.Button(name="Stop Recording", button_type="danger", disabled=True)
playback = pn.pane.Audio(None, name='Audio')
record_id = None
save_recording = pn.widgets.Button(name="Save Recording", button_type = "primary", disabled = True)
audio_retrieval = pn.widgets.Button(name="Retrieve Audio", button_type = "primary")
audio_id_input = pn.widgets.TextInput(name="Audio ID", placeholder = "ID", width = 300)
model = whisper.load_model("large") 


def reflect_db():
    sql = """SELECT * FROM recordings"""

    df = pd.read_sql_query(sql, engine)

    df["Timestamp"] = df["time_s"].apply(seconds_to_time)
    df.rename(columns = {"transcript": "Transcript", "audioid": "ID"}, inplace=True)

    df = df[["ID", "Timestamp", "Transcript"]]

    return df



new_transcript_df = pn.pane.DataFrame(reflect_db(),
                    height=300, width=700)

stream = None

db_audio = pd.DataFrame(columns=["ID","Timestamp", "Transcript"])

def callback(indata, frames, time, status):
    
    if status:
        print(status, file=sys.stderr)

    audio_buffer.append(indata.copy())  # store incoming audio chunk


def record_audio(event):
    global stream, audio_buffer
    audio_buffer = []
    playback.object = None
    stream = sd.InputStream(samplerate=samplerate, channels=channels, dtype=dtype, callback=callback)

    stream.start()
    recording_status.object = "### 🟢 **Recording...**"
    record_button.disabled = True
    stop_button.disabled = False
    save_recording.disabled = True
    audio_retrieval.disabled = True


def stop_recording(event):
    global stream, audio_buffer

    stream.stop()
    stream.close()

    audio = np.concatenate(audio_buffer, axis=0)
    recording_status.object = "### 🔴 **Stopped Recording**"

    stop_button.disabled = True
    record_button.disabled = False
    save_recording.disabled = False
    audio_retrieval.disabled = False
    
    wv.write("recording.wav", audio, samplerate, sampwidth=2)
    playback.object = "recording.wav"

record_button.on_click(record_audio)
stop_button.on_click(stop_recording)

def transcribe_audio():
    result = model.transcribe(playback.object)
    return result["text"]





def audio_to_db(event):

    sql = """ INSERT INTO recordings (time_s, audio, sample_rate, channels, transcript, embedding)  
    VALUES (%s, %s, %s, %s, %s, %s) 
    RETURNING audioID; """
    

    with open("recording.wav", "rb") as f:
        wav_bytes = f.read()


    try:

        recording_status.object = "### Saving Recording..."

        result = transcribe_audio()
        cur.execute(
            sql,
            (round(video_pane.time), psycopg2.Binary(wav_bytes), samplerate, channels, result, model_st.encode(result))
        )

        record_id = cur.fetchone()[0]

        conn.commit()

        
        new_transcript_df.object = None
        new_transcript_df.object = reflect_db()


        recording_status.object = f"### ✅ Recording Saved with ID: {record_id}"
        

    except:
        conn.rollback()
        recording_status.object = "### ❌ Recording failed to Save"

    

def retrieve_audio(event):

    save_recording.disabled = True
    sql = """ SELECT audio FROM recordings
                WHERE audioID = %s"""
    
    id = audio_id_input.value
    try:
        cur.execute(sql, (id,))
        wav_bytes = cur.fetchone()[0]

        with open("recording.wav", "wb") as f:
            f.write(wav_bytes)

        recording_status.object = "### ✅ Audio Retrieved"
        playback.object = None
        playback.object = "recording.wav"
    except:
        conn.rollback()
        recording_status.object = "### ❌ Audio Retrieval Failed: ID not found"


save_recording.on_click(audio_to_db)
audio_retrieval.on_click(retrieve_audio)

# ------------ Search Added ----------

search_add_box = pn.widgets.TextInput(name='Search', placeholder='Search...')
plot_added = pn.widgets.Button(name="Plot Results", button_type="primary")
clear_added = pn.widgets.Button(name="Clear Plot", button_type = "primary")

def filter_added(event=None):
    df  = reflect_db().copy()
    if search_add_box.value is not None:

        t_input = search_add_box.value.strip().lower()
    
        df = df[df["Transcript"].str.contains(t_input)]

    new_transcript_df.object = df

pn.state.add_periodic_callback(filter_added, 250)
search_add_box.param.watch(filter_added, 'value')
search_add_box.param.watch(filter_added, 'value')

def plot_added_map(event):
    if not event:
        return
    
    to_remove = []

    for layer in m.layers:
        # keep basemap + the marker we want to keep
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker and hasattr(layer, "added"):
            to_remove.append(layer)
        
    for layer in to_remove:
        m.remove_layer(layer)
    
    df = new_transcript_df.object.copy()


    df = df[df["Transcript"].str.contains(search_add_box.value)]

    df["time_s"] = df["Timestamp"].apply(time_to_seconds)

    times = df.time_s.tolist()


    for i in times:
        lat = gps[gps["time_seconds"] == i]["latitude"].tolist()
        lon = gps[gps["time_seconds"] == i]["longitude"].tolist()

        if lat:
            dot = ipyl.CircleMarker(
                
                location=(lat[0], lon[0]),
                radius=8,
                color="black",
                fill=True,
                fill_color="green",
                opacity=0.8,
                fill_opacity=0.8
            )
            dot.added = True
            m.add_layer(dot)

def clear_added_plot(event):

    to_remove = []

    for layer in m.layers:
        # keep basemap + the marker we want to keep
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker and hasattr(layer, "added"):
            to_remove.append(layer)
        
    for layer in to_remove:
        m.remove_layer(layer)

plot_added.on_click(plot_added_map)
clear_added.on_click(clear_added_plot)



# ------------- Embedding ------------
semantic_status = pn.pane.Markdown("### Semantic search idle", width=400)
embed = input("Has embedding happened? (y/n): ")

if embed == "n":
    text = narrative["Transcript"].tolist()

    embeddings = model_st.encode(text, normalize_embeddings=True)

    for time_s, text, embedding in zip(narrative["st_time"].to_list(), narrative["Transcript"], embeddings):
        cur.execute(
            "INSERT INTO embedding (time_s, transcript, embedding) VALUES (%s, %s, %s)",
            (time_s, text, embedding.tolist())
        )
    conn.commit()


# ----------- Semantic Search --------
query_og = pn.widgets.TextInput(name='Query', placeholder='Query...')
score_og_df = pn.pane.DataFrame(narrative[["Media Time", "Transcript"]])
export_scores = pn.widgets.Button(name="Export Search Scores", button_type = "primary")


def expand_query(user_query):
    prompt = f"""
                    You are helping search inside VIDEO TRANSCRIPTS.

                    Rules:
                    - DO NOT invent objects, scenes, or visual elements
                    - DO NOT assume anything not stated
                    - ONLY add synonyms and closely related phrases
                    - Stay literal and grounded
                    - Output ONE short expanded query

                    Original query:
                    "{user_query}"""
    
    response = llm_model.generate(prompt)
    augmented_query = response.strip()

    return augmented_query

def semantic_search_og(event):
    semantic_status.object = "### 🔄 Semantic search running..."

    query = query_og.value


    expanded_query= expand_query(query)
    expanded_query_embedding = model_st.encode(expanded_query).tolist()

    threshold = 0.2  # smaller distance = more similar
    cur.execute("""
        SELECT audioID, time_s, transcript, embedding <=> %s::vector AS distance
        FROM embedding
    
        ORDER BY distance
    """, (expanded_query_embedding,))

    
    rows = cur.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["ID", "time_s", "Transcript", "distance"])
        df["Timestamp"] = df["time_s"].apply(seconds_to_time)
        # 1️⃣ Scale distances to 0-1 using min-max
        min_d = df["distance"].min()
        max_d = df["distance"].max()

        df["similarity"] = 1 - (df["distance"] - min_d) / (max_d - min_d)  # 0 = worst, 1 = best

        # 2️⃣ Apply sigmoid to exaggerate differences
        alpha = 10  # controls steepness
        df["Score"] = 1 / (1 + np.exp(-alpha * (df["similarity"] - 0.5)))  # 0-1

        # 3️⃣ Convert to 0-100
        df["Score"] = (df["Score"] * 100).round(2)
        df = df[["ID", "Timestamp", "Transcript", "Score"]]
                
    else:
        df = pd.DataFrame(columns=["ID", "Timestamp", "Transcript", "Score"])
    score_og_df.object = df

    semantic_status.object = f"### ✅ Semantic search complete"

    
def export_semantics(event):
    score_og_df.object.to_csv("semantic_scores.csv")

query_og.param.watch(semantic_search_og, 'value')
export_scores.on_click(export_semantics)

# -------------- Cleanup -------------


def session_destroyed(session_context):
    cur.close()
    conn.close()

    try: 
        m.close()
    except: 
        pass

    try:
        map_pane._widget.close()
    except:
        pass


    try:
        for widget in pn.state.cache.values():
            try:
                widget.close()
            except: 
                pass
    except:
        pass


    if stream is not None:
        try:
            stream.stop()
            stream.close()
        except:
            pass

        stream = None

pn.state.on_session_destroyed(session_destroyed)

# ---------------- UI ----------------

left  = pn.Column("## Video Display",
                  video_pane,
                  "## Transcript Search",
                  pn.Row(Search, plot_button, clear_plot_button), 
                  transcript_table)



right = pn.Column("## Live GPS Map",
                  map_pane,
                  "## Add Commentary",
                  pn.Row(record_button, stop_button, save_recording),
                  recording_status,
                  playback,
                  pn.Row(audio_retrieval, audio_id_input),
                  "## Added Audio",
                  pn.Row(search_add_box, plot_added, clear_added),
                  new_transcript_df
                  )

pn.Column("# Newburgh Heights Dash GPS Sync",
          pn.Row(left, right, sizing_mode="stretch_width"),
          "## Semantic Search",
          pn.Row(query_og, export_scores),
          semantic_status,
          score_og_df).servable()



