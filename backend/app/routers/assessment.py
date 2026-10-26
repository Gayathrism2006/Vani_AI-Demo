import uuid
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.database import get_db
from app.services.question_service import question_service
from app.services.voice_service import voice_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.verification_service import verification_service
from app.config import (
    SUPPORTED_PROGRAMMING_LANGUAGES,
    SUPPORTED_ASSESSMENT_LANGUAGES,
    RECORDINGS_DIR
)

logger = logging.getLogger("assessment_router")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api/assessment", tags=["assessment"])

class StartAssessmentRequest(BaseModel):
    user_id: Optional[int] = 1
    user_email: Optional[str] = "candidate@vani.ai"
    programming_language: str
    assessment_language: str

async def _initialize_assessment_session(
    user_id: int,
    user_email: str,
    programming_language: str,
    assessment_language: str,
    terms_audio_bytes: Optional[bytes] = None,
    terms_transcript: Optional[str] = None
) -> dict:
    # Validation
    if not programming_language:
        raise HTTPException(status_code=400, detail="Programming language must be selected.")
    if not assessment_language:
        raise HTTPException(status_code=400, detail="Assessment language must be selected.")
        
    if programming_language not in SUPPORTED_PROGRAMMING_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported programming language. Supported: {', '.join(SUPPORTED_PROGRAMMING_LANGUAGES)}"
        )
    if assessment_language not in SUPPORTED_ASSESSMENT_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported assessment language. Supported: {', '.join(SUPPORTED_ASSESSMENT_LANGUAGES)}"
        )

    assessment_id = str(uuid.uuid4())
    logger.info(f"Starting assessment {assessment_id} for {programming_language} in {assessment_language}")

    # Register baseline voice from Terms & Conditions audio if supplied
    baseline_filename = ""
    baseline_audio_url = ""
    if terms_audio_bytes and len(terms_audio_bytes) > 500:
        base_res = verification_service.register_baseline_voice(
            assessment_id=assessment_id,
            audio_bytes=terms_audio_bytes
        )
        baseline_filename = base_res.get("baseline_audio_filename", "")
        baseline_audio_url = base_res.get("baseline_audio_url", "")
        logger.info(f"Terms & Conditions voice registered: {baseline_filename}")

    # Generate 5 scenario questions
    questions = await question_service.generate_questions(
        programming_language=programming_language,
        assessment_language=assessment_language
    )
    
    # Initialize empty answers dictionary for all 5 questions
    answers = {
        str(i): {
            "question_id": i,
            "recorded": False,
            "transcript": "",
            "audio_filename": "",
            "audio_url": "",
            "isolation_message": "",
            "recorded_at": None,
            "voice_matched": True,
            "voice_similarity_score": 100.0,
            "voice_match_status": "pending",
            "voice_match_message": "Awaiting answer recording"
        }
        for i in range(1, 6)
    }

    # Pre-generate Question 1 audio in cloned voice
    try:
        q1_text = questions[0]["question"]
        q1_audio = await voice_service.generate_speech(
            text=q1_text,
            language=assessment_language,
            assessment_id=assessment_id,
            question_index=1
        )
        questions[0]["audio_url"] = f"/api/audio/cached/{q1_audio['filename']}"
        questions[0]["is_cloned"] = q1_audio.get("is_cloned", False)
        questions[0]["tts_provider"] = q1_audio.get("tts_provider", "Unknown")
    except Exception as e:
        logger.error(f"Failed to pre-generate Q1 audio: {e}")
        questions[0]["audio_url"] = ""

    # Start asynchronous background pre-generation for Questions 2, 3, 4, 5
    import asyncio
    async def pre_cache_remaining():
        for q_idx in range(2, 6):
            try:
                q_text = questions[q_idx - 1]["question"]
                logger.info(f"Background pre-generating cloned audio for Q{q_idx}...")
                q_res = await voice_service.generate_speech(
                    text=q_text,
                    language=assessment_language,
                    assessment_id=assessment_id,
                    question_index=q_idx
                )
                logger.info(f"Background pre-generated audio for Q{q_idx} successfully: {q_res['filename']}")
                
                # Persist updated audio_url into DB
                try:
                    c = get_db()
                    cur = c.cursor()
                    cur.execute("SELECT questions_json FROM assessments WHERE id = ?", (assessment_id,))
                    row_db = cur.fetchone()
                    if row_db:
                        db_q = json.loads(row_db["questions_json"])
                        db_q[q_idx - 1]["audio_url"] = f"/api/audio/cached/{q_res['filename']}"
                        db_q[q_idx - 1]["is_cloned"] = q_res.get("is_cloned", False)
                        db_q[q_idx - 1]["tts_provider"] = q_res.get("tts_provider", "Unknown")
                        cur.execute("UPDATE assessments SET questions_json = ? WHERE id = ?", (json.dumps(db_q), assessment_id))
                        c.commit()
                    c.close()
                except Exception as db_err:
                    logger.warning(f"Failed to update DB for pre-cached Q{q_idx}: {db_err}")
            except Exception as ex:
                logger.warning(f"Background audio generation failed for Q{q_idx}: {ex}")

    asyncio.create_task(pre_cache_remaining())

    # Save to database
    now = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO assessments (
            id, user_id, user_email, programming_language, assessment_language,
            questions_json, answers_json, status, created_at,
            baseline_audio_filename, baseline_transcript
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        assessment_id,
        user_id,
        user_email,
        programming_language,
        assessment_language,
        json.dumps(questions),
        json.dumps(answers),
        "in_progress",
        now,
        baseline_filename,
        terms_transcript or ""
    ))
    conn.commit()
    conn.close()

    return {
        "id": assessment_id,
        "assessment_id": assessment_id,
        "programming_language": programming_language,
        "assessment_language": assessment_language,
        "questions": questions,
        "status": "in_progress",
        "baseline_registered": bool(baseline_filename),
        "baseline_audio_url": baseline_audio_url
    }

