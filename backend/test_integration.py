import io
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

def run_suite():
    client = TestClient(app)

    print("=== 1. Health & System Check ===")
    res = client.get('/api/system/status')
    status = res.json()
    print("System status code:", res.status_code)
    print("OpenVoice Ready:", status['openvoice']['engine_ready'])
    print("Reference voice present:", status['openvoice']['reference_voice_present'])

    print("\n=== 2. Candidate Login ===")
    res = client.post('/api/auth/login', json={'email': 'candidate@vani.ai', 'password': 'password123'})
    assert res.status_code == 200, res.text
    token = res.json()['token']
    print("Login success! User:", res.json()['user'])

    print("\n=== 3. Start Assessment (Python / English) ===")
    res = client.post('/api/assessment/start', json={
        'programming_language': 'Python',
        'assessment_language': 'English'
    })
    assert res.status_code == 200, res.text
    data = res.json()
    aid = data['assessment_id']
    questions = data['questions']
    print(f"Started assessment: {aid}")
    print(f"Generated {len(questions)} questions. Q1: {questions[0]['title']}")

    print("\n=== 4. Test Question Audio Endpoint (Voice Cloned) ===")
    res = client.get(f'/api/assessment/{aid}/question/1/audio')
    assert res.status_code == 200, res.text
    q1_audio = res.json()
    print("Q1 audio url:", q1_audio['audio_url'], "is_cloned:", q1_audio['is_cloned'])

    print("\n=== 5. Record Candidate Answers for All 5 Questions ===")
    # Dummy audio sample for candidate speech
    sample_audio_bytes = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00' + (b'\x00' * 2000)

    for q_num in range(1, 6):
        files = {'audio': (f'q{q_num}.wav', io.BytesIO(sample_audio_bytes), 'audio/wav')}
        res = client.post(f'/api/assessment/{aid}/question/{q_num}/answer', files=files)
        assert res.status_code == 200, f"Q{q_num} failed: {res.text}"
        ans = res.json()['answer']
        print(f"Q{q_num} recorded! Status: {ans['recorded']}, Audio URL: {ans['audio_url']}")

    print("\n=== 6. Submit Assessment ===")
    res = client.post(f'/api/assessment/{aid}/submit')
    assert res.status_code == 200, res.text
    submit_res = res.json()
    print("Submit result:", submit_res['message'])
    assert 'submitted successfully' in submit_res['message']

    print("\n=== 7. Review Assessment ===")
    res = client.get(f'/api/assessment/{aid}/review')
    assert res.status_code == 200, res.text
    review = res.json()
    print("Review items count:", len(review['review_items']), "Status:", review['status'])

    print("\n=== 8. Test Tamil Assessment (Java / Tamil) ===")
    res = client.post('/api/assessment/start', json={
        'programming_language': 'Java',
        'assessment_language': 'Tamil'
    })
    assert res.status_code == 200, res.text
    tamil_data = res.json()
    print(f"Tamil assessment started! Q count: {len(tamil_data['questions'])}")
    print("Q1 Title (encoded):", tamil_data['questions'][0]['title'].encode('ascii', 'backslashreplace').decode())

    print("\n========================================")
    print("  ALL INTEGRATION TESTS PASSED 100%!  ")
    print("========================================")

if __name__ == "__main__":
    run_suite()
