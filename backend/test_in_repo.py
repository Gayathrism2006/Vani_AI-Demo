import sys, asyncio
sys.path.insert(0, ".")
from app.services.question_service import question_service

async def main():
    print("Main started inside backend directory!", flush=True)
    question_service._quota_exhausted_until = 9999999999.0
    q = await question_service.generate_questions("Rust", "English")
    print("Rust Q1 title:", q[0]["title"], flush=True)

if __name__ == "__main__":
    asyncio.run(main())
