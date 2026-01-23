# app.py
# Email Draft Generator (Australia MPs & Senators)
# - Step 1: Ask sender name once
# - Step 2: Filter MPs/Senators + pick ONE recipient via checkbox table (no dropdown)
# - Step 3: Auto-generate 10 variations, randomly pick 1, show draft + "Send" mailto link
# - Reroll: generates a new random pick (still 1 of 10) for the SAME recipient & tone
#
# Files required in the SAME folder as this app.py:
#   - au_parliament_contacts.csv
#   - requirements.txt (streamlit, pandas)
#
# Run locally:
#   streamlit run app.py

import random
import urllib.parse
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------
# Paths (works locally + Streamlit Cloud)
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "au_parliament_contacts.csv"

st.set_page_config(
    page_title="Email Draft Generator (AU MPs & Senators)",
    layout="wide",
)

# ---------------------------
# LOCKED: Six items (verbatim)
# ---------------------------
SIX_ITEMS = [
    "1. Protect the people of Iran by weakening the regime’s machinery of repression, especially by targeting the Islamic Revolutionary Guard Corps (IRGC), its commanders, its command structure, and its infrastructure.",
    "2. Maximum economic pressure by blocking the regime’s assets around the world and targeting its clandestine network of oil tankers, known as the “shadow fleet.”",
    "3. Provide internet for Iran through Starlink and other secure communications tools, and disable the regime’s ability to shut down the internet.",
    "4. Expel the regime’s diplomats and pursue legal action against perpetrators of crimes against humanity.",
    "5. The immediate and unconditional release of all political prisoners.",
    "6. Prepare for a democratic transition in Iran and recognize a legitimate transitional government, led by Reza Pahlavi, who has publicly committed to democratic principles and people trust to guide the country through a peaceful transition.",
]

SUBJECT_OPTIONS = [
    "Urgent: Six actions Australia should support for Iran",
    "Request: Six concrete measures to protect the people of Iran",
    "Iran: Six urgent actions for human rights and democratic transition",
    "Support the people of Iran: Six urgent measures",
]

INTRO_BANK = {
    "Diplomatic": [
        "I am writing as a deeply concerned Iranian-Australian citizen regarding the ongoing crisis in Iran and the grave human rights violations being committed by the Islamic Republic against its own people.",
        "I am an Iranian-Australian citizen writing to respectfully request support for practical measures that align with Australia’s commitment to human rights and democratic values.",
        "I am writing as an Iranian-Australian citizen to urge practical steps that support the Iranian people’s basic freedoms and Australia’s human rights commitments.",
        "I am reaching out as an Iranian-Australian citizen with deep concern about the escalating repression in Iran and the urgent need for concrete international action.",
    ],
    "Firm": [
        "I am writing as an Iranian-Australian citizen with deep concern about the regime’s escalating violence and repression in Iran.",
        "I am contacting you to urge clear, concrete action in response to the Islamic Republic’s brutality against the Iranian people.",
        "I am writing to urge decisive action in response to the regime’s ongoing repression and the widening humanitarian and human rights crisis in Iran.",
        "I am reaching out to ask for specific and enforceable measures, not statements of concern, in response to the regime’s brutality in Iran.",
    ],
    "Personal": [
        "I am an Iranian-Australian citizen, and like many in our community, I am deeply distressed by what is happening to ordinary people in Iran.",
        "As an Iranian-Australian, I am reaching out because the situation in Iran is unbearable, and silence costs lives.",
        "Like many Iranian-Australians, I am living with daily fear for family, friends, and innocent people in Iran who are targeted for demanding basic rights.",
        "I am writing with a heavy heart as an Iranian-Australian citizen, asking you to help turn compassion into practical action for people in Iran.",
    ],
}

