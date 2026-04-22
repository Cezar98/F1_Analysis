import os

import fastf1
from matplotlib import pyplot as plt
import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from fastf1 import plotting
fastf1.Cache.enable_cache("cache")  # Enable caching to speed up data loading on subsequent runs
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme="fastf1")
 

class F1AnalysisRequest(BaseModel):
    season: str
    race: str
    session: str
    driver1: str
    driver2: str
    driver1_lap_summary: str
    driver2_lap_summary: str


@st.cache_data(show_spinner=False)
def get_schedule(season: int):
    return fastf1.get_event_schedule(season)


@st.cache_data(show_spinner=False)
def get_session_names(season: int, race_name: str,backend=None):
    event = fastf1.get_event(season, race_name,backend= backend)
    return [
        event[key]
        for key in event.index
        if key.startswith("Session")
        and not key.endswith("Date")
        and not key.endswith("DateUtc")
        and str(event[key]) != "nan"
    ]


@st.cache_resource
def get_openai_client():
    api_key = (
        st.secrets["OPENAI_API_KEY"]
        if "OPENAI_API_KEY" in st.secrets
        else os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def format_lap_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = seconds - minutes * 60
    return f"{minutes}:{remaining_seconds:06.3f}"


def build_lap_summary(laps) -> str:
    clean_laps = laps.dropna(subset=["LapTime"])
    if clean_laps.empty:
        return "No valid lap times were recorded for this driver in this session."

    lap_seconds = clean_laps["LapTime"].dt.total_seconds()
    
    best = lap_seconds.min()
    median = lap_seconds.median()
    std_dev = lap_seconds.std()
    lap_count = len(clean_laps)
    lap_seconds = lap_seconds.map(format_lap_time)

    std_dev_value = 0.0 if std_dev != std_dev else std_dev

    return (
        
        f"Valid laps: {lap_count}. "
        f"Lap stats: {laps[['LapNumber','LapTime','Compound', 'Position']].to_string(index=False)}. "
        f"Weather stats: {laps.get_weather_data().to_string(index=False)}. "
        f"Best lap: {format_lap_time(best)}. "
        f"Median lap: {format_lap_time(median)}. "
        f"Lap time standard deviation: {format_lap_time(std_dev_value)}."
        
    )

def analyze_performance(client: OpenAI, request: F1AnalysisRequest):
    prompt = (
        f"Analyze the performance of {request.driver1} in the "
        f"{request.session} session of the {request.race} ({request.season}).\n"
        f"Use only the data below:\n{request.driver1_lap_summary}\n"
        "Give 4-6 concise bullet points on pace, consistency, and notable patterns. "
        "If data is limited, say that explicitly."
    )
    #st.write(prompt)
    #st.warning("Do not forget to delete the writing of the prompt before going into production")
    response = client.responses.create(
        model="gpt-5-nano",
        instructions="You are an F1 analyst. Be clear, factual, and concise.",
        input=prompt,
    )
    return response.output_text


def compare_drivers(client: OpenAI, request: F1AnalysisRequest):
    prompt = (
        f"Compare   the performances of {request.driver1} and {request.driver2} in the "
        f"{request.session} session of the {request.race} ({request.season}).\n"
        f"Use only the data below (the first belongs to the first driver, the second belongs to the second driver):\n{request.driver1_lap_summary}\n"
        f"{request.driver2_lap_summary}\n"
        "Give 4-6 concise bullet points on pace, consistency, and notable patterns."
        "If data is limited, say that explicitly."
    )

    response = client.responses.create(
        model="gpt-5-nano",
        instructions="You are an F1 analyst. Be clear, factual, and concise.",
        input=prompt,
    )
    return response.output_text

analysis_result = None
backend = None
st.set_page_config(page_title="F1 Data Analysis", layout="wide")
st.title("F1 Data Analysis with FastF1 + OpenAI")
st.write("Pick a season, event, session, and service")



seasons = [2018 + x for x in range(8)]
selected_season = st.selectbox("Select Season", seasons, index=None)


if selected_season is None:
    st.warning("Please select a season to continue.")
    st.stop()
try:
    if selected_season < 2018:   
        st.warning("Data for seasons before 2018 may be incomplete or unavailable. Please select 2018 or later for the best experience.")
        backend = "ergast"
    with st.spinner("Loading event schedule..."):
        races = get_schedule(selected_season)
except Exception as exc:
    st.error(f"Could not load event schedule for {selected_season}: {exc}")
    st.stop()

selected_race = st.selectbox("Select Grand Prix", races["EventName"],index=None)
if selected_race is None:
    st.warning("Please select a Grand Prix to continue.")
    st.stop()

try:
    session_names = get_session_names(selected_season, selected_race,backend=backend)
except Exception as exc:
    st.error(f"Could not load sessions for {selected_race}: {exc}")
    st.stop()

selected_session = st.selectbox("Select Session", session_names,index=None)
if selected_session is None:
    st.warning("Please select a session to continue.")
    st.stop()

try:
    with st.spinner("Loading timing data..."):
        session = fastf1.get_session(selected_season, selected_race, selected_session,backend=backend)
        session.load()
except Exception as exc:
    st.error(f"Could not load selected session data: {exc}")
    st.stop()

service = st.radio("Select Service", ["Analyze driver performance", "Compare drivers"], index=None)
result_cols = [col for col in ["Abbreviation", "FullName"] if col in session.results.columns]
if service is None:
    st.warning("Please select a service to continue.")
    st.stop()
    
drivers_df = session.results[result_cols].dropna()
if drivers_df.empty:
        st.error("No driver results were found for this session.")
        st.stop()
driver_map = dict(zip(drivers_df["Abbreviation"], drivers_df["FullName"]))

openai_client = get_openai_client()
if openai_client is None:
        st.info(
            "AI analysis is disabled until you set `OPENAI_API_KEY` in Streamlit secrets "
            "or your environment."
        )

if service == "Analyze driver performance":
    

    
    selected_driver_abbr = st.selectbox("Select Driver",list(driver_map.keys()),index=None,
        format_func=lambda d: f"{d} - {driver_map.get(d, d)}",
    )

    if selected_driver_abbr != None:
        laps = session.laps.pick_drivers(selected_driver_abbr)
       
        
    else:
        st.warning("Please select a driver to continue.")
        st.stop()
    if laps.empty:
        st.warning("No laps found for the selected driver in this session.")
        st.stop()

    st.subheader(
        f"Lap Data: {driver_map.get(selected_driver_abbr, selected_driver_abbr)} "
        f"({selected_driver_abbr})"
    )
    display_cols = ["LapNumber", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]
    available_display_cols = [col for col in display_cols if col in laps.columns]
    #st.dataframe(laps[available_display_cols], width='stretch',hide_index=True)

    plot_laps = laps.dropna(subset=["LapTime"]).copy()
    if not plot_laps.empty:
    
        fig, ax = plt.subplots()
        style = plotting.get_driver_style(identifier=selected_driver_abbr,style=['color', 'linestyle'],session=session)
        ax.plot(plot_laps["LapNumber"], plot_laps["LapTime"], **style ,marker="o")
        ax.set_title(
            f"Lap Times for {selected_driver_abbr} | "
            f"{selected_session} - {selected_race} ({selected_season})"
        )
        ax.set_xlabel("Lap Number")
        ax.set_ylabel("Lap Time ")
        ax.grid(alpha=0.3)
        st.pyplot(fig, width='stretch')
    else:
        st.info("No valid timed laps are available to plot.")

    
    analyze_clicked = st.button(
        "Analyze Performance with AI",
        disabled=openai_client is None,
    )
    if analyze_clicked and openai_client is not None:
        analysis_request = F1AnalysisRequest(
            season=str(selected_season),
            race=str(selected_race),
            session=str(selected_session),
            driver1=f"{driver_map.get(selected_driver_abbr, selected_driver_abbr)} ({selected_driver_abbr})",
            driver2 = "",
            driver1_lap_summary=build_lap_summary(laps),
            driver2_lap_summary=""
        )

        try:
            with st.spinner("Generating analysis..."):
                analysis_result = analyze_performance(openai_client, analysis_request)
            st.subheader("AI Performance Analysis")
            st.write(analysis_result)
        except Exception as exc:
            st.error(f"Analysis request failed: {exc}")
    
else:
    selected_driver1_abbr = st.selectbox("Select Driver 1",list(driver_map.keys()),index=None,
        format_func=lambda d: f"{d} - {driver_map.get(d, d)}",
    )
    if selected_driver1_abbr is None:
        st.warning("Please select Driver 1 to continue.")
        st.stop()
    laps1 = session.laps.pick_drivers(selected_driver1_abbr)
    if laps1.empty:
        st.warning("No laps found for the selected driver in this session.")
        st.stop()

    
    selected_driver2_abbr = st.selectbox("Select Driver 2",list(driver_map.keys()),index=None,
        format_func=lambda d: f"{d} - {driver_map.get(d, d)}",
    )
    if selected_driver2_abbr is None:
        st.warning("Please select Driver 1 to continue.")
        st.stop()
    if selected_driver1_abbr == selected_driver2_abbr:
        st.warning("Please select two different drivers for comparison.")
        st.stop()

    laps2 = session.laps.pick_drivers(selected_driver2_abbr)
    if laps2.empty:
        st.warning("No laps found for the selected driver in this session.")
        st.stop()

    fig, ax = plt.subplots(figsize=(8, 5))

    for driver in (selected_driver1_abbr, selected_driver2_abbr):
        laps = session.laps.pick_drivers(driver).pick_quicklaps().reset_index()
        style = plotting.get_driver_style(identifier=driver,
                                          style=['color', 'linestyle'],
                                          session=session)
        ax.plot(laps['LapTime'], **style, label=driver)

    # add axis labels and a legend
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time")
    ax.legend()
    st.pyplot(fig, width='stretch')


    analyze_clicked = st.button(
        "Compare drivers with AI",
        disabled=openai_client is None,
    )
    
    
    
    if analyze_clicked and openai_client is not None:
        try:
            analysis_request = F1AnalysisRequest(
            season=str(selected_season),
            race=str(selected_race),
            session=str(selected_session),
            driver1=f"{driver_map.get(selected_driver1_abbr, selected_driver1_abbr)} ({selected_driver1_abbr})",
            driver2=f"{driver_map.get(selected_driver2_abbr, selected_driver2_abbr)} ({selected_driver2_abbr})",
            driver1_lap_summary=build_lap_summary(laps1),
            driver2_lap_summary=build_lap_summary(laps2),
            )
            with st.spinner("Generating analysis..."):
                    analysis_result = compare_drivers(openai_client, analysis_request)
            st.subheader("AI Driver Comparison")
            st.write(analysis_result)
        except Exception as exc:
                st.error(f"Analysis request failed: {exc}")
    

    st.download_button(
        label="Download Analysis as Text File",
        data=analysis_result,
        file_name=f"{selected_season}_{selected_race}_{selected_session}_analysis.txt",
        mime="text/plain",
    )




   