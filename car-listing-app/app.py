import streamlit as st
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from dotenv import load_dotenv
import json, os
from llm_extract import extract_doc_from_text, merge_body_type
from emailer import send_car_payload
load_dotenv()

st.set_page_config(page_title="Text + Image Uploader", page_icon="🖼️", layout="wide")

st.title("Car Listing App")
st.caption("Compose your message, add ONE image with the ➕, then click **Send**.")

# --- Session state ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "sent_text" not in st.session_state:
    st.session_state.sent_text = None
if "sent_image" not in st.session_state:
    st.session_state.sent_image = None 
# Keep latest extraction + email status so it survives reruns
if "last_doc" not in st.session_state:
    st.session_state.last_doc = None
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "email_error" not in st.session_state:
    st.session_state.email_error = None

# --- Sidebar actions ---
with st.sidebar:
    st.header("Actions")
    if st.button("Clear uploaded image"):
        st.session_state.uploader_key += 1
        st.session_state.sent_image = None
        st.rerun()
    if st.button("Clear message"):
        st.session_state.sent_text = None
        st.session_state.sent_image = None
        st.session_state.last_doc = None
        st.session_state.email_sent = False
        st.session_state.email_error = None
        st.rerun()

# --- Compose form ---
with st.form("compose_form", clear_on_submit=False):
    left, right = st.columns([12, 1], vertical_alignment="center")
    with left:
        text = st.text_area("Your text", placeholder="Type something here…", height=150, key="main_text")

    uploaded_file = None
    with right:
        popover_fn = getattr(st, "popover", None)
        if popover_fn is not None:
            with popover_fn("➕", help="Attach a single image"):
                uploaded_file = st.file_uploader(
                    "Upload image (1 max)",
                    type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
                    accept_multiple_files=False,
                    key=f"uploader_{st.session_state.uploader_key}",
                )
        else:
            st.caption("Image")
            uploaded_file = st.file_uploader(
                "Upload image (1 max)",
                type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
                accept_multiple_files=False,
                key=f"uploader_{st.session_state.uploader_key}",
            )
    submitted = st.form_submit_button("Send", use_container_width=True)

# When Send is clicked, capture current inputs AND run extraction + email
if submitted:
    st.session_state.sent_text = text if text and text.strip() else None

    # read image file (optional)
    meta = None
    if uploaded_file is not None:
        try:
            content = uploaded_file.read()
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            meta = {
                "name": uploaded_file.name,
                "type": getattr(uploaded_file, "type", "unknown"),
                "size": getattr(uploaded_file, "size", 0),
                "data": content,
            }
        except Exception as e:
            st.toast(f"Couldn't read {getattr(uploaded_file, 'name', 'file')}: {e}", icon="⚠️")
    st.session_state.sent_image = meta

    # --- Run extraction + merge body_type + send email ---
    with st.spinner("Processing (extracting JSON and sending email)..."):
        try:
            # 1) Extract strictly from TEXT (schema-enforced)
            doc = extract_doc_from_text(st.session_state.sent_text or "")

            # 2) Merge body_type from IMAGE via dummy classifier (always 'sedan' for now if image present)
            img_bytes = st.session_state.sent_image["data"] if (st.session_state.sent_image and st.session_state.sent_image.get("data")) else None
            doc = merge_body_type(doc, img_bytes)

            # Store for display/download after rerun
            st.session_state.last_doc = doc

            # 3) Send email via Gmail API
            to_addr = os.getenv("GMAIL_TO")  # REQUIRED
            if not to_addr:
                st.session_state.email_sent = False
                st.session_state.email_error = "GMAIL_TO not set; skipping email send."
                st.warning(st.session_state.email_error)
            else:
                send_car_payload(
                    to_addr=to_addr,
                    subject_prefix=os.getenv("EMAIL_SUBJECT_PREFIX", "[CarApp]"),
                    doc=doc,
                    image_meta=st.session_state.sent_image,
                )
                st.session_state.email_sent = True
                st.session_state.email_error = None
                st.toast("Email sent via Gmail API.", icon="✅")

            st.success("Extraction complete.")

        except Exception as e:
            st.session_state.last_doc = None
            st.session_state.email_sent = False
            st.session_state.email_error = str(e)
            st.error(f"Processing failed: {e}")

GRID_COLS = 4
MAX_PREVIEW_HEIGHT = 600

# --- Output ---
if st.session_state.sent_text is None and st.session_state.sent_image is None and st.session_state.last_doc is None:
    st.info("Compose your message, attach a single image, and click **Send**.")
else:
    # Show the text the user sent
    if st.session_state.sent_text:
        st.subheader("Text")
        st.write(st.session_state.sent_text)

    # Show extracted JSON (if available)
    if st.session_state.last_doc is not None:
        st.subheader("Extracted JSON")
        st.code(json.dumps(st.session_state.last_doc, ensure_ascii=False, indent=2), language="json")
        st.download_button(
            "Download JSON",
            data=json.dumps(st.session_state.last_doc, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="car.json",
            mime="application/json",
        )
        # Email status
        if st.session_state.email_error:
            st.error(f"Email status: {st.session_state.email_error}")
        elif st.session_state.email_sent:
            st.success("Email sent ✔")

    # Show image preview (if any)
    if st.session_state.sent_image:
        st.subheader("Image (1)")
        cols = st.columns(GRID_COLS)
        with cols[0]:
            meta = st.session_state.sent_image
            try:
                img = Image.open(BytesIO(meta["data"]))
                if img.height > MAX_PREVIEW_HEIGHT:
                    ratio = MAX_PREVIEW_HEIGHT / float(img.height)
                    new_width = int(img.width * ratio)
                    img = img.resize((new_width, MAX_PREVIEW_HEIGHT))
                st.image(
                    img,
                    caption=f"{meta['name']} • {img.size[0]}×{img.size[1]}",
                    use_container_width=True
                )
                kb = (meta.get("size") or 0) / 1024
                st.caption(f"Size: {kb:.1f} KB • Type: {meta.get('type', 'unknown')}")
            except UnidentifiedImageError:
                st.error(f"'{meta['name']}' does not appear to be a supported image.")
            except Exception as e:
                st.error(f"Couldn't preview {meta['name']}: {e}")

st.divider()