FRAMING_BANK = {
    "Diplomatic": [
        "Iranians inside the country, as well as the Iranian diaspora worldwide, are calling on democratic governments to take principled and concrete action.",
        "These measures focus on accountability, pressure on the regime’s capacity to repress, and support for the Iranian people’s basic freedoms.",
        "This request is grounded in human rights, international law, and the need to reduce the regime’s capacity for repression and transnational intimidation.",
        "Targeted measures that restrict the regime’s coercive apparatus and illicit revenue streams can materially reduce harm to civilians.",
    ],
    "Firm": [
        "Iranians in Iran and abroad are calling for action that is specific, enforceable, and focused on the regime’s repression and funding networks.",
        "These are concrete steps that can reduce harm, increase accountability, and help prevent further atrocities.",
        "The regime’s repression is sustained by command structures, revenue channels, and diplomatic cover; addressing these levers is essential.",
        "Action should focus on weakening the machinery of repression and constraining the financial and logistical networks that sustain it.",
    ],
    "Personal": [
        "People are being harmed for demanding basic freedoms. Practical actions from democratic countries can make a real difference.",
        "The Iranian community is asking for targeted measures that protect people on the ground and keep pressure on those responsible.",
        "When the internet is cut and voices are silenced, the world’s response matters even more. Concrete steps can save lives.",
        "I hope Australia will stand clearly with the people, not the oppressors, by backing practical measures that reduce harm and support freedom.",
    ],
}

CLOSING_BANK = {
    "Diplomatic": [
        "I would appreciate it if you could raise these points within Parliament and with relevant ministers, and support any parliamentary actions consistent with these measures.",
        "I would be grateful to know your position on these measures and whether you will advocate for them.",
        "If possible, I respectfully ask that you support and encourage cross-party action aligned with these measures, including public statements and parliamentary engagement.",
        "I would appreciate your support in amplifying these six measures through parliamentary channels and relevant committees or ministerial briefings.",
    ],
    "Firm": [
        "I ask you to raise these measures publicly and within Parliament, and to push for clear action rather than statements of concern.",
        "Please use your platform to press for decisive action that protects civilians and holds perpetrators accountable.",
        "I urge you to advocate for these six measures and to press for tangible outcomes, including sanctions, investigations, and action against the regime’s networks.",
        "Please support urgent action focused on constraining the regime’s coercive and financial machinery and defending the Iranian people’s right to freedom.",
    ],
    "Personal": [
        "Thank you for taking this seriously. I hope you will stand with the people of Iran and help turn concern into action.",
        "Thank you for your attention. I hope you will help ensure Australia is on the right side of history.",
        "Thank you for listening. I hope you will stand with the Iranian people by supporting these practical steps and encouraging others to do the same.",
        "Thank you for your time and consideration. Your support can help protect lives and support a peaceful path to freedom.",
    ],
}

SIGN_OFFS = ["Kind regards", "Sincerely", "Respectfully"]


# ---------------------------
# Helpers
# ---------------------------
def mailto_link(to_email: str, subject: str, body: str) -> str:
    params = {"subject": subject, "body": body}
    return f"mailto:{to_email}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


def normalise_contacts(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure required columns exist
    required = ["chamber", "title", "first_name", "last_name", "state", "party", "email", "display"]
    for c in required:
        if c not in df.columns:
            df[c] = ""

    # Fill NaNs + strip
    for c in required:
        df[c] = df[c].fillna("").astype(str).str.strip()

    # If display missing, build it
    if (df["display"] == "").any():
        df["display"] = (
            (df["title"] + " " + df["first_name"] + " " + df["last_name"])
            .str.replace("  ", " ")
            .str.strip()
        )

    return df


@st.cache_data
def load_contacts() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CSV_PATH}. Make sure 'au_parliament_contacts.csv' is in the same folder as app.py."
        )
    df = pd.read_csv(CSV_PATH)
    return normalise_contacts(df)