@router.post("/start")
async def start_assessment(req: StartAssessmentRequest):
    return await _initialize_assessment_session(
        user_id=req.user_id or 1,
        user_email=req.user_email or "candidate@vani.ai",
        programming_language=req.programming_language,
        assessment_language=req.assessment_language
    )

@router.post("/start-with-terms")
async def start_with_terms(
    user_id: int = Form(1),
    user_email: str = Form("candidate@vani.ai"),
    programming_language: str = Form(...),
    assessment_language: str = Form(...),
    terms_audio: Optional[UploadFile] = File(None),
    terms_transcript: Optional[str] = Form(None)
):
    terms_bytes = await terms_audio.read() if terms_audio else None
    return await _initialize_assessment_session(
        user_id=user_id,
        user_email=user_email,
        programming_language=programming_language,
        assessment_language=assessment_language,
        terms_audio_bytes=terms_bytes,
        terms_transcript=terms_transcript
    )

@router.get("/{assessment_id}")
def get_assessment(assessment_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    row_keys = row.keys()
    baseline_fn = row["baseline_audio_filename"] if "baseline_audio_filename" in row_keys else None
    baseline_tr = row["baseline_transcript"] if "baseline_transcript" in row_keys else ""

    return {
        "id": row["id"],
        "user_email": row["user_email"],
        "programming_language": row["programming_language"],
        "assessment_language": row["assessment_language"],
        "questions": json.loads(row["questions_json"]),
        "answers": json.loads(row["answers_json"]),
        "status": row["status"],
        "baseline_audio_filename": baseline_fn,
        "baseline_audio_url": f"/api/audio/recording/{baseline_fn}" if baseline_fn else None,
        "baseline_transcript": baseline_tr,
        "created_at": row["created_at"],
        "submitted_at": row["submitted_at"]
    }

@router.get("/{assessment_id}/question/{question_idx}/audio")
async def get_question_audio(assessment_id: str, question_idx: int):
    """
    Returns cloned voice audio for the specific question.
    Generates and caches audio if not yet created.
    """
    if question_idx < 1 or question_idx > 5:
        raise HTTPException(status_code=400, detail="Invalid question index (1-5).")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    questions = json.loads(row["questions_json"])
    question = questions[question_idx - 1]
    
    # Generate speech with OpenVoice cloned reference voice
    audio_meta = await voice_service.generate_speech(
        text=question["question"],
        language=row["assessment_language"],
        assessment_id=assessment_id,
        question_index=question_idx
    )

    audio_url = f"/api/audio/cached/{audio_meta['filename']}"
    
    # Persist audio_url to SQLite so subsequent fetches are instant
    try:
        conn = get_db()
        cursor = conn.cursor()
        questions[question_idx - 1]["audio_url"] = audio_url
        questions[question_idx - 1]["is_cloned"] = audio_meta.get("is_cloned", False)
        questions[question_idx - 1]["tts_provider"] = audio_meta.get("tts_provider", "Unknown")
        cursor.execute("UPDATE assessments SET questions_json = ? WHERE id = ?", (json.dumps(questions), assessment_id))
        conn.commit()
        conn.close()
    except Exception as db_e:
        logger.warning(f"Could not update questions_json for Q{question_idx}: {db_e}")

    return {
        "question_idx": question_idx,
        "audio_url": audio_url,
        "filename": audio_meta["filename"],
        "is_cloned": audio_meta.get("is_cloned", False),
        "tts_provider": audio_meta.get("tts_provider", "Unknown"),
        "cached": audio_meta.get("cached", False)
    }

@router.post("/{assessment_id}/question/{question_idx}/answer")
async def record_answer(
    assessment_id: str,
    question_idx: int,
    audio: UploadFile = File(...),
    live_transcript: Optional[str] = Form(None)
):
    """
    Processes candidate answer:
    1. Browser records candidate voice.
    2. ElevenLabs Audio Isolation cleans the audio (removing noise).
    3. ElevenLabs Speech-to-Text transcribes the speech.
    4. Answer and transcript are preserved without overwriting other answers.
    """
    if question_idx < 1 or question_idx > 5:
        raise HTTPException(status_code=400, detail="Invalid question index (1-5).")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assessment not found.")

    if row["status"] == "submitted":
        conn.close()
        raise HTTPException(status_code=400, detail="Assessment has already been submitted and cannot be modified.")

    # Read uploaded bytes
    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) < 100:
        conn.close()
        raise HTTPException(status_code=400, detail="Recorded audio is empty or too short. Please speak clearly and try again.")

    # Run ElevenLabs Isolation and STT
    lang = row["assessment_language"]
    prog_lang = row["programming_language"]
    questions = json.loads(row["questions_json"])
    current_q = questions[question_idx - 1] if 0 <= question_idx - 1 < len(questions) else {}
    q_context = f"{prog_lang} {current_q.get('title', '')} {current_q.get('concept', '')} {current_q.get('question', '')}"

    result = await elevenlabs_service.process_candidate_recording(
        audio_bytes=audio_bytes,
        assessment_id=assessment_id,
        question_index=question_idx,
        language=lang,
        programming_language=prog_lang,
        question_context=q_context,
        live_transcript=live_transcript
    )

    final_transcript = result["transcript"]
    if (not final_transcript or final_transcript.startswith("(Candidate speech")) and live_transcript and live_transcript.strip():
        final_transcript = live_transcript.strip()

    # Biometric Voice Verification against candidate's Terms & Conditions baseline voice
    clean_audio_path = RECORDINGS_DIR / result["audio_filename"]
    verify_res = verification_service.verify_speaker(
        assessment_id=assessment_id,
        answer_audio_path=clean_audio_path
    )
    logger.info(
        f"Verification for {assessment_id} Q{question_idx}: "
        f"matched={verify_res.get('matched')} score={verify_res.get('similarity_score')}%"
    )

    # Update answers json
    answers = json.loads(row["answers_json"])
    now = datetime.utcnow().isoformat()
    answers[str(question_idx)] = {
        "question_id": question_idx,
        "recorded": True,
        "transcript": final_transcript,
        "audio_filename": result["audio_filename"],
        "audio_url": result["audio_url"],
        "isolation_message": result["isolation_message"],
        "isolation_success": result["isolation_success"],
        "stt_provider": result["stt_provider"],
        "voice_matched": verify_res.get("matched", True),
        "voice_similarity_score": verify_res.get("similarity_score", 100.0),
        "voice_match_status": verify_res.get("status", "matched"),
        "voice_match_message": verify_res.get("message", "Voice Verified"),
        "recorded_at": now
    }

    cursor.execute(
        "UPDATE assessments SET answers_json = ? WHERE id = ?",
        (json.dumps(answers), assessment_id)
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "question_idx": question_idx,
        "answer": answers[str(question_idx)]
    }

