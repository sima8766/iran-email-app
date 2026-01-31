# app_V4Draft3.py
# Bulk Email Draft Generator (AU MPs & Senators)
# User enters name, then clicks one button to open a prefilled email
# All recipients are in BCC, no recipient selection, no email preview
# Each click generates a new random draft, different from the previous one

import random
import urllib.parse
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ---------------------------
# Paths
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "au_parliament_contacts.csv"

st.set_page_config(
    page_title="Email Draft Generator",
    layout="centered",
)

st.title("Email Draft Generator")
st.caption("Enter your name, then open a prefilled email with all recipients included in BCC.")

# Blue line message as requested
st.info("This tool can be used by anyone, anywhere in the world, no matter where you live.")


# ---------------------------
# Locked: Six items
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
    "Request: Six concrete measures to support the people of Iran",
    "Iran: Request for practical human rights and democratic measures",
    "Support the people of Iran: Six urgent actions",
    "Six priority actions Australia should support for Iran",
]

INTRO_BANK = [
    "I am writing as an Iranian citizen regarding the ongoing crisis in Iran and the grave human rights violations being committed against civilians.",
    "I am writing to respectfully request support for practical measures that align with democratic values, the rule of law, and basic human rights.",
    "I am reaching out with deep concern about escalating repression in Iran and the urgent need for concrete international action.",
    "I am writing to ask for your support for clear, actionable steps that help protect Iranian civilians and advance a peaceful democratic transition.",
]

CLOSING_BANK = [
    "Thank you for your time and for any action you can take to support the Iranian people’s basic freedoms and safety.",
    "I appreciate your consideration and your continued commitment to human rights and democratic principles.",
    "Thank you for your attention to this urgent matter and for standing for human dignity and justice.",
    "I would be grateful for your support and for any public stance you can take in line with these measures.",
]


def find_email_column(df: pd.DataFrame) -> str | None:
    candidates = ["email", "Email", "EMAIL", "e-mail", "E-mail", "mail", "Mail"]
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    for c in df.columns:
        if "email" in str(c).lower():
            return c
    return None


def load_recipients(csv_path: Path) -> list[str]:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing required file: {csv_path.name}. Place it in the same folder as this app."
        )

    df = pd.read_csv(csv_path)
    email_col = find_email_column(df)
    if not email_col:
        raise ValueError("Could not find an email column in the CSV. Please ensure it has a column named 'email'.")

    emails = (
        df[email_col]
        .astype(str)
        .str.strip()
        .replace({"nan": "", "None": ""})
        .tolist()
    )

    seen = set()
    cleaned = []
    for e in emails:
        if not e:
            continue
        if "@" not in e:
            continue
        if e not in seen:
            cleaned.append(e)
            seen.add(e)

    if not cleaned:
        raise ValueError("No valid email addresses were found in the CSV.")
    return cleaned


def build_email(sender_name: str, choice_index: int) -> tuple[str, str]:
    greeting = "Dear Member of Parliament,"
    intro = INTRO_BANK[choice_index % len(INTRO_BANK)]
    closing = CLOSING_BANK[choice_index % len(CLOSING_BANK)]
    subject = SUBJECT_OPTIONS[choice_index % len(SUBJECT_OPTIONS)]

    items_block = "\n".join(SIX_ITEMS)

    body = (
        f"{greeting}\n\n"
        f"{intro}\n\n"
        f"I respectfully ask you to support the following six measures:\n\n"
        f"{items_block}\n\n"
        f"{closing}\n\n"
        f"Sincerely,\n"
        f"{sender_name}"
    )

    return subject, body


def build_mailto_bcc_link(bcc_emails: list[str], subject: str, body: str) -> str:
    bcc_value = ",".join(bcc_emails)
    params = {"bcc": bcc_value, "subject": subject, "body": body}

    query = "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in params.items())
    return f"mailto:?{query}"


def pick_new_index(exclude_index: int | None, n: int) -> int:
    if n <= 1:
        return 0
    choices = list(range(n))
    if exclude_index is not None and exclude_index in choices:
        choices.remove(exclude_index)
    return random.choice(choices)


# ---------------------------
# Load recipients
# ---------------------------
try:
    recipients = load_recipients(CSV_PATH)
except Exception as e:
    st.error(str(e))
    st.stop()

# Keep state of last pick so next click is different
if "last_pick" not in st.session_state:
    st.session_state.last_pick = None

name = st.text_input("Your name (English)", placeholder="Sam Niknejad")


# ---------------------------
# Single action button: generates a new draft and opens mail app
# ---------------------------
if st.button("Open email in your email app", use_container_width=True):
    if not name.strip():
        st.warning("Please enter your name first.")
    else:
        pool_size = max(len(INTRO_BANK), len(CLOSING_BANK), len(SUBJECT_OPTIONS))
        new_pick = pick_new_index(st.session_state.last_pick, pool_size)
        st.session_state.last_pick = new_pick

        subject, body = build_email(name.strip(), new_pick)
        mailto_url = build_mailto_bcc_link(recipients, subject, body)

        # Open the user's default mail client immediately after click
        components.html(
            f"""
            <script>
              window.location.href = "{mailto_url}";
            </script>
            """,
            height=0,
        )