def infer_recipient_title(row: dict) -> str:
    """
    Use title from CSV if present; otherwise infer by chamber (robust).
    """
    title = str(row.get("title", "")).strip()
    if title:
        low = title.lower()
        if "senator" in low:
            return "Senator"
        if low in ["mr", "ms", "mrs", "dr"]:
            return title
        return title

    chamber = str(row.get("chamber", "")).strip().lower()
    if "senate" in chamber:
        return "Senator"
    if "house" in chamber:
        return "Mr/Ms"

    return ""


def get_last_name(row: dict) -> str:
    """
    Prefer last_name; fall back to last token in display.
    """
    last_name = str(row.get("last_name", "")).strip()
    if last_name:
        return last_name

    display = str(row.get("display", "")).strip()
    if display:
        parts = display.split()
        if parts:
            return parts[-1]

    return ""


def build_email(
    tone: str,
    sender_name: str,
    recipient_title: str,
    recipient_lastname: str,
    seed: int,
) -> tuple[str, str]:
    rnd = random.Random(seed)

    subject = rnd.choice(SUBJECT_OPTIONS)
    greeting = f"Dear {recipient_title} {recipient_lastname},".replace("  ", " ").strip()

    intro = rnd.choice(INTRO_BANK[tone])
    framing = rnd.choice(FRAMING_BANK[tone])
    closing = rnd.choice(CLOSING_BANK[tone])
    signoff = rnd.choice(SIGN_OFFS)

    items_block = "\n".join(SIX_ITEMS)

    body = (
        f"{greeting}\n\n"
        f"{intro}\n\n"
        f"{framing}\n\n"
        f"In this context, I respectfully urge you to support and advocate for the following six measures:\n\n"
        f"{items_block}\n\n"
        f"{closing}\n\n"
        f"{signoff},\n"
        f"{sender_name}\n"
    )
    return subject, body


def generate_one_of_ten(tone: str, sender_name: str, row: dict) -> tuple[str, str]:
    """
    Generate 10 variations (same 6 items), then randomly pick one.
    """
    base_seed = random.randint(1, 10_000_000)
    candidates = []
    for i in range(10):
        subject, body = build_email(
            tone=tone,
            sender_name=sender_name,
            recipient_title=infer_recipient_title(row),
            recipient_lastname=get_last_name(row),
            seed=base_seed + i,
        )
        candidates.append((subject, body))
    return random.choice(candidates)


# ---------------------------
# UI
# ---------------------------
st.title("Email Draft Generator (Australia MPs & Senators)")
st.caption("Enter your name once, pick a recipient (filter by Party/State), draft auto-generated, tap Send.")

if "step" not in st.session_state:
    st.session_state.step = 1

if "sender_name" not in st.session_state:
    st.session_state.sender_name = ""

if "draft" not in st.session_state:
    st.session_state.draft = None


# ---------------------------
# Step 1: sender name
# ---------------------------
if st.session_state.step == 1:
    st.subheader("Step 1: Your name (signature)")
    sender = st.text_input("Sender name", value=st.session_state.sender_name, placeholder="Your name")

    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("Continue"):
            if not sender.strip():
                st.error("Please enter your name.")
            else:
                st.session_state.sender_name = sender.strip()
                st.session_state.step = 2
                st.rerun()