@router.post("/{assessment_id}/submit")
def submit_assessment(assessment_id: str):
    """
    Submits completed assessment:
    1. Validates all 5 questions answered.
    2. Prevents duplicate submissions.
    3. Saves timestamp and status.
    4. Returns success message: 'Your answers have been submitted successfully!'
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assessment not found.")

    if row["status"] == "submitted":
        conn.close()
        return {
            "success": True,
            "message": "Your answers have been submitted successfully!",
            "already_submitted": True,
            "submitted_at": row["submitted_at"]
        }

    answers = json.loads(row["answers_json"])
    
    # Check that all 5 questions have recorded answers
    unanswered = []
    for i in range(1, 6):
        ans = answers.get(str(i))
        if not ans or not ans.get("recorded"):
            unanswered.append(i)

    if unanswered:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Please record answers for all questions before submitting. Unanswered questions: {unanswered}"
        )

    now = datetime.utcnow().isoformat()
    cursor.execute(
        "UPDATE assessments SET status = 'submitted', submitted_at = ? WHERE id = ?",
        (now, assessment_id)
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Your answers have been submitted successfully!",
        "submitted_at": now
    }

@router.get("/{assessment_id}/review")
def review_assessment(assessment_id: str):
    """
    Provides read-only review data for all 5 questions, candidate recordings, and transcripts.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    questions = json.loads(row["questions_json"])
    answers = json.loads(row["answers_json"])

    review_items = []
    for idx, q in enumerate(questions, start=1):
        ans = answers.get(str(idx), {})
        review_items.append({
            "question_number": idx,
            "title": q.get("title", f"Question {idx}"),
            "question": q.get("question", ""),
            "difficulty": q.get("difficulty", "Medium"),
            "concept": q.get("concept", ""),
            "recorded": ans.get("recorded", False),
            "transcript": ans.get("transcript", ""),
            "audio_url": ans.get("audio_url", ""),
            "isolation_message": ans.get("isolation_message", ""),
            "voice_matched": ans.get("voice_matched", True),
            "voice_similarity_score": ans.get("voice_similarity_score", 100.0),
            "voice_match_status": ans.get("voice_match_status", "matched"),
            "voice_match_message": ans.get("voice_match_message", "Voice Verified"),
            "recorded_at": ans.get("recorded_at")
        })

    row_keys = row.keys()
    baseline_fn = row["baseline_audio_filename"] if "baseline_audio_filename" in row_keys else None
    baseline_tr = row["baseline_transcript"] if "baseline_transcript" in row_keys else ""

    return {
        "assessment_id": row["id"],
        "user_email": row["user_email"],
        "programming_language": row["programming_language"],
        "assessment_language": row["assessment_language"],
        "status": row["status"],
        "baseline_audio_filename": baseline_fn,
        "baseline_audio_url": f"/api/audio/recording/{baseline_fn}" if baseline_fn else None,
        "baseline_transcript": baseline_tr,
        "created_at": row["created_at"],
        "submitted_at": row["submitted_at"],
        "review_items": review_items
    }
