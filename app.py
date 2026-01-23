
import streamlit as st
import pandas as pd
import random
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "au_parliament_contacts.csv"

st.set_page_config(page_title="Email Draft Generator (AU MPs & Senators)", layout="wide")

# LOCKED: Six items (verbatim)
SIX_ITEMS = [
    "1. Protect the people of Iran by weakening the regime’s machinery of repression, especially by targeting the Islamic Revolutionary Guard Corps (IRGC), its commanders, its command structure, and its infrastructure.",
    "2. Maximum economic pressure by blocking the regime’s assets around the world and targeting its clandestine network of oil tankers, known as the “shadow fleet.”",
    "3. Provide internet for Iran through Starlink and other secure communications tools, and disable the regime’s ability to shut down the internet.",
    "4. Expel the regime’s diplomats and pursue legal action against perpetrators of crimes against humanity.",
    "5. The immediate and unconditional release of all political prisoners.",
    "6. Prepare for a democratic transition in Iran and recognize a legitimate transitional government, led by Reza Pahlavi, who has publicly committed to democratic principles and people trust to guide the country through a peaceful transition."
]

SUBJECT_OPTIONS = [
    "Urgent: Six actions Australia should support for Iran",
    "Request: Six concrete measures to protect the people of Iran",
    "Iran: Six urgent actions for human rights and democratic transition",
    "Support the people of Iran: Six urgent measures"
]

INTRO_BANK = {
    "Diplomatic": [
        "I am writing as a deeply concerned Iranian-Australian citizen regarding the ongoing crisis in Iran and the grave human rights violations being committed by the Islamic Republic against its own people.",
        "I am an Iranian-Australian citizen writing to respectfully request support for practical measures that align with Australia’s commitment to human rights and democratic values."
    ],
    "Firm": [
        "I am writing as an Iranian-Australian citizen with deep concern about the regime’s escalating violence and repression in Iran.",
        "I am contacting you to urge clear, concrete action in response to the Islamic Republic’s brutality against the Iranian people."
    ],
    "Personal": [
        "I am an Iranian-Australian citizen, and like many in our community, I am deeply distressed by what is happening to ordinary people in Iran.",
        "As an Iranian-Australian, I am reaching out because the situation in Iran is unbearable, and silence costs lives."
    ]
}

FRAMING_BANK = {
    "Diplomatic": [
        "Iranians inside the country, as well as the Iranian diaspora worldwide, are calling on democratic governments to take principled and concrete action.",
        "These measures focus on accountability, pressure on the regime’s capacity to repress, and support for the Iranian people’s basic freedoms."
    ],
    "Firm": [
        "Iranians in Iran and abroad are calling for action that is specific, enforceable, and focused on the regime’s repression and funding networks.",
        "These are concrete steps that can reduce harm, increase accountability, and help prevent further atrocities."
    ],
    "Personal": [
        "People are being harmed for demanding basic freedoms. Practical actions from democratic countries can make a real difference.",
        "The Iranian community is asking for targeted measures that protect people on the ground and keep pressure on those responsible."
    ]
}

CLOSING_BANK = {
    "Diplomatic": [
        "I would appreciate it if you could raise these points within Parliament and with relevant ministers, and support any parliamentary actions consistent with these measures.",
        "I would be grateful to know your position on these measures and whether you will advocate for them."
    ],
    "Firm": [
        "I ask you to raise these measures publicly and within Parliament, and to push for clear action rather than statements of concern.",
        "Please use your platform to press for decisive action that protects civilians and holds perpetrators accountable."
    ],
    "Personal": [
        "Thank you for taking this seriously. I hope you will stand with the people of Iran and help turn concern into action.",
        "Thank you for your attention. I hope you will help ensure Australia is on the right side of history."
    ]
}

SIGN_OFFS = ["Kind regards", "Sincerely", "Respectfully"]

def build_email(tone: str, sender_name: str, recipient_title: str, recipient_lastname: str, seed: int):
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

def mailto_link(to_email: str, subject: str, body: str):
    params = {"subject": subject, "body": body}
    return f"mailto:{to_email}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"