# ---------------------------
# Step 2: filter + pick recipient from table (NO dropdown)
# ---------------------------
elif st.session_state.step == 2:
    st.subheader("Step 2: Choose recipient")

    df = load_contacts()

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        chamber = st.selectbox("Chamber", ["All", "House", "Senate"], index=0)
    with c2:
        states = ["All"] + sorted([s for s in df["state"].unique().tolist() if str(s).strip()])
        state = st.selectbox("State", states, index=0)
    with c3:
        parties = ["All"] + sorted([p for p in df["party"].unique().tolist() if str(p).strip()])
        party = st.selectbox("Party", parties, index=0)

    filtered = df.copy()

    if chamber != "All":
        filtered = filtered[filtered["chamber"].str.lower() == chamber.lower()]
    if state != "All":
        filtered = filtered[filtered["state"] == state]
    if party != "All":
        filtered = filtered[filtered["party"] == party]

    search = st.text_input("Search by name", placeholder="Type surname or first name")
    if search.strip():
        s = search.strip().lower()
        filtered = filtered[filtered["display"].str.lower().str.contains(s, na=False)]

    # Make selectable table
    filtered = filtered.copy().reset_index(drop=True)
    if "Select" not in filtered.columns:
        filtered.insert(0, "Select", False)
    else:
        filtered["Select"] = filtered["Select"].astype(bool)

    st.write("Tick exactly **ONE** recipient in the table:")
    edited = st.data_editor(
        filtered[["Select", "display", "chamber", "state", "party", "email"]],
        hide_index=True,
        use_container_width=True,
        disabled=["display", "chamber", "state", "party", "email"],
        key="recipient_editor",
    )

    # Controls
    colA, colB, colC = st.columns([1.2, 1.8, 5])
    with colA:
        if st.button("Clear selection"):
            st.session_state.pop("recipient_editor", None)
            st.rerun()

    with colB:
        tone = st.selectbox("Tone", ["Diplomatic", "Firm", "Personal"], index=0)

    selected_rows = edited[edited["Select"] == True]

    colX, colY = st.columns([1.6, 5])
    with colX:
        if st.button("Create draft automatically"):
            if len(selected_rows) != 1:
                st.error("Please tick exactly ONE recipient in the table.")
            else:
                selected = selected_rows.iloc[0]
                sel_email = str(selected.get("email", "")).strip()
                sel_display = str(selected.get("display", "")).strip()

                # Look up FULL row from filtered dataframe (contains title/first/last)
                if sel_email:
                    match = filtered[filtered["email"].astype(str).str.strip() == sel_email]
                else:
                    match = filtered[filtered["display"].astype(str).str.strip() == sel_display]

                if match.empty:
                    st.error("Could not find full recipient record. Please try again.")
                    st.stop()

                row_full = match.iloc[0].to_dict()

                subject, body = generate_one_of_ten(
                    tone=tone,
                    sender_name=st.session_state.sender_name,
                    row=row_full,
                )

                st.session_state.draft = {
                    "to": str(row_full.get("email", "")).strip(),
                    "subject": subject,
                    "body": body,
                    "recipient": str(row_full.get("display", "")).strip(),
                    "tone": tone,
                    "row": row_full,  # keep for reroll
                }
                st.session_state.step = 3
                st.rerun()

    with colY:
        if st.button("Back"):
            st.session_state.step = 1
            st.rerun()


# ---------------------------
# Step 3: draft + send
# ---------------------------
elif st.session_state.step == 3:
    st.subheader("Step 3: Draft ready")

    d = st.session_state.draft
    if not d:
        st.warning("No draft found. Please go back and create a draft.")
    else:
        st.write(f"**Recipient:** {d['recipient']}")
        st.write(f"**Tone:** {d['tone']}")
        st.write(f"**To:** {d['to'] if d['to'] else '(no email found)'}")
        st.write(f"**Subject:** {d['subject']}")

        st.text_area("Email body", value=d["body"], height=380)

        if d["to"]:
            link = mailto_link(d["to"], d["subject"], d["body"])
            st.markdown(f"### ✅ [Send (opens your email app)]({link})")
        else:
            st.warning("No email address is available for this recipient. You can copy/paste the draft manually.")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reroll (new variation, same recipient)"):
                row = d["row"]
                subject, body = generate_one_of_ten(
                    tone=d["tone"],
                    sender_name=st.session_state.sender_name,
                    row=row,
                )
                st.session_state.draft["subject"] = subject
                st.session_state.draft["body"] = body
                st.rerun()

        with c2:
            if st.button("Pick another recipient"):
                st.session_state.step = 2
                st.rerun()

        with c3:
            if st.button("Start over"):
                st.session_state.step = 1
                st.session_state.draft = None
                st.session_state.pop("recipient_editor", None)
                st.rerun()
