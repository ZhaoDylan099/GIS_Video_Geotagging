import panel as pn
import pandas as pd
import ipyleaflet as ipyl
import sounddevice as sd 
import sys
import numpy as np
import wavio as wv



VIDEO_URL = "http://localhost/newburgheights_dash_video.mp4"
CSV_FILE  = "newburgheights_dash_video_gps.csv"
NARRATIVE_FILE = "newburgheights_dash_video_narrative.csv"

TIME_COL = "media time"
LAT_COL  = "latitude"
LON_COL  = "longitude"
ZOOM_START = 15


audio_buffer = []
samplerate = 44100
channels = 1
dtype = np.float32

# May differ between devices
sd.default.device = (2, 3)




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
narrative["active"] = ""
    


# ---------------- MAP ----------------

def get_current_location(t=None):
    t = video_pane.time if t is None else t
    idx = (gps["time_seconds"] - t).abs().idxmin()
    row = gps.loc[idx]
    return float(row[LAT_COL]), float(row[LON_COL])

lat, lon = get_current_location()


m = ipyl.Map(center=(lat, lon), zoom=ZOOM_START, scroll_wheel_zoom=True)


marker = ipyl.CircleMarker(location=(lat, lon), radius=7, color="red", fill=True, fill_color="red", fill_opacity=0.7)
m.add_layer(marker)


legend = ipyl.LegendControl(
    {
        "GPS Synced Point": "red",
        "Search Results": "blue",
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
    narrative[["active","Media Time", "Transcript"]],
    height=300, width=700                
)


def update_transcript(event=None):
    t = float(video_pane.time)

    # Find first row where time falls inside window
    rows = narrative[narrative["st_time"] <= t]

    index = -1
    if rows.empty == False:

        index = rows.index[-1]
    df = narrative.copy()
    df["active"] = ""

    if index != -1:
        df.loc[index, "active"] = "▶ CURRENT"

    t_input = Search.value.strip().lower()

    if t_input:

        df = df[df["Transcript"].str.contains(t_input)]


    # Force UI update with a NEW object ref

    transcript_table.object = df[["active", "Media Time", "Transcript"]]

    

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
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker:
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

            m.add_layer(dot)

plot_button.on_click(plot_search)

clear_plot_button = pn.widgets.Button(name = "Clear Plot", button_type = "primary")

def clear_search(event):

    to_remove = []

    for layer in m.layers:
        # keep basemap + the marker we want to keep
        if isinstance(layer, ipyl.CircleMarker) and layer is not marker:
            to_remove.append(layer)
        
    for layer in to_remove:
        m.remove_layer(layer)

clear_plot_button.on_click(clear_search)

# ---------- Audio Recording ---------


recording_status = pn.pane.Markdown("🔴 **Not Recording**")
record_button = pn.widgets.Button(name= 'Record', button_type = "primary")
stop_button = pn.widgets.Button(name="Stop Recording", button_type="danger", disabled=True)
playback = pn.pane.Audio(None, name='Audio')


stream = None



def callback(indata, frames, time, status):
    
    if status:
        print(status, file=sys.stderr)

    audio_buffer.append(indata.copy())  # store incoming audio chunk


def record_audio(event):
    global stream, audio_buffer
    audio_buffer = []
    stream = sd.InputStream(samplerate=samplerate, channels=channels, dtype=dtype, callback=callback)

    stream.start()
    recording_status.object = "🟢 **Recording...**"
    record_button.disabled = True
    stop_button.disabled = False


def stop_recording(event):
    global stream, audio_buffer

    stream.stop()
    stream.close()

    audio = np.concatenate(audio_buffer, axis=0)
    recording_status.object = "🔴 **Stopped Recording**"

    stop_button.disabled = True
    record_button.disabled = False
    
    wv.write("recording.wav", audio, samplerate, sampwidth=2)
    playback.object = "recording.wav"

record_button.on_click(record_audio)
stop_button.on_click(stop_recording)


# ---------------- UI ----------------

left  = pn.Column("## Video Display",
                  video_pane,
                  "## Transcript Search",
                  pn.Row(Search, plot_button, clear_plot_button), 
                  transcript_table)




right = pn.Column("## Live GPS Map",
                  map_pane,
                  "## Add Commentary",
                  pn.Row(record_button, stop_button),
                  recording_status,
                  playback)

pn.Column("# Newburgh Heights Dash GPS Sync",
          pn.Row(left, right)).servable()