@st.cache_data
def load_contacts():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Could not find {CSV_PATH}. Run build_contacts.py first.")
    df = pd.read_csv(CSV_PATH)
    for c in ["party", "state", "email", "first_name", "last_name", "title", "chamber", "display"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("")
    if (df["display"] == "").any():
        df["display"] = (df["title"] + " " + df["first_name"] + " " + df["last_name"]).str.replace("  ", " ").str.strip()
    return df

st.title("Email Draft Generator (Australia MPs & Senators)")
st.caption("Enter your name once, pick recipient (filter by Party/State), draft auto-generated, tap Send.")

if "step" not in st.session_state:
    st.session_state.step = 1
if "sender_name" not in st.session_state:
    st.session_state.sender_name = ""
if "draft" not in st.session_state:
    st.session_state.draft = None

# Step 1: sender name
if st.session_state.step == 1:
    st.subheader("Step 1: Your name (signature)")
    sender = st.text_input("Sender name", value=st.session_state.sender_name, placeholder="Your name")
    if st.button("Continue"):
        if not sender.strip():
            st.error("Please enter your name.")
        else:
            st.session_state.sender_name = sender.strip()
            st.session_state.step = 2
            st.rerun()

# Step 2: choose recipient and generate draft
elif st.session_state.step == 2:
    st.subheader("Step 2: Choose recipient")

    df = load_contacts()

    col1, col2, col3 = st.columns(3)
    with col1:
        chamber = st.selectbox("Chamber", ["All", "House", "Senate"])
    with col2:
        states = ["All"] + sorted([s for s in df["state"].unique().tolist() if str(s).strip()])
        state = st.selectbox("State", states)
    with col3:
        parties = ["All"] + sorted([p for p in df["party"].unique().tolist() if str(p).strip()])
        party = st.selectbox("Party", parties)

    filtered = df.copy()
    if chamber != "All":
        filtered = filtered[filtered["chamber"] == chamber]
    if state != "All":
        filtered = filtered[filtered["state"] == state]
    if party != "All":
        filtered = filtered[filtered["party"] == party]

    search = st.text_input("Search by name", placeholder="Type surname or first name")
    if search.strip():
        s = search.strip().lower()
        filtered = filtered[filtered["display"].str.lower().str.contains(s, na=False)]

    st.dataframe(filtered[["display", "chamber", "state", "party", "email"]], hide_index=True, use_container_width=True)

    selected = st.selectbox("Select recipient", options=filtered["display"].tolist())
    tone = st.selectbox("Tone", ["Diplomatic", "Firm", "Personal"], index=0)

    if st.button("Create draft automatically"):
        row = filtered[filtered["display"] == selected].iloc[0].to_dict()

        # 10 variations -> pick 1 randomly
        base_seed = random.randint(1, 10_000_000)
        candidates = []
        for i in range(10):
            subject, body = build_email(
                tone=tone,
                sender_name=st.session_state.sender_name,
                recipient_title=row.get("title", "Dear"),
                recipient_lastname=row.get("last_name", ""),
                seed=base_seed + i
            )
            candidates.append((subject, body))

        subject, body = random.choice(candidates)

        st.session_state.draft = {
            "to": row.get("email", ""),
            "subject": subject,
            "body": body,
            "recipient": row.get("display", ""),
            "tone": tone,
            "row": row
        }
        st.session_state.step = 3
        st.rerun()

    if st.button("Back"):
        st.session_state.step = 1
        st.rerun()

# Step 3: show draft + send
elif st.session_state.step == 3:
    st.subheader("Step 3: Draft ready")

    d = st.session_state.draft
    st.write(f"**Recipient:** {d['recipient']}")
    st.write(f"**Tone:** {d['tone']}")
    st.write(f"**To:** {d['to']}")
    st.write(f"**Subject:** {d['subject']}")

    st.text_area("Email body", value=d["body"], height=380)

    if d["to"].strip():
        link = mailto_link(d["to"].strip(), d["subject"], d["body"])
        st.markdown(f"### ✅ [Send (opens your email app)]({link})")
    else:
        st.warning("No email found for this recipient. You can copy/paste the draft.")

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("Reroll (new variation, same recipient)"):
            row = d["row"]
            base_seed = random.randint(1, 10_000_000)
            candidates = []
            for i in range(10):
                subject, body = build_email(
                    tone=d["tone"],
                    sender_name=st.session_state.sender_name,
                    recipient_title=row.get("title", "Dear"),
                    recipient_lastname=row.get("last_name", ""),
                    seed=base_seed + i
                )
                candidates.append((subject, body))
            subject, body = random.choice(candidates)
            st.session_state.draft["subject"] = subject
            st.session_state.draft["body"] = body
            st.rerun()
    with colB:
        if st.button("Pick another recipient"):
            st.session_state.step = 2
            st.rerun()
    with colC:
        if st.button("Start over"):
            st.session_state.step = 1
            st.session_state.draft = None
            st.rerun()
